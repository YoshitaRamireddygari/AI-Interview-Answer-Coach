import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import get_db
from app.services.gemini_service import gemini_service

client = TestClient(app)


def test_start_interview_session():
    """Test starting a new interview session."""
    response = client.post("/api/interview/start", json={"category": "technical"})
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["category"] == "technical"
    assert data["question_number"] == 1
    assert data["total_questions"] == 5
    assert len(data["current_question"]) > 5


def test_submit_interview_answer_flow(monkeypatch):
    """Test submitting answers through a multi-question interview flow."""
    # 1. Start Session
    start_resp = client.post("/api/interview/start", json={"category": "behavioral"})
    assert start_resp.status_code == 201
    start_data = start_resp.json()
    session_id = start_data["session_id"]
    current_q = start_data["current_question"]

    # 2. Submit Question 1 Answer
    answer_1 = "In my previous role, our main payment system crashed during Black Friday sale. I immediately organized an emergency war room, rolled back the broken deployment, and restored operations within 15 minutes."
    sub_1 = client.post("/api/interview/submit", json={
        "session_id": session_id,
        "question": current_q,
        "answer": answer_1
    })
    assert sub_1.status_code == 200
    sub_1_data = sub_1.json()
    assert sub_1_data["session_id"] == session_id
    assert sub_1_data["question_number"] == 1
    assert sub_1_data["is_completed"] is False
    assert sub_1_data["next_question"] is not None
    assert "analysis" in sub_1_data
    assert sub_1_data["analysis"]["calculated_score"] > 0

    # STAR analysis present for behavioral
    assert sub_1_data["analysis"]["star_analysis"] is not None


def test_finish_interview_early():
    """Test manually finishing an interview session early."""
    start_resp = client.post("/api/interview/start", json={"category": "project"})
    session_id = start_resp.json()["session_id"]
    q1 = start_resp.json()["current_question"]

    client.post("/api/interview/submit", json={
        "session_id": session_id,
        "question": q1,
        "answer": "We built a scalable backend using FastAPI, React, and MongoDB."
    })

    finish_resp = client.post("/api/interview/finish", json={"session_id": session_id})
    assert finish_resp.status_code == 200
    summary = finish_resp.json()
    assert summary["session_id"] == session_id
    assert summary["total_questions_answered"] == 1
    assert summary["average_score"] > 0
    assert len(summary["items"]) == 1


def test_next_question_grounding_and_context():
    """Verify that question generation produces relevant follow up questions."""
    history = [
        {"question": "Walk me through your project.", "answer": "I built a real-time chat app using MongoDB and Socket.io."}
    ]
    next_q = gemini_service.generate_next_question(
        category="technical",
        history=history,
        current_question_num=2
    )
    assert isinstance(next_q, str)
    assert len(next_q) > 10


def test_submit_nonexistent_and_malformed_session_id():
    """Verify 404 response for nonexistent session_id and 422 for malformed session_id."""
    # 1. Nonexistent session ID (99999) -> 404 Not Found
    resp_404 = client.post("/api/interview/submit", json={
        "session_id": 99999,
        "question": "What is Python?",
        "answer": "Python is a dynamic programming language."
    })
    assert resp_404.status_code == 404
    assert "not found" in resp_404.json()["detail"].lower()

    finish_404 = client.post("/api/interview/finish", json={"session_id": 99999})
    assert finish_404.status_code == 404

    # 2. Malformed session ID ("not-an-int") -> 422 Validation Error
    resp_422 = client.post("/api/interview/submit", json={
        "session_id": "not-an-int",
        "question": "What is Python?",
        "answer": "Python is a dynamic programming language."
    })
    assert resp_422.status_code == 422
