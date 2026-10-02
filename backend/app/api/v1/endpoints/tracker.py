import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.tracker_service import tracker_service
from app.schemas.tracker import (
    OverallProgressResponse,
    ScoreHistoryResponse,
    WeaknessesResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/progress", tags=["Progress & Weakness Tracker"])


@router.get(
    "/overall",
    response_model=OverallProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get overall progress statistics",
    description="Calculates average overall score, criteria component averages, category breakdown, and total interviews completed."
)
def get_overall_progress(db: Session = Depends(get_db)):
    try:
        return tracker_service.get_overall_progress(db=db)
    except Exception as exc:
        logger.error(f"Error retrieving overall progress: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate progress statistics: {str(exc)}"
        )


@router.get(
    "/history",
    response_model=ScoreHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get score history timeline",
    description="Retrieves chronological timeline of past interview analysis scores."
)
def get_score_history(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    try:
        return tracker_service.get_score_history(db=db, limit=limit)
    except Exception as exc:
        logger.error(f"Error retrieving score history: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch score history: {str(exc)}"
        )


@router.get(
    "/weaknesses",
    response_model=WeaknessesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get recurring improvement categories",
    description="Analyzes stored evaluation data to derive recurring weakness patterns, frequencies, and actionable tips."
)
def get_recurring_weaknesses(db: Session = Depends(get_db)):
    try:
        return tracker_service.get_recurring_weaknesses(db=db)
    except Exception as exc:
        logger.error(f"Error calculating recurring weaknesses: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate recurring improvement categories: {str(exc)}"
        )


@router.get(
    "/eval-report",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get AI reliability evaluation report",
    description="Runs engineering evaluation dataset through the AI pipeline and returns measured reliability metrics and disclaimers."
)
def get_ai_evaluation_report():
    try:
        from app.eval.evaluator import AIReliabilityEvaluator
        report = AIReliabilityEvaluator.run_evaluation()
        return report.model_dump()
    except Exception as exc:
        logger.error(f"Error executing AI reliability evaluation: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate evaluation report: {str(exc)}"
        )

