from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.db.models import InterviewSession, QuestionAnswer, AnalysisResult


class AnalysisRepository:
    """
    Repository class providing CRUD database operations for interview analysis sessions.
    """

    @staticmethod
    def create_analysis_record(
        db: Session,
        question: str,
        user_answer: str,
        category: str,
        calculated_score: float,
        criteria_scores: Dict[str, Any],
        fillers_detected: List[str],
        strengths: List[str],
        improvements: List[str],
        improved_answer: str,
        session_id: Optional[int] = None,
    ) -> AnalysisResult:
        """
        Saves a full interview analysis session (session, question/answer, analysis result)
        within a single database transaction.
        """
        try:
            target_session_id = session_id
            if not target_session_id:
                # 1. Create interview session entity
                session_title = f"{category.capitalize()} Interview Analysis"
                db_session = InterviewSession(
                    title=session_title,
                    category=category
                )
                db.add(db_session)
                db.flush()  # Obtain db_session.id
                target_session_id = db_session.id

            # 2. Create question/answer entity
            db_question = QuestionAnswer(
                session_id=target_session_id,
                question=question,
                user_answer=user_answer,
                category=category
            )
            db.add(db_question)
            db.flush()  # Obtain db_question.id

            # 3. Create analysis result entity
            db_analysis = AnalysisResult(
                session_id=target_session_id,
                question_id=db_question.id,
                calculated_score=calculated_score,
                criteria_scores=criteria_scores,
                fillers_detected=fillers_detected,
                strengths=strengths,
                improvements=improvements,
                improved_answer=improved_answer
            )
            db.add(db_analysis)
            db.commit()
            db.refresh(db_analysis)
            return db_analysis


        except SQLAlchemyError as exc:
            db.rollback()
            raise exc

    @staticmethod
    def get_all_analyses(
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[AnalysisResult]:
        """
        Retrieves a list of all analysis results with joined question and session data,
        ordered by creation time descending.
        """
        return (
            db.query(AnalysisResult)
            .options(
                joinedload(AnalysisResult.question_answer),
                joinedload(AnalysisResult.session)
            )
            .order_by(AnalysisResult.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_analysis_by_id(
        db: Session, 
        analysis_id: int
    ) -> Optional[AnalysisResult]:
        """
        Retrieves a single analysis result by its unique ID.
        """
        return (
            db.query(AnalysisResult)
            .options(
                joinedload(AnalysisResult.question_answer),
                joinedload(AnalysisResult.session)
            )
            .filter(AnalysisResult.id == analysis_id)
            .first()
        )
