import os
import json
import pytest
from unittest.mock import MagicMock, patch

from app.schemas.gemini import GeminiEvaluationResult, CriterionEvaluation
from app.services.gemini_service import (
    GeminiService, 
    gemini_service, 
    GeminiServiceError, 
    GeminiAPIKeyError, 
    GeminiParseError,
    GeminiAPIError
)
from app.schemas.analysis import AnalyzeRequest
from app.services.analysis_service import AnalysisService


def test_api_key_reading_from_env(monkeypatch):
    """
    Requirement 1 & 2: Verify Gemini API key is read from environment variable
    and raises GeminiAPIKeyError when key is missing or placeholder.
    """
    # Test placeholder key
    monkeypatch.setenv("GEMINI_API_KEY", "your_gemini_api_key_here")
    with pytest.raises(GeminiAPIKeyError) as exc_info:
        GeminiService.get_api_key(raise_if_invalid=True)
    assert "GEMINI_API_KEY environment variable is not configured" in str(exc_info.value)

    # Test empty key
    monkeypatch.setenv("GEMINI_API_KEY", "")
    with pytest.raises(GeminiAPIKeyError):
        GeminiService.get_api_key(raise_if_invalid=True)

    # Test valid key in env
    monkeypatch.setenv("GEMINI_API_KEY", "test_actual_gemini_key_12345")
    key = GeminiService.get_api_key(raise_if_invalid=True)
    assert key == "test_actual_gemini_key_12345"


def test_prompt_construction():
    """
    Requirement 4 & 5: Verify prompt contains interview question, answer, category,
    and system instructions enforce grounding and safety rules.
    """
    service = GeminiService(api_key="mock_key")
    prompt = service.build_prompt(
        question="Tell me about a time you led a project.",
        answer="I led a database migration project with 3 engineers...",
        category="behavioral"
    )

    assert "Tell me about a time you led a project." in prompt
    assert "I led a database migration project with 3 engineers..." in prompt
    assert "Category: behavioral" in prompt

    # Verify system instruction rules
    system_inst = GeminiService.SYSTEM_INSTRUCTION
    assert "GROUNDING & ANTI-FABRICATION" in system_inst
    assert "SAFETY, BIAS & OBJECTIVITY" in system_inst
    assert "integers from 0 to 10" in system_inst
    assert "personality, intelligence, mental health" in system_inst


def test_parse_response_valid_json():
    """
    Requirement 5: Verify response parser handles clean JSON correctly.
    """
    service = GeminiService(api_key="mock_key")
    sample_json = json.dumps({
        "relevance": {"score": 9, "reason": "Directly addresses the project leadership prompt."},
        "completeness": {"score": 8, "reason": "Covers task, action, and team details well."},
        "clarity": {"score": 9, "reason": "Clear narrative flow without unnecessary filler words."},
        "structure": {"score": 8, "reason": "Follows STAR method effectively."},
        "technical_accuracy": {"score": 9, "reason": "Database migration terms used accurately."},
        "strengths": ["Clear timeline", "Specific action steps"],
        "improvements": ["Include measurable outcome metrics"],
        "improved_answer": "When leading a database migration with a 3-engineer team, I...",
        "technical_warnings": []
    })

    result = service.parse_response(sample_json)
    assert isinstance(result, GeminiEvaluationResult)
    assert result.relevance.score == 9
    assert result.completeness.score == 8
    assert result.improved_answer.startswith("When leading")
    assert len(result.strengths) == 2


def test_parse_response_markdown_fence_wrapped():
    """
    Requirement 5: Verify response parser strips markdown json code blocks.
    """
    service = GeminiService(api_key="mock_key")
    wrapped_raw = """```json
{
  "relevance": {"score": 10, "reason": "Perfect match."},
  "completeness": {"score": 7, "reason": "Good details."},
  "clarity": {"score": 8, "reason": "Very clear."},
  "structure": {"score": 8, "reason": "STAR structured."},
  "technical_accuracy": {"score": 9, "reason": "Accurate concepts."},
  "strengths": ["Strong motivation"],
  "improvements": ["Add quantitative result"],
  "improved_answer": "Refined answer text...",
  "technical_warnings": []
}
```"""
    result = service.parse_response(wrapped_raw)
    assert result.relevance.score == 10
    assert result.improvements == ["Add quantitative result"]


