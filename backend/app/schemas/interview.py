from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.schemas.analysis import AnalyzeResponse

class StartInterviewRequest(BaseModel):
    """
    Schema for starting an interview session.
    """
    category: str = Field(
        default="behavioral",
        description="Interview category: behavioral, technical, hr, project",
        json_schema_extra={"example": "technical"}
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        valid_categories = ["behavioral", "technical", "hr", "project", "general"]
        cleaned = v.strip().lower() if v else "behavioral"
        if cleaned not in valid_categories:
            return "behavioral"
        return cleaned

    model_config = ConfigDict(from_attributes=True)


class StartInterviewResponse(BaseModel):
    """
    Response when an interview session is initiated.
    """
    session_id: int = Field(..., description="Unique database ID for the interview session")
    category: str = Field(..., description="Selected interview category")
    question_number: int = Field(default=1, description="Current question number in session")
    total_questions: int = Field(default=5, description="Maximum questions in session")
    current_question: str = Field(..., description="The initial interview question generated")

    model_config = ConfigDict(from_attributes=True)


class SubmitInterviewAnswerRequest(BaseModel):
    """
    Schema for submitting an answer to a question within an active interview session.
    """
    session_id: int = Field(..., description="Active interview session ID")
    question: str = Field(..., min_length=5, max_length=1000, description="The question being answered")
    answer: str = Field(..., min_length=10, max_length=5000, description="The user's answer")

    @field_validator("question")
    @classmethod
    def validate_question_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question cannot be empty.")
        return v.strip()

    @field_validator("answer")
    @classmethod
    def validate_answer_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Answer cannot be empty.")
        return v.strip()

    model_config = ConfigDict(from_attributes=True)


class InterviewSummaryResponse(BaseModel):
    """
    Final report summary for a completed interview session.
    """
    session_id: int = Field(..., description="Session ID")
    category: str = Field(..., description="Interview category")
    average_score: float = Field(..., ge=0, le=100, description="Average percentage score across answered questions")
    average_score_10: float = Field(..., ge=0, le=10, description="Average score on 0-10 scale")
    total_questions_answered: int = Field(..., description="Total questions answered")
    items: List[AnalyzeResponse] = Field(..., description="List of evaluated Q&As in this session")
    overall_strengths: List[str] = Field(default=[], description="Aggregated strengths across session")
    overall_improvements: List[str] = Field(default=[], description="Aggregated areas for improvement across session")

    model_config = ConfigDict(from_attributes=True)


class SubmitInterviewAnswerResponse(BaseModel):
    """
    Response after submitting an answer in an interview session.
    """
    session_id: int = Field(..., description="Interview session ID")
    question_number: int = Field(..., description="Question number just evaluated")
    total_questions: int = Field(default=5, description="Total planned questions")
    is_completed: bool = Field(..., description="True if interview session is finished")
    analysis: AnalyzeResponse = Field(..., description="Evaluation of the submitted answer")
    next_question: Optional[str] = Field(default=None, description="The next context-aware question to answer")
    summary: Optional[InterviewSummaryResponse] = Field(default=None, description="Session summary report if finished")

    model_config = ConfigDict(from_attributes=True)


class FinishInterviewRequest(BaseModel):
    """
    Schema for manually concluding an active interview session early.
    """
    session_id: int = Field(..., description="Active interview session ID")

    model_config = ConfigDict(from_attributes=True)
