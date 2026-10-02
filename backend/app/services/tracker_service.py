import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session, joinedload

from app.db.models import InterviewSession, QuestionAnswer, AnalysisResult
from app.schemas.tracker import (
    ComponentAverages,
    OverallProgressResponse,
    ScoreHistoryItem,
    ScoreHistoryResponse,
    RecurringWeaknessItem,
    WeaknessesResponse
)

logger = logging.getLogger(__name__)

WEAKNESS_CATEGORIES_DEF = [
    {
        "category_key": "missing_metrics",
        "title": "Missing Measurable Results",
        "keywords": ["metric", "result", "outcome", "quantitative", "percent", "number", "data", "impact", "measurable", "measure", "stat"],
        "description": "Answers often describe activities without providing quantifiable impact or measurable metrics.",
        "actionable_tip": "Include specific quantitative results (e.g., 'reduced latency by 35%', 'handled 50k active users') to prove your accomplishments."
    },
    {
        "category_key": "weak_role",
        "title": "Weak Project-Role Explanation",
        "keywords": ["role", "project", "personal", "contribution", "responsibility", "ownership", "individually", "personally", "team vs"],
        "description": "Difficulty distinguishing your personal contributions from general team activities.",
        "actionable_tip": "Use clear 'I' statements when describing technical choices and problem-solving steps you personally led."
    },
    {
        "category_key": "filler_language",
        "title": "Repeated / Filler Language",
        "keywords": ["filler", "word", "language", "conversational", "um", "basically", "like", "phrase", "repetitive", "informal"],
        "description": "Frequent usage of conversational filler words or informal repetitive phrasing.",
        "actionable_tip": "Pause intentionally for 1-2 seconds to structure your thoughts instead of filling silence with 'um' or 'basically'."
    },
    {
        "category_key": "incomplete_technical",
        "title": "Incomplete Technical Explanations",
        "keywords": ["technical", "accuracy", "precision", "term", "depth", "detail", "architecture", "concept", "methodology", "code", "schema", "engine"],
        "description": "Technical concepts or system choices are mentioned at a surface level without domain precision.",
        "actionable_tip": "Explain the underlying mechanisms, trade-offs, and technical rationale behind key architecture choices."
    },
    {
        "category_key": "weak_structure",
        "title": "Weak Answer Structure (STAR)",
        "keywords": ["structure", "star", "situation", "task", "action", "flow", "organization", "narrative", "concise", "rambling"],
        "description": "Narrative structure lacks logical progression through Situation, Task, Action, and Result.",
        "actionable_tip": "Organize responses using the STAR format: Situation (15%), Task (15%), Action (50%), and Result (20%)."
    }
]


