import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.interview_service import interview_service
from app.schemas.interview import (
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitInterviewAnswerRequest,
    SubmitInterviewAnswerResponse,
    FinishInterviewRequest,
    InterviewSummaryResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview", tags=["Interview Mode"])


@router.post(
    "/start",
    response_model=StartInterviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start interactive interview session",
    description="Initializes a multi-turn 5-question interview session for the specified category."
)
def start_interview(
    payload: StartInterviewRequest,
    db: Session = Depends(get_db)
):
    try:
        return interview_service.start_session(db=db, category=payload.category)
    except Exception as exc:
        logger.error(f"Error starting interview session: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview session: {str(exc)}"
        )


@router.post(
    "/submit",
    response_model=SubmitInterviewAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit interview answer",
    description="Evaluates answer using deterministic scoring, saves progress, and returns next context-aware question."
)
def submit_interview_answer(
    payload: SubmitInterviewAnswerRequest,
    db: Session = Depends(get_db)
):
    try:
        return interview_service.submit_answer(
            db=db,
            session_id=payload.session_id,
            question=payload.question,
            answer=payload.answer
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error evaluating interview answer for session {payload.session_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(exc)}"
        )


@router.post(
    "/finish",
    response_model=InterviewSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Finish interview session early",
    description="Concludes active interview session and compiles final performance summary report."
)
def finish_interview(
    payload: FinishInterviewRequest,
    db: Session = Depends(get_db)
):
    try:
        return interview_service.finish_session(db=db, session_id=payload.session_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error concluding interview session {payload.session_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finish interview session: {str(exc)}"
        )


@router.get(
    "/{session_id}/summary",
    response_model=InterviewSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get interview session summary",
    description="Retrieves performance report and question history for a given interview session."
)
def get_interview_summary(
    session_id: int,
    db: Session = Depends(get_db)
):
    try:
        return interview_service.get_session_summary(db=db, session_id=session_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching summary for session {session_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session summary: {str(exc)}"
        )
