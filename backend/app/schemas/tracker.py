from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class ComponentAverages(BaseModel):
    """
    Average scores across evaluation criteria.
    """
    relevance: float = Field(..., ge=0, le=10, description="Average relevance score (0-10)")
    completeness: float = Field(..., ge=0, le=10, description="Average completeness score (0-10)")
    clarity: float = Field(..., ge=0, le=10, description="Average clarity score (0-10)")
    structure: float = Field(..., ge=0, le=10, description="Average structure score (0-10)")
    technical_accuracy: float = Field(..., ge=0, le=10, description="Average technical accuracy score (0-10)")

    model_config = ConfigDict(from_attributes=True)


class OverallProgressResponse(BaseModel):
    """
    Response schema for overall interview progress statistics.
    """
    total_interviews_completed: int = Field(..., description="Total count of interview sessions completed")
    total_answers_analyzed: int = Field(..., description="Total count of individual answers analyzed")
    average_overall_score: float = Field(..., ge=0, le=100, description="Average overall score (0-100)")
    average_overall_score_10: float = Field(..., ge=0, le=10, description="Average overall score (0-10)")
    component_averages: ComponentAverages = Field(..., description="Criteria score averages")
    category_averages: Dict[str, float] = Field(..., description="Average percentage score by category")

    model_config = ConfigDict(from_attributes=True)


class ScoreHistoryItem(BaseModel):
    """
    Schema for individual score entry in progress history timeline.
    """
    id: int = Field(..., description="Analysis record ID")
    session_id: int = Field(..., description="Interview session ID")
    created_at: datetime = Field(..., description="Timestamp of analysis")
    question: str = Field(..., description="Question answered")
    category: str = Field(..., description="Interview category")
    score: float = Field(..., ge=0, le=100, description="Calculated percentage score")
    score_10: float = Field(..., ge=0, le=10, description="Calculated score (0-10)")

    model_config = ConfigDict(from_attributes=True)


class ScoreHistoryResponse(BaseModel):
    """
    Response schema for score history timeline.
    """
    total: int = Field(..., description="Total count of history entries")
    items: List[ScoreHistoryItem] = Field(..., description="Chronological list of score history items")

    model_config = ConfigDict(from_attributes=True)


class RecurringWeaknessItem(BaseModel):
    """
    Schema for a recurring weakness / improvement category.
    """
    category_key: str = Field(..., description="Identifier key for the weakness category")
    title: str = Field(..., description="Human-readable category title")
    count: int = Field(..., description="Number of times identified across stored analyses")
    percentage: float = Field(..., description="Percentage of analyzed answers exhibiting this improvement area")
    description: str = Field(..., description="Short explanation of the weakness pattern")
    example_feedback: List[str] = Field(default=[], description="Sample feedback quotes from user analysis records")
    actionable_tip: str = Field(..., description="Actionable recommendation to improve")

    model_config = ConfigDict(from_attributes=True)


class WeaknessesResponse(BaseModel):
    """
    Response schema for recurring improvement categories.
    """
    total_analyzed: int = Field(..., description="Total answers analyzed to derive recurring weaknesses")
    recurring_weaknesses: List[RecurringWeaknessItem] = Field(..., description="Ranked list of recurring weakness categories")

    model_config = ConfigDict(from_attributes=True)
