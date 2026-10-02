from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.schemas.gemini import STARAnalysis, STARComponent
from app.schemas.technical_verification import TechnicalVerificationReport

DEFAULT_WEIGHTS_CONFIG = {
    "relevance": 0.25,
    "completeness": 0.20,
    "clarity": 0.20,
    "structure": 0.15,
    "technical_accuracy": 0.20
}



class CriterionScore(BaseModel):
    """
    Schema for individual scoring criterion feedback.
    """
    score: int = Field(..., ge=0, le=100, description="Criterion score between 0 and 100")
    feedback: str = Field(..., description="Specific feedback for this criterion")

    model_config = ConfigDict(from_attributes=True)


class AnalyzeRequest(BaseModel):
    """
    Schema for incoming answer analysis request payload.
    """
    question: str = Field(
        ..., 
        min_length=5, 
        max_length=1000, 
        description="The interview question being answered",
        json_schema_extra={"example": "Tell me about a time you handled a difficult deadline."}
    )
    answer: str = Field(
        ..., 
        min_length=10, 
        max_length=5000, 
        description="The user's interview answer to analyze",
        json_schema_extra={"example": "Um, so basically we had a project due on Friday and..."}
    )
    category: Optional[str] = Field(
        default="general", 
        description="Interview question category (behavioral, technical, general)",
        json_schema_extra={"example": "behavioral"}
    )

    @field_validator("question")
    @classmethod
    def validate_question_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question cannot be empty or whitespace only.")
        return v.strip()

    @field_validator("answer")
    @classmethod
    def validate_answer_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Answer cannot be empty or whitespace only.")
        return v.strip()

    model_config = ConfigDict(from_attributes=True)


class SaveAnalysisRequest(BaseModel):
    """
    Schema for explicitly saving an analysis result.
    If scores/feedback are omitted, placeholder evaluation is generated.
    """
    question: str = Field(..., min_length=5, max_length=1000, description="The interview question")
    answer: str = Field(..., min_length=10, max_length=5000, description="The user's answer")
    category: Optional[str] = Field(default="general", description="Interview category")
    calculated_score: Optional[float] = Field(default=None, ge=0, le=100, description="Calculated overall score")
    criteria_scores: Optional[Dict[str, CriterionScore]] = Field(default=None, description="Criteria breakdown")
    fillers_detected: Optional[List[str]] = Field(default=None, description="Detected filler words")
    strengths: Optional[List[str]] = Field(default=None, description="Key strengths")
    improvements: Optional[List[str]] = Field(default=None, description="Areas for improvement")
    technical_warnings: Optional[List[str]] = Field(default=None, description="Technical warnings")
    missing_information: Optional[List[str]] = Field(default=None, description="Missing details or gaps")
    star_analysis: Optional[STARAnalysis] = Field(default=None, description="STAR framework analysis for behavioral questions")
    improved_answer: Optional[str] = Field(default=None, description="Suggested improved answer")

    model_config = ConfigDict(from_attributes=True)


class AnalyzeResponse(BaseModel):
    """
    Schema for answer analysis response payload.
    Transparently displays calculated scores, criteria weights, component contributions,
    and specialized STAR framework analysis for behavioral interview questions.
    """
    id: Optional[int] = Field(default=None, description="Database record ID if saved")
    session_id: Optional[int] = Field(default=None, description="Interview session ID if saved")
    status: str = Field(..., description="Execution status mode (e.g. placeholder, stored)")
    message: str = Field(..., description="Human-readable response message")
    question: str = Field(..., description="Original question")
    user_answer: str = Field(..., description="Original user answer")
    category: str = Field(..., description="Interview category")
    calculated_score: float = Field(..., ge=0, le=100, description="Weighted final percentage score (0-100)")
    score_10: Optional[float] = Field(default=None, ge=0, le=10, description="Weighted final score on 0-10 scale")
    weights_config: Dict[str, float] = Field(
        default_factory=lambda: dict(DEFAULT_WEIGHTS_CONFIG),
        description="Criteria weights configuration applied (sum = 1.0)"
    )
    score_breakdown: Optional[Dict[str, float]] = Field(
        default=None, 
        description="Weighted contribution per component on 0-10 scale"
    )
    criteria_scores: Dict[str, CriterionScore] = Field(..., description="Detailed breakdown per criterion")
    fillers_detected: List[str] = Field(default=[], description="List of detected filler words or phrases")
    strengths: List[str] = Field(default=[], description="List of identified answer strengths")
    improvements: List[str] = Field(default=[], description="List of key actionable suggestions for improvement")
    technical_warnings: List[str] = Field(default=[], description="List of technical inaccuracies or warnings")
    missing_information: List[str] = Field(default=[], description="List of missing details or narrative gaps")
    star_analysis: Optional[STARAnalysis] = Field(default=None, description="STAR framework analysis for behavioral questions")
    technical_verification: Optional[TechnicalVerificationReport] = Field(default=None, description="Technical accuracy verification report with uncertainty labels")
    improved_answer: str = Field(..., description="Enhanced version of answer grounded in user's original context")
    created_at: Optional[datetime] = Field(default=None, description="Timestamp of creation")

    model_config = ConfigDict(from_attributes=True)


class AnalysisDetailResponse(BaseModel):
    """
    Schema for retrieving stored analysis result details by ID or in history lists.
    """
    id: int = Field(..., description="Analysis result primary key ID")
    session_id: int = Field(..., description="Associated interview session ID")
    question_id: int = Field(..., description="Associated question/answer ID")
    question: str = Field(..., description="The interview question")
    user_answer: str = Field(..., description="The user's original answer")
    category: str = Field(..., description="Interview category")
    calculated_score: float = Field(..., ge=0, le=100, description="Overall weighted percentage score")
    score_10: Optional[float] = Field(default=None, ge=0, le=10, description="Weighted final score on 0-10 scale")
    weights_config: Dict[str, float] = Field(
        default_factory=lambda: dict(DEFAULT_WEIGHTS_CONFIG),
        description="Criteria weights configuration applied"
    )
    criteria_scores: Dict[str, CriterionScore] = Field(..., description="Criterion breakdown")
    fillers_detected: List[str] = Field(default=[], description="Detected filler words")
    strengths: List[str] = Field(default=[], description="Key answer strengths")
    improvements: List[str] = Field(default=[], description="Areas for improvement")
    technical_warnings: List[str] = Field(default=[], description="Technical warnings")
    missing_information: List[str] = Field(default=[], description="Missing information")
    star_analysis: Optional[STARAnalysis] = Field(default=None, description="STAR framework analysis")
    technical_verification: Optional[TechnicalVerificationReport] = Field(default=None, description="Technical verification report")
    improved_answer: str = Field(..., description="Improved answer version")
    created_at: datetime = Field(..., description="Creation timestamp")


    model_config = ConfigDict(from_attributes=True)


class AnalysisListResponse(BaseModel):
    """
    Schema for paginated list of previous analysis results.
    """
    total: int = Field(..., description="Total count of retrieved analysis items")
    items: List[AnalysisDetailResponse] = Field(..., description="List of analysis records")

    model_config = ConfigDict(from_attributes=True)
