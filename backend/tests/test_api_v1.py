from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_get():
    """
    Test GET /api/v1/health endpoint.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_health_check_post():
    """
    Test POST /api/v1/health endpoint.
    """
    response = client.post("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_analyze_placeholder_valid_request():
    """
    Test POST /api/v1/analyze endpoint with valid payload.
    """
    payload = {
        "question": "Tell me about yourself",
        "answer": "My name is Alex and I am a software engineer with 3 years of experience in backend development.",
        "category": "general"
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["placeholder", "stored"]
    assert data["question"] == payload["question"]
    assert data["user_answer"] == payload["answer"]
    assert "calculated_score" in data
    assert "criteria_scores" in data
    assert "fillers_detected" in data
    assert "improved_answer" in data


def test_analyze_validation_error_short_answer():
    """
    Test POST /api/v1/analyze endpoint with invalid payload (answer too short).
    """
    payload = {
        "question": "Tell me about yourself",
        "answer": "Too short"  # Min length is 10
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "Validation Error"
    assert "details" in data
