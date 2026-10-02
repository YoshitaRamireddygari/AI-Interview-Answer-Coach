from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class CriterionEvaluation(BaseModel):
    """
    Evaluation details for an individual interview criterion.
    Score MUST be an integer from 0 to 10.
    """
    score: int = Field(
        ..., 
        ge=0, 
        le=10, 
        description="Integer criterion score between 0 and 10"
    )
    reason: str = Field(
        ..., 
        description="Detailed explanation and reasoning for the assigned score"
    )

    model_config = ConfigDict(from_attributes=True)


class STARComponent(BaseModel):
    """
    Evaluation for an individual STAR framework element (Situation, Task, Action, or Result).
    """
    present: bool = Field(..., description="Whether this STAR element is present in the answer")
    feedback: str = Field(..., description="Feedback explaining presence or missing details for this element")

    model_config = ConfigDict(from_attributes=True)


class STARAnalysis(BaseModel):
    """
    Structured STAR (Situation, Task, Action, Result) framework breakdown for behavioral questions.
    """
    situation: STARComponent = Field(..., description="Situation element breakdown")
    task: STARComponent = Field(..., description="Task element breakdown")
    action: STARComponent = Field(..., description="Action element breakdown")
    result: STARComponent = Field(..., description="Result element breakdown")
    summary_feedback: Optional[str] = Field(
        default=None, 
        description="Overall summary explaining missing or present STAR elements"
    )

    model_config = ConfigDict(from_attributes=True)


class GeminiEvaluationResult(BaseModel):
    """
    Structured JSON evaluation response from Gemini AI.
    Contains evaluation criteria (0-10), strengths, improvements,
    technical warnings, missing information, STAR analysis, and grounded improved answer.
    """
    relevance: CriterionEvaluation = Field(
        ..., 
        description="Evaluation of relevance to the question (score 0-10 and reason)"
    )
    completeness: CriterionEvaluation = Field(
        ..., 
        description="Evaluation of answer completeness (score 0-10 and reason)"
    )
    clarity: CriterionEvaluation = Field(
        ..., 
        description="Evaluation of communication clarity and conciseness (score 0-10 and reason)"
    )
    structure: CriterionEvaluation = Field(
        ..., 
        description="Evaluation of answer structure e.g. STAR framework (score 0-10 and reason)"
    )
    technical_accuracy: CriterionEvaluation = Field(
        ..., 
        description="Evaluation of technical accuracy and terminology (score 0-10 and reason)"
    )
    strengths: List[str] = Field(
        default_factory=list, 
        description="List of key strengths demonstrated in the user's answer"
    )
    improvements: List[str] = Field(
        default_factory=list, 
        description="List of specific, actionable suggestions for improvement"
    )
    technical_warnings: List[str] = Field(
        default_factory=list, 
        description="List of any technical inaccuracies, risks, or warnings identified"
    )
    missing_information: List[str] = Field(
        default_factory=list, 
        description="List of unstated details, missing metrics, or key gaps in the answer"
    )
    star_analysis: Optional[STARAnalysis] = Field(
        default=None,
        description="STAR framework breakdown for behavioral questions (Situation, Task, Action, Result)"
    )
    improved_answer: str = Field(
        ..., 
        description="Enhanced version of the answer grounded strictly in the user's stated experience"
    )

    model_config = ConfigDict(from_attributes=True)
