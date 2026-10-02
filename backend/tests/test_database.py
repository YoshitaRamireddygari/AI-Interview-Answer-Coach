import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db

# Setup in-memory SQLite database for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """
    Creates fresh database schema and overrides DB dependency before each test.
    Cleans up overrides and drops schema afterwards.
    """
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_auto_create_tables():
    """
    Requirement 3: Verify database tables are created automatically.
    """
    table_names = engine.dialect.get_table_names(engine.connect())
    assert "interview_sessions" in table_names
    assert "question_answers" in table_names
    assert "analysis_results" in table_names


def test_save_analysis_endpoint():
    """
    Requirement 5: Test API endpoint to save an analysis result (POST /api/v1/analyses).
    """
    payload = {
        "question": "Tell me about a time you handled a tight deadline.",
        "answer": "At my previous role as a software developer, we had a major project release scheduled for Friday. A critical bug was discovered on Thursday afternoon.",
        "category": "behavioral",
        "calculated_score": 85.0,
        "criteria_scores": {
            "relevance": {"score": 90, "feedback": "Directly answered deadline scenario."},
            "clarity": {"score": 80, "feedback": "Clear phrasing."}
        },
        "fillers_detected": ["basically"],
        "strengths": ["Clear situation description"],
        "improvements": ["Mention quantitative metrics"],
        "improved_answer": "At my previous role, I prioritized tasks to meet the Friday deadline..."
    }
    response = client.post("/api/v1/analyses", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["session_id"] is not None
    assert data["question_id"] is not None
    assert data["question"] == payload["question"]
    assert data["user_answer"] == payload["answer"]
    assert data["category"] == "behavioral"
    assert data["calculated_score"] == 85.0
    assert "relevance" in data["criteria_scores"]
    assert data["criteria_scores"]["relevance"]["score"] == 90


def test_save_analysis_implicit_placeholder():
    """
    Test POST /api/v1/analyses when optional score/criteria details are omitted.
    """
    payload = {
        "question": "What are your strengths as a backend engineer?",
        "answer": "I specialize in API design, database query optimization, and microservice architecture."
    }
    response = client.post("/api/v1/analyses", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["calculated_score"] == 75.0
    assert "relevance" in data["criteria_scores"]


def test_retrieve_previous_analysis_results():
    """
    Requirement 6: Test API endpoint to retrieve previous analysis results (GET /api/v1/analyses).
    """
    # 1. Create two test records
    payload1 = {
        "question": "Describe a complex bug you solved.",
        "answer": "I solved a memory leak in our backend server by profiling memory allocations using heap dumps."
    }
    payload2 = {
        "question": "How do you handle disagreement with team members?",
        "answer": "I schedule a 1-on-1 meeting to listen to their perspective and review objective data together."
    }
    client.post("/api/v1/analyses", json=payload1)
    client.post("/api/v1/analyses", json=payload2)

    # 2. Retrieve history list
    response = client.get("/api/v1/analyses")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    # Verify ordered by newest first
    assert data["items"][0]["question"] == payload2["question"]
    assert data["items"][1]["question"] == payload1["question"]


def test_retrieve_one_analysis_by_id():
    """
    Requirement 7: Test endpoint to retrieve one analysis by ID (GET /api/v1/analyses/{id}).
    """
    payload = {
        "question": "Why do you want to join our engineering team?",
        "answer": "I admire your engineering blog post on high scale distributed systems and want to contribute to that mission."
    }
    create_res = client.post("/api/v1/analyses", json=payload)
    analysis_id = create_res.json()["id"]

    response = client.get(f"/api/v1/analyses/{analysis_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == analysis_id
    assert data["question"] == payload["question"]


def test_retrieve_analysis_not_found():
    """
    Requirement 7 & 9: Test 404 response for non-existent analysis ID.
    """
    response = client.get("/api/v1/analyses/9999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_input_validation_errors():
    """
    Requirement 8: Test input validation on save payload (short question/answer).
    """
    payload = {
        "question": "Tiny",  # Min length 5 required (4 chars)
        "answer": "Too short"  # Min length 10 required (9 chars)
    }
    response = client.post("/api/v1/analyses", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "Validation Error"
    assert len(data["details"]) >= 2


def test_analyze_and_save_endpoint():
    """
    Test POST /api/v1/analyze auto-saves to database.
    """
    payload = {
        "question": "What experience do you have with relational databases?",
        "answer": "I have 4 years of experience writing SQL queries, indexing, and designing database models in PostgreSQL and SQLite."
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stored"
    assert data["id"] is not None
    assert data["session_id"] is not None

    fetch_res = client.get(f"/api/v1/analyses/{data['id']}")
    assert fetch_res.status_code == 200
    fetch_data = fetch_res.json()
    assert fetch_data["question"] == payload["question"]


def test_cascade_delete_session():
    """
    Verify deleting an InterviewSession deletes associated QuestionAnswer and AnalysisResult records.
    """
    from app.db.models import InterviewSession, QuestionAnswer, AnalysisResult

    db = TestingSessionLocal()
    payload = {
        "question": "Explain database indexing.",
        "answer": "B-Tree indexes speed up SELECT query filtering at the cost of slight write overhead."
    }
    response = client.post("/api/v1/analyze", json=payload)
    session_id = response.json()["session_id"]
    analysis_id = response.json()["id"]

    # Verify entities exist
    assert db.query(InterviewSession).filter(InterviewSession.id == session_id).count() == 1
    assert db.query(QuestionAnswer).filter(QuestionAnswer.session_id == session_id).count() == 1
    assert db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).count() == 1

    # Delete session
    sess = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    db.delete(sess)
    db.commit()

    # Assert zero orphaned records remain
    assert db.query(InterviewSession).filter(InterviewSession.id == session_id).count() == 0
    assert db.query(QuestionAnswer).filter(QuestionAnswer.session_id == session_id).count() == 0
    assert db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).count() == 0
    db.close()
