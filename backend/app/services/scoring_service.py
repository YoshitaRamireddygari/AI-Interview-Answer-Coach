import math
from typing import Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class InvalidScoringConfigError(ValueError):
    """Raised when scoring weights configuration is invalid."""
    pass


class InvalidComponentScoreError(ValueError):
    """Raised when an individual criterion score is outside the valid range [0, 10]."""
    pass


class ScoringBreakdown(BaseModel):
    """
    Detailed output breakdown of the deterministic scoring calculation.
    """
    score_10: float = Field(..., ge=0, le=10, description="Final weighted score on a 0-10 scale")
    score_100: float = Field(..., ge=0, le=100, description="Final weighted score on a 0-100 percentage scale")
    component_scores: Dict[str, float] = Field(..., description="Raw component scores on 0-10 scale")
    weighted_components: Dict[str, float] = Field(..., description="Weighted score contribution per component")
    weights_config: Dict[str, float] = Field(..., description="Weighting configuration applied (sum = 1.0)")

    model_config = ConfigDict(from_attributes=True)


class ScoringService:
    """
    Dedicated deterministic evaluation and scoring service.
    Ensures final scores are calculated in Python using strict configurable weights
    rather than relying directly on LLM raw overall score decisions.
    """

    # Configurable default criteria weights (must sum to 1.0)
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "relevance": 0.25,
        "completeness": 0.20,
        "clarity": 0.20,
        "structure": 0.15,
        "technical_accuracy": 0.20
    }

    REQUIRED_COMPONENTS = {"relevance", "completeness", "clarity", "structure", "technical_accuracy"}

    @classmethod
    def validate_weights(cls, weights: Dict[str, float]) -> None:
        """
        Validates that all required component weights are present,
        non-negative, and sum exactly to 1.0 (within float tolerance).
        """
        if not weights:
            raise InvalidScoringConfigError("Weights configuration cannot be empty.")

        missing = cls.REQUIRED_COMPONENTS - set(weights.keys())
        if missing:
            raise InvalidScoringConfigError(
                f"Missing required component weights: {', '.join(sorted(missing))}"
            )

        for comp, w in weights.items():
            if not isinstance(w, (int, float)):
                raise InvalidScoringConfigError(f"Weight for component '{comp}' must be a number.")
            if w < 0.0 or w > 1.0:
                raise InvalidScoringConfigError(
                    f"Weight for component '{comp}' must be between 0.0 and 1.0 (got {w})."
                )

        total_weight = sum(weights.values())
        if not math.isclose(total_weight, 1.0, rel_tol=1e-5, abs_tol=1e-5):
            raise InvalidScoringConfigError(
                f"Component weights must add up to 1.0 (got sum = {total_weight:.4f})."
            )

    @classmethod
    def validate_component_scores(cls, scores: Dict[str, float]) -> None:
        """
        Validates that every required component score is provided
        and lies within the 0 to 10 integer/float range inclusive.
        """
        if not scores:
            raise InvalidComponentScoreError("Component scores dictionary cannot be empty.")

        missing = cls.REQUIRED_COMPONENTS - set(scores.keys())
        if missing:
            raise InvalidComponentScoreError(
                f"Missing required component scores: {', '.join(sorted(missing))}"
            )

        for comp, s in scores.items():
            if not isinstance(s, (int, float)):
                raise InvalidComponentScoreError(f"Score for component '{comp}' must be a number.")
            if s < 0.0 or s > 10.0:
                raise InvalidComponentScoreError(
                    f"Component score for '{comp}' must be between 0 and 10 (got {s})."
                )

    @classmethod
    def calculate_score(
        cls, 
        component_scores: Dict[str, float], 
        weights: Optional[Dict[str, float]] = None
    ) -> ScoringBreakdown:
        """
        Deterministically calculates the final weighted score (0-10 scale and 0-100 percentage)
        from component scores using configured component weights.
        """
        active_weights = weights if weights is not None else cls.DEFAULT_WEIGHTS

        # Validate inputs
        cls.validate_weights(active_weights)
        cls.validate_component_scores(component_scores)

        # Calculate weighted contribution per component
        weighted_components = {}
        total_weighted_10 = 0.0

        for comp in cls.REQUIRED_COMPONENTS:
            raw_s = float(component_scores[comp])
            w = float(active_weights[comp])
            contrib = raw_s * w
            weighted_components[comp] = round(contrib, 3)
            total_weighted_10 += contrib

        score_10 = round(total_weighted_10, 2)
        score_100 = round(score_10 * 10.0, 1)

        return ScoringBreakdown(
            score_10=score_10,
            score_100=score_100,
            component_scores={k: float(v) for k, v in component_scores.items()},
            weighted_components=weighted_components,
            weights_config={k: float(v) for k, v in active_weights.items()}
        )


# Global singleton instance of ScoringService
scoring_service = ScoringService()
