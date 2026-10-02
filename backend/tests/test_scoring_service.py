import pytest
from app.services.scoring_service import (
    ScoringService, 
    scoring_service, 
    InvalidScoringConfigError, 
    InvalidComponentScoreError
)


def test_default_weights_calculation():
    """
    Requirement 5 & 6: Test score calculation using standard default weights.
    Relevance: 25%, Completeness: 20%, Clarity: 20%, Structure: 15%, Technical accuracy: 20%.
    """
    scores = {
        "relevance": 10.0,
        "completeness": 8.0,
        "clarity": 8.0,
        "structure": 6.0,
        "technical_accuracy": 10.0
    }
    # Expected: (10*0.25) + (8*0.20) + (8*0.20) + (6*0.15) + (10*0.20) = 2.5 + 1.6 + 1.6 + 0.9 + 2.0 = 8.6 out of 10 (86.0%)
    result = scoring_service.calculate_score(scores)

    assert result.score_10 == 8.6
    assert result.score_100 == 86.0
    assert result.component_scores == scores
    assert result.weights_config["relevance"] == 0.25
    assert result.weights_config["structure"] == 0.15
    assert result.weighted_components["relevance"] == 2.5
    assert result.weighted_components["completeness"] == 1.6
    assert result.weighted_components["clarity"] == 1.6
    assert result.weighted_components["structure"] == 0.9
    assert result.weighted_components["technical_accuracy"] == 2.0


def test_custom_weights_calculation():
    """
    Requirement 3 & 4: Test score calculation with custom valid weights that sum to 1.0.
    """
    custom_weights = {
        "relevance": 0.40,
        "completeness": 0.20,
        "clarity": 0.10,
        "structure": 0.10,
        "technical_accuracy": 0.20
    }
    scores = {
        "relevance": 9.0,
        "completeness": 7.0,
        "clarity": 8.0,
        "structure": 6.0,
        "technical_accuracy": 10.0
    }
    # Expected: (9*0.4) + (7*0.2) + (8*0.1) + (6*0.1) + (10*0.2) = 3.6 + 1.4 + 0.8 + 0.6 + 2.0 = 8.4 out of 10 (84.0%)
    result = scoring_service.calculate_score(scores, weights=custom_weights)

    assert result.score_10 == 8.4
    assert result.score_100 == 84.0
    assert result.weights_config == custom_weights


def test_component_score_out_of_bounds_low():
    """
    Requirement 2: Validate that scores below 0 raise InvalidComponentScoreError.
    """
    invalid_scores = {
        "relevance": -1.0,  # Invalid negative score
        "completeness": 8.0,
        "clarity": 8.0,
        "structure": 8.0,
        "technical_accuracy": 8.0
    }
    with pytest.raises(InvalidComponentScoreError) as exc_info:
        scoring_service.calculate_score(invalid_scores)
    assert "must be between 0 and 10" in str(exc_info.value)


def test_component_score_out_of_bounds_high():
    """
    Requirement 2: Validate that scores above 10 raise InvalidComponentScoreError.
    """
    invalid_scores = {
        "relevance": 12.0,  # Invalid score > 10
        "completeness": 8.0,
        "clarity": 8.0,
        "structure": 8.0,
        "technical_accuracy": 8.0
    }
    with pytest.raises(InvalidComponentScoreError) as exc_info:
        scoring_service.calculate_score(invalid_scores)
    assert "must be between 0 and 10" in str(exc_info.value)


def test_missing_component_score():
    """
    Requirement 2: Test error raised when a required component score is omitted.
    """
    incomplete_scores = {
        "relevance": 8.0,
        "completeness": 8.0,
        "clarity": 8.0,
        "structure": 8.0
        # Missing technical_accuracy
    }
    with pytest.raises(InvalidComponentScoreError) as exc_info:
        scoring_service.calculate_score(incomplete_scores)
    assert "Missing required component scores" in str(exc_info.value)


def test_weights_sum_not_equal_to_one():
    """
    Requirement 4: Validate that weights not adding up to 1.0 raise InvalidScoringConfigError.
    """
    invalid_weights = {
        "relevance": 0.30,
        "completeness": 0.30,
        "clarity": 0.30,
        "structure": 0.30,
        "technical_accuracy": 0.30  # Sum = 1.5, invalid
    }
    scores = {
        "relevance": 8.0,
        "completeness": 8.0,
        "clarity": 8.0,
        "structure": 8.0,
        "technical_accuracy": 8.0
    }
    with pytest.raises(InvalidScoringConfigError) as exc_info:
        scoring_service.calculate_score(scores, weights=invalid_weights)
    assert "Component weights must add up to 1.0" in str(exc_info.value)


def test_negative_weight_config():
    """
    Requirement 3: Validate that negative weights raise InvalidScoringConfigError.
    """
    invalid_weights = {
        "relevance": -0.25,  # Invalid negative weight
        "completeness": 0.45,
        "clarity": 0.20,
        "structure": 0.40,
        "technical_accuracy": 0.20
    }
    scores = {
        "relevance": 8.0,
        "completeness": 8.0,
        "clarity": 8.0,
        "structure": 8.0,
        "technical_accuracy": 8.0
    }
    with pytest.raises(InvalidScoringConfigError) as exc_info:
        scoring_service.calculate_score(scores, weights=invalid_weights)
    assert "must be between 0.0 and 1.0" in str(exc_info.value)


def test_all_zero_scores():
    """
    Test edge case: all 0 component scores return 0.0 score_10 and 0.0 score_100.
    """
    zero_scores = {
        "relevance": 0.0,
        "completeness": 0.0,
        "clarity": 0.0,
        "structure": 0.0,
        "technical_accuracy": 0.0
    }
    result = scoring_service.calculate_score(zero_scores)
    assert result.score_10 == 0.0
    assert result.score_100 == 0.0


def test_all_perfect_ten_scores():
    """
    Test edge case: all 10 component scores return 10.0 score_10 and 100.0 score_100.
    """
    perfect_scores = {
        "relevance": 10.0,
        "completeness": 10.0,
        "clarity": 10.0,
        "structure": 10.0,
        "technical_accuracy": 10.0
    }
    result = scoring_service.calculate_score(perfect_scores)
    assert result.score_10 == 10.0
    assert result.score_100 == 100.0
