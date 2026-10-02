from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse, SaveAnalysisRequest
from app.services.analysis_service import AnalysisService

router = APIRouter()


@router.post(
    "/analyze", 
    response_model=AnalyzeResponse, 
    status_code=status.HTTP_200_OK,
    summary="Analyze and Save Interview Answer"
)
def analyze_answer(
    request: AnalyzeRequest,
    save: bool = True,
    db: Session = Depends(get_db)
):
    """
    Endpoint for submitting an interview answer for criteria analysis.
    Uses Gemini AI service for structured evaluation when configured,
    and automatically persists the interview session and analysis to SQLite DB when save=True.
    """
    analysis = AnalysisService.analyze_answer(request)
    
    if save:
        saved_record = AnalysisService.save_analysis(
            db, 
            SaveAnalysisRequest(
                question=request.question,
                answer=request.answer,
                category=request.category,
                calculated_score=analysis.calculated_score,
                criteria_scores=analysis.criteria_scores,
                fillers_detected=analysis.fillers_detected,
                strengths=analysis.strengths,
                improvements=analysis.improvements,
                improved_answer=analysis.improved_answer
            )
        )
        analysis.id = saved_record.id
        analysis.session_id = saved_record.session_id
        analysis.created_at = saved_record.created_at
        analysis.status = "stored"
        analysis.message = f"[Stage 4] Analysis evaluated and saved successfully with ID #{saved_record.id}."

    return analysis
