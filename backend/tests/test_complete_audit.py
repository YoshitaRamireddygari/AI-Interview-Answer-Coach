import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.services.tracker_service import tracker_service
from app.services.interview_service import interview_service
from app.services.technical_verifier import technical_verifier

# In-memory database setup for isolation
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
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_empty_database_handling():
    """Verify system handles empty database state without errors or zero-division exceptions."""
    db = TestingSessionLocal()
    
    # Tracker APIs on empty DB
    progress = tracker_service.get_overall_progress(db)
    assert progress.total_interviews_completed == 0
    assert progress.total_answers_analyzed == 0
    assert progress.average_overall_score == 0.0

    history = tracker_service.get_score_history(db)
    assert history.total == 0
    assert history.items == []

    weaknesses = tracker_service.get_recurring_weaknesses(db)
    assert weaknesses.total_analyzed == 0
    assert weaknesses.recurring_weaknesses == []

    # API endpoints on empty DB
    res_list = client.get("/api/analyses")
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 0

    res_404 = client.get("/api/analyses/999")
    assert res_404.status_code == 404
    db.close()


def test_database_crud_and_relationships():
    """Verify complete CRUD lifecycle: create, read list, read single, session relationship linkage."""
    payload = {
        "question": "Walk me through how you optimized a slow SQL query in production.",
        "answer": "I identified a slow query using EXPLAIN ANALYZE, discovered a missing index on user_id, and added a composite index which reduced query execution time from 1.2s to 45ms.",
        "category": "technical",
        "calculated_score": 92.0,
        "criteria_scores": {
            "relevance": {"score": 95, "feedback": "Directly answered technical question."},
            "technical_accuracy": {"score": 95, "feedback": "Accurate SQL optimization terms."}
        }
    }
    
    # 1. Create
    create_res = client.post("/api/analyses", json=payload)
    assert create_res.status_code == 201
    record_id = create_res.json()["id"]

    # 2. Read Single
    get_res = client.get(f"/api/analyses/{record_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == record_id
    assert data["question"] == payload["question"]

    # 3. Read List
    list_res = client.get("/api/analyses")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1


def test_technical_verification_claim_extraction():
    """Verify claim extraction, uncertainty labeling, and technical warnings."""
    answer = "HTTP is a programming language used to build operating systems."
    report = technical_verifier.verify_answer(
        question="What is HTTP?",
        answer=answer,
        category="technical"
    )
    assert len(report.claims) > 0
    assert report.limitations_disclaimer is not None
    assert "protocol" in report.warnings[0].lower() or "programming language" in report.warnings[0].lower()


def test_interview_mode_multi_turn_flow():
    """Verify starting, submitting answers, adaptive next question generation, and final summary."""
    db = TestingSessionLocal()
    
    # 1. Start Interview
    start_res = interview_service.start_session(db, category="behavioral")
    session_id = start_res.session_id
    assert start_res.question_number == 1
    assert start_res.current_question != ""

    # 2. Submit Turn 1
    turn1_res = interview_service.submit_answer(
        db=db,
        session_id=session_id,
        question=start_res.current_question,
        answer="I faced a tight deadline on a web application release. I prioritized core tasks and deployed on time."
    )
    assert turn1_res.question_number == 1
    assert turn1_res.next_question is not None
    assert turn1_res.is_completed is False

    # 3. Finish session early
    summary = interview_service.finish_session(db, session_id=session_id)
    assert summary.session_id == session_id
    assert summary.total_questions_answered == 1
    assert summary.average_score > 0
    db.close()