def test_parse_response_score_boundary_error():
    """
    Verify parser rejects scores outside [0, 10] integer range.
    """
    service = GeminiService(api_key="mock_key")
    invalid_score_json = json.dumps({
        "relevance": {"score": 15, "reason": "Out of range score"},
        "completeness": {"score": 8, "reason": "Valid"},
        "clarity": {"score": 8, "reason": "Valid"},
        "structure": {"score": 8, "reason": "Valid"},
        "technical_accuracy": {"score": 8, "reason": "Valid"},
        "strengths": [],
        "improvements": [],
        "improved_answer": "Test answer",
        "technical_warnings": []
    })

    with pytest.raises(GeminiParseError) as exc_info:
        service.parse_response(invalid_score_json)
    assert "relevance" in str(exc_info.value) or "less than or equal to 10" in str(exc_info.value)


def test_evaluate_answer_mocked_gemini_client(monkeypatch):
    """
    Requirement 3, 4, 5: Test complete evaluate_answer pipeline with a mocked genai.Client response.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "valid_test_api_key_abc123")
    
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "relevance": {"score": 8, "reason": "Good topic relevance."},
        "completeness": {"score": 7, "reason": "Covers context but missing outcome."},
        "clarity": {"score": 8, "reason": "Easy to follow."},
        "structure": {"score": 9, "reason": "Well structured STAR response."},
        "technical_accuracy": {"score": 8, "reason": "Accurate concepts."},
        "strengths": ["Structured narrative"],
        "improvements": ["Quantify impact"],
        "improved_answer": "In my previous role as software engineer...",
        "technical_warnings": []
    })

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        service = GeminiService()
        res = service.evaluate_answer(
            question="Describe a challenge you solved.",
            answer="I solved a memory leak issue by profiling heap usage...",
            category="technical"
        )

        assert res.relevance.score == 8
        assert res.structure.score == 9
        assert res.strengths == ["Structured narrative"]
        assert mock_client.models.generate_content.called


def test_analysis_service_integration_with_gemini(monkeypatch):
    """
    Test AnalysisService using GeminiService when key is configured.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "valid_test_api_key_abc123")

    mock_eval = GeminiEvaluationResult(
        relevance=CriterionEvaluation(score=9, reason="Highly relevant."),
        completeness=CriterionEvaluation(score=8, reason="Complete description."),
        clarity=CriterionEvaluation(score=9, reason="Very clear."),
        structure=CriterionEvaluation(score=8, reason="Good STAR method."),
        technical_accuracy=CriterionEvaluation(score=9, reason="Accurate tech details."),
        strengths=["Clear logic", "Good tech depth"],
        improvements=["Mention team size"],
        improved_answer="Enhanced answer text...",
        technical_warnings=[]
    )

    with patch.object(GeminiService, "evaluate_answer", return_value=mock_eval):
        req = AnalyzeRequest(
            question="How do you optimize slow database queries?",
            answer="I analyze EXPLAIN plans and add appropriate indexes on foreign keys.",
            category="technical"
        )
        response = AnalysisService.analyze_answer(req)

        assert response.status == "ai_evaluated"
        assert response.calculated_score == 86.5  # (9*0.25 + 8*0.20 + 9*0.20 + 8*0.15 + 9*0.20)*10 = 86.5
        assert response.score_10 == 8.65
        assert response.criteria_scores["relevance"].score == 90
        assert response.criteria_scores["relevance"].feedback == "Highly relevant."
        assert response.strengths == ["Clear logic", "Good tech depth"]
        assert response.improved_answer == "Enhanced answer text..."
