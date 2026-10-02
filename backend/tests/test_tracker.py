import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_overall_progress_endpoint():
    """Test GET /api/progress/overall endpoint."""
    response = client.get("/api/progress/overall")
    assert response.status_code == 200
    data = response.json()
    assert "total_interviews_completed" in data
    assert "total_answers_analyzed" in data
    assert "average_overall_score" in data
    assert "average_overall_score_10" in data
    assert "component_averages" in data

    comp = data["component_averages"]
    assert "relevance" in comp
    assert "completeness" in comp
    assert "clarity" in comp
    assert "structure" in comp
    assert "technical_accuracy" in comp

    assert "category_averages" in data


def test_get_score_history_endpoint():
    """Test GET /api/progress/history endpoint."""
    response = client.get("/api/progress/history")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_get_recurring_weaknesses_endpoint():
    """Test GET /api/progress/weaknesses endpoint."""
    response = client.get("/api/progress/weaknesses")
    assert response.status_code == 200
    data = response.json()
    assert "total_analyzed" in data
    assert "recurring_weaknesses" in data
    assert isinstance(data["recurring_weaknesses"], list)

    if data["recurring_weaknesses"]:
        w = data["recurring_weaknesses"][0]
        assert "category_key" in w
        assert "title" in w
        assert "count" in w
        assert "percentage" in w
        assert "description" in w
        assert "actionable_tip" in w
