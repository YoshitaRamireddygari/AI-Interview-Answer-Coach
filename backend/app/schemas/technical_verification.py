from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ClaimVerificationStatus(str, Enum):
    """
    Uncertainty status labels for technical claim verification.
    """
    LIKELY_CORRECT = "Likely correct"
    POTENTIAL_ISSUE = "Potential issue"
    NEEDS_VERIFICATION = "Needs verification"


class TechnicalClaim(BaseModel):
    """
    Schema for an extracted technical assertion and its verification result.
    """
    claim_text: str = Field(..., description="The specific technical statement extracted from the user's answer")
    status: ClaimVerificationStatus = Field(..., description="Uncertainty label: Likely correct, Potential issue, Needs verification")
    explanation: str = Field(..., description="Technical explanation or context for the claim status")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score of the verification result (0.0 to 1.0)")
    source_reference: Optional[str] = Field(default=None, description="Optional reference category or rule name (no fake URLs)")

    model_config = ConfigDict(from_attributes=True)


class TechnicalVerificationReport(BaseModel):
    """
    Complete technical verification report for an interview submission.
    """
    category: str = Field(default="technical", description="Interview category")
    total_claims_extracted: int = Field(..., description="Total count of technical claims extracted")
    claims: List[TechnicalClaim] = Field(default=[], description="Extracted claims with uncertainty labels and explanations")
    warnings: List[str] = Field(default=[], description="List of technical warning messages derived from potential issues")
    limitations_disclaimer: str = Field(
        default=(
            "LLM-based technical verification evaluates statements against known domain patterns, but may miss subtle "
            "edge cases or version differences. Always verify critical architecture claims with official technical documentation."
        ),
        description="Disclaimer detailing LLM technical fact-checking limitations."
    )

    model_config = ConfigDict(from_attributes=True)
