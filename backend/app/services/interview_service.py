import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.db.models import InterviewSession, QuestionAnswer, AnalysisResult
from app.services.analysis_service import AnalysisService, analysis_service
from app.services.gemini_service import gemini_service
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse, SaveAnalysisRequest
from app.schemas.interview import (
    StartInterviewResponse,
    SubmitInterviewAnswerResponse,
    InterviewSummaryResponse
)

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class InterviewService:
    """
    Manages interactive multi-turn interview sessions.
    Maintains session history, orchestrates evaluation, generates follow-up questions,
    and compiles final interview summary reports.
    """

    MAX_QUESTIONS_PER_SESSION = 5

    def start_session(self, db: Session, category: str = "behavioral") -> StartInterviewResponse:
        """
        Creates a new interview session record in SQLite DB and generates Question 1.
        """
        category_clean = category.strip().lower() if category else "behavioral"
        session_title = f"{category_clean.capitalize()} Interview Session"

        db_session = InterviewSession(
            title=session_title,
            category=category_clean
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        # Generate Initial Question
        initial_question = gemini_service.generate_initial_question(category=category_clean)

        return StartInterviewResponse(
            session_id=db_session.id,
            category=category_clean,
            question_number=1,
            total_questions=self.MAX_QUESTIONS_PER_SESSION,
            current_question=initial_question
        )

    def submit_answer(
        self,
        db: Session,
        session_id: int,
        question: str,
        answer: str
    ) -> SubmitInterviewAnswerResponse:
        """
        Processes a candidate's answer within an interview session:
        1. Runs the 5-criteria deterministic analysis pipeline (+ STAR framework if behavioral).
        2. Saves question/answer and analysis result to database linked to session.
        3. Fetches past session history.
        4. If question_number < MAX_QUESTIONS, generates next context-aware question.
        5. If question_number >= MAX_QUESTIONS, finishes session and generates summary report.
        """
        db_session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview session with ID {session_id} not found."
            )

        category = db_session.category or "behavioral"

        # 1. Run Analysis Pipeline
        req = AnalyzeRequest(question=question, answer=answer, category=category)
        analysis_response = AnalysisService.analyze_answer(req)

        # 2. Persist in database linked to session_id
        saved_detail = AnalysisService.save_analysis(
            db=db,
            request=SaveAnalysisRequest(
                question=question,
                answer=answer,
                category=category,
                calculated_score=analysis_response.calculated_score,
                criteria_scores=analysis_response.criteria_scores,
                fillers_detected=analysis_response.fillers_detected,
                strengths=analysis_response.strengths,
                improvements=analysis_response.improvements,
                technical_warnings=analysis_response.technical_warnings,
                missing_information=analysis_response.missing_information,
                star_analysis=analysis_response.star_analysis,
                improved_answer=analysis_response.improved_answer
            ),
            session_id=session_id
        )

        analysis_response.id = saved_detail.id
        analysis_response.session_id = session_id
        analysis_response.created_at = saved_detail.created_at

        # 3. Query session QA history
        qa_records = (
            db.query(QuestionAnswer)
            .filter(QuestionAnswer.session_id == session_id)
            .order_by(QuestionAnswer.created_at.asc())
            .all()
        )

        history: List[Dict[str, str]] = [
            {"question": record.question, "answer": record.user_answer}
            for record in qa_records
        ]

        question_number = len(history)
        is_completed = question_number >= self.MAX_QUESTIONS_PER_SESSION

        next_question: Optional[str] = None
        summary: Optional[InterviewSummaryResponse] = None

        if not is_completed:
            # Generate next question with context awareness
            next_question = gemini_service.generate_next_question(
                category=category,
                history=history,
                current_question_num=question_number + 1
            )
        else:
            # Session finished, generate summary report
            summary = self.get_session_summary(db=db, session_id=session_id)

        return SubmitInterviewAnswerResponse(
            session_id=session_id,
            question_number=question_number,
            total_questions=self.MAX_QUESTIONS_PER_SESSION,
            is_completed=is_completed,
            analysis=analysis_response,
            next_question=next_question,
            summary=summary
        )

    def finish_session(self, db: Session, session_id: int) -> InterviewSummaryResponse:
        """
        Concludes an active interview session early and builds the summary report.
        """
        return self.get_session_summary(db=db, session_id=session_id)

    def get_session_summary(self, db: Session, session_id: int) -> InterviewSummaryResponse:
        """
        Builds a comprehensive final report summarizing all answered questions,
        average overall score, aggregated strengths, and key areas to improve.
        """
        db_session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview session with ID {session_id} not found."
            )
        category = db_session.category or "behavioral"

        # Fetch all analysis results linked to this session
        analysis_records = (
            db.query(AnalysisResult)
            .options(joinedload(AnalysisResult.question_answer))
            .filter(AnalysisResult.session_id == session_id)
            .order_by(AnalysisResult.created_at.asc())
            .all()
        )

        items: List[AnalyzeResponse] = []
        total_score = 0.0
        all_strengths: List[str] = []
        all_improvements: List[str] = []

        for record in analysis_records:
            qa = record.question_answer
            q_text = qa.question if qa else "Question"
            a_text = qa.user_answer if qa else "Answer"

            detail = AnalysisService._to_detail_response(record)
            
            analyze_resp = AnalyzeResponse(
                id=record.id,
                session_id=record.session_id,
                status="stored",
                message="Retrieved session record",
                question=q_text,
                user_answer=a_text,
                category=category,
                calculated_score=record.calculated_score,
                score_10=round(record.calculated_score / 10.0, 1),
                criteria_scores=detail.criteria_scores,
                fillers_detected=record.fillers_detected or [],
                strengths=record.strengths or [],
                improvements=record.improvements or [],
                technical_warnings=detail.technical_warnings or [],
                missing_information=detail.missing_information or [],
                star_analysis=detail.star_analysis,
                improved_answer=record.improved_answer or a_text,
                created_at=record.created_at
            )
            items.append(analyze_resp)
            total_score += record.calculated_score

            if record.strengths:
                all_strengths.extend(record.strengths)
            if record.improvements:
                all_improvements.extend(record.improvements)

        count = len(items)
        avg_score = round(total_score / count, 1) if count > 0 else 0.0
        avg_score_10 = round(avg_score / 10.0, 1)

        unique_strengths = list(dict.fromkeys(all_strengths))
        unique_improvements = list(dict.fromkeys(all_improvements))

        return InterviewSummaryResponse(
            session_id=session_id,
            category=category,
            average_score=avg_score,
            average_score_10=avg_score_10,
            total_questions_answered=count,
            items=items,
            overall_strengths=unique_strengths[:6],
            overall_improvements=unique_improvements[:6]
        )


interview_service = InterviewService()
