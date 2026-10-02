import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.main import app
from app.services.gemini_service import (
    GeminiService, 
    GeminiAPIError, 
    GeminiParseError, 
    GeminiAPIKeyError
)
from app.db.repository import AnalysisRepository

client = TestClient(app)


def test_post_api_analyze_success_flow(monkeypatch):
    """
    Requirement 1-10: Test complete POST /api/analyze pipeline success flow.
    """
    payload = {
        "question": "Tell me about a time you resolved a conflict within your software development team.",
        "answer": "In my previous project, two engineers disagreed on microservices vs monolith design. I facilitated a design review, documented tradeoffs, and built a prototype to align the team.",
        "category": "behavioral"
    }

    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["question"] == payload["question"]
    assert data["user_answer"] == payload["answer"]
    assert data["category"] == "behavioral"
    assert "calculated_score" in data
    assert "score_10" in data
    assert "weights_config" in data
    assert "score_breakdown" in data
    assert "criteria_scores" in data
    assert "improved_answer" in data
    assert data["id"] is not None


def test_category_autodetect_pipeline():
    """
    Test interview category auto-detection in pipeline when category is omitted or 'auto'.
    """
    payload = {
        "question": "How do you optimize slow database SQL queries and indexes?",
        "answer": "I analyze EXPLAIN ANALYZE execution plans, add composite indexes, and refactored ORM eager loading.",
        "category": "auto"
    }

    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "technical"


def test_invalid_input_validation_short_fields():
    """
    Error Handling: Test HTTP 422 validation error for short question and answer.
    """
    payload = {
        "question": "Tiny",  # Min length 5 required (4 chars)
        "answer": "Tiny"     # Min length 10 required (4 chars)
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "Validation Error"
    assert len(data["details"]) >= 2


def test_invalid_input_whitespace_only():
    """
    Error Handling: Test HTTP 422 validation error when question or answer contains only whitespace.
    """
    payload = {
        "question": "   \n\t   ",
        "answer": "Valid answer text with sufficient length for testing."
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "Validation Error"


def test_gemini_api_failure_handling(monkeypatch):
    """
    Error Handling: Test HTTP 502 response when Gemini API call fails.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_gemini_123")
    
    with patch.object(GeminiService, "evaluate_answer", side_effect=GeminiAPIError("Remote Gemini connection reset")):
        payload = {
            "question": "Tell me about a time you led a migration project.",
            "answer": "I led a database migration project with 3 engineers over 4 months."
        }
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 502
        data = response.json()
        assert data["error"] == "AI Service Error"
        assert "Failed to communicate with AI evaluation service" in data["message"]


def test_malformed_ai_response_handling(monkeypatch):
    """
    Error Handling: Test HTTP 502 response when AI service returns malformed output.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_gemini_123")
    
    with patch.object(GeminiService, "evaluate_answer", side_effect=GeminiParseError("Invalid JSON structure returned")):
        payload = {
            "question": "Tell me about a time you led a migration project.",
            "answer": "I led a database migration project with 3 engineers over 4 months."
        }
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 502
        data = response.json()
        assert data["error"] == "Malformed AI Response"
        assert "Received malformed evaluation output" in data["message"]


def test_gemini_timeout_handling(monkeypatch):
    """
    Error Handling: Test HTTP 504 response when Gemini API request times out.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_gemini_123")
    
    with patch.object(GeminiService, "evaluate_answer", side_effect=TimeoutError("Request timed out")):
        payload = {
            "question": "Tell me about a time you led a migration project.",
            "answer": "I led a database migration project with 3 engineers over 4 months."
        }
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 504
        data = response.json()
        assert data["error"] == "Gateway Timeout"
        assert "timed out" in data["message"]


def test_database_failure_handling():
    """
    Error Handling: Test HTTP 500 response when database persistence fails.
    """
    with patch.object(AnalysisRepository, "create_analysis_record", side_effect=SQLAlchemyError("SQLite DB connection locked")):
        payload = {
            "question": "Tell me about a time you led a migration project.",
            "answer": "I led a database migration project with 3 engineers over 4 months."
        }
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Database Error"
        assert "database operation failed" in data["message"].lower()


def test_security_no_api_key_or_stack_trace_leak(monkeypatch):
    """
    Security Requirement: Verify error details never leak sensitive API keys or raw internal tracebacks.
    """
    fake_key = "AIzaSySecretApiKeyDoNotExpose12345"
    monkeypatch.setenv("GEMINI_API_KEY", fake_key)
    
    with patch.object(GeminiService, "evaluate_answer", side_effect=GeminiAPIError(f"Error with key={fake_key}")):
        payload = {
            "question": "Tell me about a time you led a migration project.",
            "answer": "I led a database migration project with 3 engineers over 4 months."
        }
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 502
        raw_text = response.text
        assert fake_key not in raw_text
        assert "[REDACTED" in raw_text or "AI Service Error" in raw_text
