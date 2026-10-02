import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.gemini import STARComponent, STARAnalysis, GeminiEvaluationResult, CriterionEvaluation
from app.services.gemini_service import GeminiService
from app.schemas.analysis import AnalyzeRequest
from app.services.analysis_service import AnalysisService

client = TestClient(app)


def test_star_analysis_pydantic_schema():
    """
    Requirement 1: Test Pydantic schema instantiation for STAR framework elements.
    """
    star = STARAnalysis(
        situation=STARComponent(present=True, feedback="Context established."),
        task=STARComponent(present=True, feedback="Responsibilities stated."),
        action=STARComponent(present=False, feedback="Action steps missing."),
        result=STARComponent(present=False, feedback="Outcome metrics missing."),
        summary_feedback="The answer explains what happened and what you were asked to do, but it does not clearly describe the action you personally took or the result."
    )

    assert star.situation.present is True
    assert star.action.present is False
    assert "Action steps missing" in star.action.feedback
    assert "result" in star.summary_feedback.lower()


def test_gemini_service_star_analysis_json_parsing():
    """
    Requirement 2: Verify GeminiService parses structured JSON containing star_analysis.
    """
    service = GeminiService(api_key="mock_key")
    raw_json = json.dumps({
        "relevance": {"score": 9, "reason": "Relevant scenario."},
        "completeness": {"score": 8, "reason": "Covers details."},
        "clarity": {"score": 9, "reason": "Clear narrative."},
        "structure": {"score": 8, "reason": "Follows STAR."},
        "technical_accuracy": {"score": 9, "reason": "Accurate concepts."},
        "strengths": ["Clear context"],
        "improvements": ["Add quantitative metrics"],
        "technical_warnings": [],
        "missing_information": ["Metrics"],
        "star_analysis": {
            "situation": {"present": True, "feedback": "Background scenario described."},
            "task": {"present": True, "feedback": "Goal clearly defined."},
            "action": {"present": True, "feedback": "Personal actions described."},
            "result": {"present": False, "feedback": "Final metrics omitted."},
            "summary_feedback": "Situation ✓, Task ✓, Action ✓, Result ✗ -- Missing quantitative outcome."
        },
        "improved_answer": "When leading the project..."
    })

    res = service.parse_response(raw_json)
    assert res.star_analysis is not None
    assert res.star_analysis.situation.present is True
    assert res.star_analysis.result.present is False
    assert "Missing quantitative outcome" in res.star_analysis.summary_feedback


def test_behavioral_pipeline_returns_star_analysis():
    """
    Requirement 3: Test POST /api/analyze endpoint returns star_analysis for behavioral questions.
    """
    payload = {
        "question": "Tell me about a time you handled a difficult conflict in your team.",
        "answer": "In my previous project, two engineers disagreed on API design. I set up a design review session to compare REST and GraphQL.",
        "category": "behavioral"
    }

    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["category"] == "behavioral"
    assert "star_analysis" in data
    assert data["star_analysis"] is not None
    assert "situation" in data["star_analysis"]
    assert "task" in data["star_analysis"]
    assert "action" in data["star_analysis"]
    assert "result" in data["star_analysis"]
    assert "summary_feedback" in data["star_analysis"]


def test_star_analysis_underlying_content_detection(monkeypatch):
    """
    Requirement 2 & 5: Ensure STAR analysis detects underlying content without requiring
    literal words 'Situation', 'Task', 'Action', or 'Result'.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_star_123")

    mock_eval = GeminiEvaluationResult(
        relevance=CriterionEvaluation(score=9, reason="Relevant"),
        completeness=CriterionEvaluation(score=8, reason="Complete"),
        clarity=CriterionEvaluation(score=9, reason="Clear"),
        structure=CriterionEvaluation(score=8, reason="Structured"),
        technical_accuracy=CriterionEvaluation(score=9, reason="Accurate"),
        strengths=["Clear narrative"],
        improvements=["Quantify impact"],
        technical_warnings=[],
        missing_information=[],
        star_analysis=STARAnalysis(
            situation=STARComponent(present=True, feedback="Setting was established."),
            task=STARComponent(present=True, feedback="Objective was clear."),
            action=STARComponent(present=True, feedback="Steps were executed."),
            result=STARComponent(present=False, feedback="Outcome metrics omitted."),
            summary_feedback="Situation ✓, Task ✓, Action ✓, Result ✗ -- Clear narrative but missing outcome."
        ),
        improved_answer="Refined answer text..."
    )

    with patch.object(GeminiService, "evaluate_answer", return_value=mock_eval):
        req = AnalyzeRequest(
            question="Describe a challenge you faced at work.",
            answer="Our database endpoint was failing under high load. I investigated query locks and added redis caching.",
            category="behavioral"
        )
        response = AnalysisService.analyze_answer(req)
        assert response.star_analysis.situation.present is True
        assert response.star_analysis.result.present is False