class TrackerService:
    """
    Analytics engine for calculating interview progress, score history,
    and deriving recurring improvement categories from stored evaluation data.
    """

    def get_overall_progress(self, db: Session) -> OverallProgressResponse:
        """
        Calculates aggregated score metrics, component score averages, and per-category averages.
        """
        records = (
            db.query(AnalysisResult)
            .options(joinedload(AnalysisResult.session))
            .all()
        )

        total_sessions = db.query(InterviewSession).count()
        total_answers = len(records)

        if total_answers == 0:
            return OverallProgressResponse(
                total_interviews_completed=0,
                total_answers_analyzed=0,
                average_overall_score=0.0,
                average_overall_score_10=0.0,
                component_averages=ComponentAverages(
                    relevance=0.0,
                    completeness=0.0,
                    clarity=0.0,
                    structure=0.0,
                    technical_accuracy=0.0
                ),
                category_averages={
                    "behavioral": 0.0,
                    "technical": 0.0,
                    "hr": 0.0,
                    "project": 0.0,
                    "general": 0.0
                }
            )

        sum_overall = sum(r.calculated_score for r in records)
        avg_overall = round(sum_overall / total_answers, 1)
        avg_overall_10 = round(avg_overall / 10.0, 1)

        # Component sums
        comp_sums = {
            "relevance": 0.0,
            "completeness": 0.0,
            "clarity": 0.0,
            "structure": 0.0,
            "technical_accuracy": 0.0
        }

        # Category sums & counts
        cat_sums: Dict[str, float] = {}
        cat_counts: Dict[str, int] = {}

        for r in records:
            cat = r.session.category if r.session else "general"
            cat_sums[cat] = cat_sums.get(cat, 0.0) + r.calculated_score
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

            if r.criteria_scores and isinstance(r.criteria_scores, dict):
                for c_name in comp_sums.keys():
                    c_data = r.criteria_scores.get(c_name)
                    if isinstance(c_data, dict):
                        sc = c_data.get("score", 0)
                        # Normalize 0-100 score to 0-10 scale
                        sc_10 = sc / 10.0 if sc > 10 else float(sc)
                        comp_sums[c_name] += sc_10

        comp_averages = ComponentAverages(
            relevance=round(comp_sums["relevance"] / total_answers, 1),
            completeness=round(comp_sums["completeness"] / total_answers, 1),
            clarity=round(comp_sums["clarity"] / total_answers, 1),
            structure=round(comp_sums["structure"] / total_answers, 1),
            technical_accuracy=round(comp_sums["technical_accuracy"] / total_answers, 1)
        )

        category_averages = {}
        all_categories = ["behavioral", "technical", "hr", "project", "general"]
        for cat in all_categories:
            if cat in cat_counts and cat_counts[cat] > 0:
                category_averages[cat] = round(cat_sums[cat] / cat_counts[cat], 1)
            else:
                category_averages[cat] = 0.0

        return OverallProgressResponse(
            total_interviews_completed=total_sessions,
            total_answers_analyzed=total_answers,
            average_overall_score=avg_overall,
            average_overall_score_10=avg_overall_10,
            component_averages=comp_averages,
            category_averages=category_averages
        )

    def get_score_history(self, db: Session, limit: int = 100) -> ScoreHistoryResponse:
        """
        Retrieves chronological history of analyzed scores for progress tracking charts.
        """
        records = (
            db.query(AnalysisResult)
            .options(
                joinedload(AnalysisResult.question_answer),
                joinedload(AnalysisResult.session)
            )
            .order_by(AnalysisResult.created_at.asc())
            .limit(limit)
            .all()
        )

        items: List[ScoreHistoryItem] = []
        for r in records:
            qa = r.question_answer
            q_text = qa.question if qa else "Interview Question"
            cat = r.session.category if r.session else "general"

            items.append(
                ScoreHistoryItem(
                    id=r.id,
                    session_id=r.session_id,
                    created_at=r.created_at,
                    question=q_text,
                    category=cat,
                    score=r.calculated_score,
                    score_10=round(r.calculated_score / 10.0, 1)
                )
            )

        return ScoreHistoryResponse(
            total=len(items),
            items=items
        )

    def get_recurring_weaknesses(self, db: Session) -> WeaknessesResponse:
        """
        Derives recurring weakness categories exclusively from empirical stored evaluation feedback.
        Ranks categories by occurrence frequency and includes actual user feedback snippets.
        """
        records = (
            db.query(AnalysisResult)
            .options(joinedload(AnalysisResult.question_answer))
            .all()
        )

        total_analyzed = len(records)
        if total_analyzed == 0:
            return WeaknessesResponse(total_analyzed=0, recurring_weaknesses=[])

        # Category tracking maps
        counts: Dict[str, int] = {cat["category_key"]: 0 for cat in WEAKNESS_CATEGORIES_DEF}
        examples: Dict[str, List[str]] = {cat["category_key"]: [] for cat in WEAKNESS_CATEGORIES_DEF}

        for r in records:
            # Combine feedback sources
            feedback_texts: List[str] = []
            if r.improvements:
                feedback_texts.extend(r.improvements)
            if r.fillers_detected:
                feedback_texts.append(f"Detected fillers: {', '.join(r.fillers_detected)}")
            if r.criteria_scores and isinstance(r.criteria_scores, dict):
                for c_val in r.criteria_scores.values():
                    if isinstance(c_val, dict) and "feedback" in c_val:
                        feedback_texts.append(c_val["feedback"])

            # Check matches for each weakness category
            for cat_def in WEAKNESS_CATEGORIES_DEF:
                key = cat_def["category_key"]
                matched = False
                for txt in feedback_texts:
                    txt_lower = txt.lower()
                    if any(kw in txt_lower for kw in cat_def["keywords"]):
                        matched = True
                        if len(examples[key]) < 3 and txt not in examples[key]:
                            examples[key].append(txt)

                if matched:
                    counts[key] += 1

        recurring_list: List[RecurringWeaknessItem] = []
        for cat_def in WEAKNESS_CATEGORIES_DEF:
            key = cat_def["category_key"]
            c = counts[key]
            pct = round((c / total_analyzed) * 100, 1)

            # Only include if observed at least once or default fallback
            recurring_list.append(
                RecurringWeaknessItem(
                    category_key=key,
                    title=cat_def["title"],
                    count=c,
                    percentage=pct,
                    description=cat_def["description"],
                    example_feedback=examples[key] if examples[key] else ["Improvement highlighted during answer evaluations."],
                    actionable_tip=cat_def["actionable_tip"]
                )
            )

        # Sort by frequency count descending
        recurring_list.sort(key=lambda x: x.count, reverse=True)

        return WeaknessesResponse(
            total_analyzed=total_analyzed,
            recurring_weaknesses=recurring_list
        )


tracker_service = TrackerService()
