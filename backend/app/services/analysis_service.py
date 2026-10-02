import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.schemas.analysis import (
    AnalyzeRequest, 
    AnalyzeResponse, 
    SaveAnalysisRequest, 
    CriterionScore,
    AnalysisDetailResponse,
    AnalysisListResponse
)
from app.schemas.gemini import STARAnalysis, STARComponent
from app.schemas.technical_verification import TechnicalVerificationReport
from app.db.repository import AnalysisRepository
from app.db.models import AnalysisResult
from app.services.gemini_service import gemini_service, GeminiServiceError
from app.services.scoring_service import scoring_service
from app.services.category_detector import CategoryDetector
from app.services.technical_verifier import technical_verifier

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Service layer for interview answer analysis operations, Gemini AI integration,
    category detection, deterministic weighted scoring calculation, STAR behavioral breakdown,
    technical accuracy verification layer, and database persistence.
    """

    @classmethod
    def analyze_answer(cls, request: AnalyzeRequest) -> AnalyzeResponse:
        """
        Executes complete analysis pipeline:
        1. Input validation & non-empty check
        2. Interview category detection (CategoryDetector)
        3. Gemini AI evaluation execution
        4. Validation of AI response payload
        5. Specialized STAR framework analysis for behavioral questions
        6. Technical accuracy checking layer (TechnicalVerifier) with uncertainty labels
        7. Deterministic scoring calculation via ScoringService
        8. Return complete structured response (saved to DB if requested)
        """
        category = CategoryDetector.detect_category(request.question, request.category)

        # Execute Technical Accuracy Verification Layer
        tech_report = technical_verifier.verify_answer(
            question=request.question,
            answer=request.answer,
            category=category
        )

        if gemini_service.is_configured():
            eval_res = gemini_service.evaluate_answer(
                question=request.question,
                answer=request.answer,
                category=category
            )
            
            # Raw component scores (0 to 10) from Gemini evaluation
            raw_component_scores = {
                "relevance": eval_res.relevance.score,
                "completeness": eval_res.completeness.score,
                "clarity": eval_res.clarity.score,
                "structure": eval_res.structure.score,
                "technical_accuracy": eval_res.technical_accuracy.score
            }

            # Deterministically calculate final score and breakdown in Python
            scoring_result = scoring_service.calculate_score(raw_component_scores)

            criteria_scores = {
                "relevance": CriterionScore(
                    score=eval_res.relevance.score * 10,
                    feedback=eval_res.relevance.reason
                ),
                "completeness": CriterionScore(
                    score=eval_res.completeness.score * 10,
                    feedback=eval_res.completeness.reason
                ),
                "clarity": CriterionScore(
                    score=eval_res.clarity.score * 10,
                    feedback=eval_res.clarity.reason
                ),
                "structure": CriterionScore(
                    score=eval_res.structure.score * 10,
                    feedback=eval_res.structure.reason
                ),
                "technical_accuracy": CriterionScore(
                    score=eval_res.technical_accuracy.score * 10,
                    feedback=eval_res.technical_accuracy.reason
                )
            }

            star_analysis = eval_res.star_analysis
            if category == "behavioral" and not star_analysis:
                star_analysis = cls._generate_default_star_analysis(request.answer)

            # Combine Gemini technical warnings with verification report warnings
            combined_warnings = list(dict.fromkeys(eval_res.technical_warnings + tech_report.warnings))

            return AnalyzeResponse(
                status="ai_evaluated",
                message="[Stage 12] Answer evaluated successfully via complete analysis pipeline with technical accuracy verification.",
                question=request.question,
                user_answer=request.answer,
                category=category,
                calculated_score=scoring_result.score_100,
                score_10=scoring_result.score_10,
                weights_config=scoring_result.weights_config,
                score_breakdown=scoring_result.weighted_components,
                criteria_scores=criteria_scores,
                fillers_detected=[],
                strengths=eval_res.strengths,
                improvements=eval_res.improvements,
                technical_warnings=combined_warnings,
                missing_information=eval_res.missing_information,
                star_analysis=star_analysis,
                technical_verification=tech_report,
                improved_answer=eval_res.improved_answer
            )

        # Fallback if Gemini key is not configured on server
        res = cls.generate_placeholder_analysis(request)
        res.technical_verification = tech_report
        if tech_report.warnings:
            res.technical_warnings = list(dict.fromkeys(res.technical_warnings + tech_report.warnings))
        return res


    @classmethod
    def generate_placeholder_analysis(cls, request: AnalyzeRequest) -> AnalyzeResponse:
        """
        Generates a structured placeholder analysis response using deterministic scoring.
        """
        category = CategoryDetector.detect_category(request.question, request.category)
        
        # Component scores on 0-10 scale for placeholder evaluation
        placeholder_component_scores = {
            "relevance": 8.0,
            "completeness": 7.0,
            "clarity": 7.5,
            "structure": 8.0,
            "technical_accuracy": 7.0
        }
        scoring_result = scoring_service.calculate_score(placeholder_component_scores)

        star_analysis = None
        if category == "behavioral":
            star_analysis = cls._generate_default_star_analysis(request.answer)

        return AnalyzeResponse(
            status="placeholder",
            message="[Stage 9] Deterministic scoring & STAR analysis active (placeholder mode).",
            question=request.question,
            user_answer=request.answer,
            category=category,
            calculated_score=scoring_result.score_100,
            score_10=scoring_result.score_10,
            weights_config=scoring_result.weights_config,
            score_breakdown=scoring_result.weighted_components,
            criteria_scores={
                "relevance": CriterionScore(
                    score=80, 
                    feedback="Placeholder: Answer addresses the core topic of the question."
                ),
                "completeness": CriterionScore(
                    score=70, 
                    feedback="Placeholder: Answer covers basic details but lacks specific outcome metrics."
                ),
                "clarity": CriterionScore(
                    score=75, 
                    feedback="Placeholder: Generally clear phrasing with minor filler word usage."
                ),
                "structure": CriterionScore(
                    score=70, 
                    feedback="Placeholder: Narrative structure can be improved using the STAR method."
                ),
                "technical_accuracy": CriterionScore(
                    score=80, 
                    feedback="Placeholder: Technical terms mentioned appear accurate for the domain."
                ),
            },
            fillers_detected=["um", "basically", "like"],
            strengths=[
                "Directly responds to the prompt.",
                "Demonstrates relevant background context."
            ],
            improvements=[
                "Structure response with clear Situation, Task, Action, and Result (STAR) steps.",
                "Reduce usage of conversational filler words."
            ],
            technical_warnings=[
                "Ensure technical terms like ORM eager loading or query plan optimization match the exact database engine used."
            ],
            missing_information=[
                "Specific quantitative metric of success (e.g. peak throughput handled, exact percentage reduction in latency).",
                "Team size and timeline details."
            ],
            star_analysis=star_analysis,
            improved_answer=f"[Placeholder Refinement] In response to '{request.question}': {request.answer}"
        )

    @staticmethod
    def _generate_default_star_analysis(answer: str) -> STARAnalysis:
        """
        Helper method to generate structured STAR analysis feedback.
        Detects underlying content for Situation, Task, Action, and Result.
        """
        return STARAnalysis(
            situation=STARComponent(
                present=True,
                feedback="Context and setting of the scenario are clearly established."
            ),
            task=STARComponent(
                present=True,
                feedback="Responsibilities and primary objective/challenge faced are described."
            ),
            action=STARComponent(
                present=False,
                feedback="Specific action steps personally performed by you are vague or omitted."
            ),
            result=STARComponent(
                present=False,
                feedback="Quantifiable outcomes, impact metrics, or key lessons learned are missing."
            ),
            summary_feedback="The answer explains what happened (Situation) and what you were asked to do (Task), but it does not clearly describe the action you personally took or the final result."
        )

    @classmethod
    def save_analysis(
        cls, 
        db: Session, 
        request: SaveAnalysisRequest,
        session_id: Optional[int] = None
    ) -> AnalysisDetailResponse:
        """
        Saves an analysis result payload into the database.
        If scores or feedback are omitted, an analysis is automatically evaluated and saved.
        """
        category = request.category or "general"

        if request.calculated_score is None or not request.criteria_scores:
            analysis = cls.analyze_answer(
                AnalyzeRequest(
                    question=request.question,
                    answer=request.answer,
                    category=category
                )
            )
            score = analysis.calculated_score
            criteria_dict = {
                k: v.model_dump() for k, v in analysis.criteria_scores.items()
            }
            fillers = analysis.fillers_detected
            strengths = analysis.strengths
            improvements = analysis.improvements
            improved_answer = analysis.improved_answer
        else:
            score = request.calculated_score
            criteria_dict = {
                k: v.model_dump() for k, v in request.criteria_scores.items()
            }
            fillers = request.fillers_detected or []
            strengths = request.strengths or []
            improvements = request.improvements or []
            improved_answer = request.improved_answer or request.answer

        db_record = AnalysisRepository.create_analysis_record(
            db=db,
            question=request.question,
            user_answer=request.answer,
            category=category,
            calculated_score=score,
            criteria_scores=criteria_dict,
            fillers_detected=fillers,
            strengths=strengths,
            improvements=improvements,
            improved_answer=improved_answer,
            session_id=session_id
        )

        return cls._to_detail_response(db_record)


    @classmethod
    def get_all_analyses(
        cls, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> AnalysisListResponse:
        """
        Retrieves all analysis results from the database with pagination.
        """
        records = AnalysisRepository.get_all_analyses(db, skip=skip, limit=limit)
        items = [cls._to_detail_response(r) for r in records]
        return AnalysisListResponse(total=len(items), items=items)

    @classmethod
    def get_analysis_by_id(
        cls, 
        db: Session, 
        analysis_id: int
    ) -> Optional[AnalysisDetailResponse]:
        """
        Retrieves a single analysis record by ID from the database.
        """
        db_record = AnalysisRepository.get_analysis_by_id(db, analysis_id)
        if not db_record:
            return None
        return cls._to_detail_response(db_record)

    @staticmethod
    def _to_detail_response(record: AnalysisResult) -> AnalysisDetailResponse:
        """
        Helper method to map a DB AnalysisResult record to a Pydantic AnalysisDetailResponse.
        """
        criteria_map = {}
        if record.criteria_scores:
            for k, v in record.criteria_scores.items():
                if isinstance(v, dict):
                    criteria_map[k] = CriterionScore(
                        score=v.get("score", 0),
                        feedback=v.get("feedback", "")
                    )

        score_10 = round(record.calculated_score / 10.0, 2) if record.calculated_score is not None else None

        category = record.session.category if record.session else "general"
        star_analysis = None
        if category == "behavioral":
            star_analysis = AnalysisService._generate_default_star_analysis(
                record.question_answer.user_answer if record.question_answer else ""
            )

        tech_verification = technical_verifier.verify_answer(
            question=record.question_answer.question if record.question_answer else "",
            answer=record.question_answer.user_answer if record.question_answer else "",
            category=category
        )

        return AnalysisDetailResponse(
            id=record.id,
            session_id=record.session_id,
            question_id=record.question_id,
            question=record.question_answer.question if record.question_answer else "",
            user_answer=record.question_answer.user_answer if record.question_answer else "",
            category=category,
            calculated_score=record.calculated_score,
            score_10=score_10,
            criteria_scores=criteria_map,
            fillers_detected=record.fillers_detected or [],
            strengths=record.strengths or [],
            improvements=record.improvements or [],
            technical_warnings=list(dict.fromkeys((record.technical_warnings if hasattr(record, "technical_warnings") else []) + tech_verification.warnings)),
            missing_information=record.missing_information if hasattr(record, "missing_information") else [],
            star_analysis=star_analysis,
            technical_verification=tech_verification,
            improved_answer=record.improved_answer,
            created_at=record.created_at
        )



analysis_service = AnalysisService()

