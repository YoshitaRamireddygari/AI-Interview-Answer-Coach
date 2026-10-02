import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.logging_utils import safe_log_snippet
from app.eval.dataset import EVALUATION_DATASET
from app.eval.evaluator import AIReliabilityEvaluator

client = TestClient(app)


def test_safe_log_snippet_privacy():
    """
    Test that sensitive strings such as email addresses and long user inputs are sanitized/truncated in logs.
    """
    pii_text = "Candidate email is candidate.john@example.com and they wrote a super long 200 character answer."
    sanitized = safe_log_snippet(pii_text, max_length=60)

    assert "[EMAIL_MASKED]" in sanitized
    assert "candidate.john@example.com" not in sanitized
    assert "..." in sanitized


def test_eval_dataset_integrity():
    """
    Ensure the engineering evaluation dataset contains valid interview examples.
    """
    assert len(EVALUATION_DATASET) >= 5
    for item in EVALUATION_DATASET:
        assert item.id
        assert item.category in ["behavioral", "technical", "hr", "project"]
        assert len(item.question) >= 5
        assert len(item.answer) >= 10


def test_evaluator_metrics_calculation():
    """
    Test running AIReliabilityEvaluator and calculating reliability metrics.
    """
    report = AIReliabilityEvaluator.run_evaluation()

    assert report.status == "success"
    assert report.metrics.total_eval_items >= 5
    assert report.metrics.valid_json_response_rate == 100.0
    assert report.metrics.schema_validation_success_rate == 100.0
    assert report.metrics.score_range_validity_rate == 100.0
    assert report.metrics.consistency_rate == 100.0

    # Non-scientific disclaimer check
    assert "engineering dataset" in report.disclaimer.lower()
    assert "not a statistically representative" in report.disclaimer.lower()



def test_get_eval_report_endpoint():
    """
    Test GET /api/progress/eval-report endpoint.
    """
    response = client.get("/api/progress/eval-report")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "disclaimer" in data
    assert "item_results" in data
