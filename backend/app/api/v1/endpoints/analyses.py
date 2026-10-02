from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import (
    SaveAnalysisRequest,
    AnalysisDetailResponse,
    AnalysisListResponse
)
from app.services.analysis_service import AnalysisService

router = APIRouter()


@router.post(
    "/analyses",
    response_model=AnalysisDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save an Analysis Result"
)
def save_analysis(
    request: SaveAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Saves an interview analysis session result to the SQLite database.
    Validates payload input, stores session, question/answer, and analysis scores/feedback.
    """
    saved_analysis = AnalysisService.save_analysis(db, request)
    return saved_analysis


@router.get(
    "/analyses",
    response_model=AnalysisListResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Previous Analysis Results"
)
def get_all_analyses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Retrieves all previously saved interview analysis results with pagination support.
    """
    return AnalysisService.get_all_analyses(db, skip=skip, limit=limit)


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve One Analysis Result by ID"
)
def get_analysis_by_id(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieves details for a specific interview analysis session by its unique ID.
    Returns HTTP 404 if the record does not exist.
    """
    if analysis_id <= 0:
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail="Analysis ID must be a positive integer."
        )

    result = AnalysisService.get_analysis_by_id(db, analysis_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis result with ID {analysis_id} not found."
        )
    return result
