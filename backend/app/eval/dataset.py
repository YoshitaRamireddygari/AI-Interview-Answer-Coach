from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EvalDatasetItem(BaseModel):
    """
    Schema for an interview evaluation test case item.
    """
    id: str = Field(..., description="Unique dataset item identifier")
    category: str = Field(..., description="Interview category: behavioral, technical, hr, project")
    question: str = Field(..., description="Interview question prompt")
    answer: str = Field(..., description="Candidate's submitted answer")
    expected_characteristics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Expected criteria characteristics, score boundaries, and STAR present/missing flags"
    )
    expected_issues: List[str] = Field(
        default=[],
        description="Expected technical issues, filler word warnings, or missing STAR narrative elements"
    )


# Small engineering evaluation dataset for reliability benchmarking
EVALUATION_DATASET: List[EvalDatasetItem] = [
    EvalDatasetItem(
        id="eval_01_behavioral_complete_star",
        category="behavioral",
        question="Tell me about a time when you faced a major project deadline pressure.",
        answer=(
            "During our Q3 payment gateway migration, a key third-party API was deprecated 2 weeks before launch (Situation). "
            "My task was to replace the integration without delaying the production rollout (Task). "
            "I refactored our payment client interface, implemented fallback retry logic, and wrote 45 automated integration tests (Action). "
            "As a result, we deployed on schedule with 0 downtime and improved payment processing latency by 22% (Result)."
        ),
        expected_characteristics={
            "min_score": 80.0,
            "max_score": 100.0,
            "expected_star": {
                "situation": True,
                "task": True,
                "action": True,
                "result": True
            }
        },
        expected_issues=[]
    ),
    EvalDatasetItem(
        id="eval_02_behavioral_missing_action_result",
        category="behavioral",
        question="Describe a time you handled a difficult conflict with a team member.",
        answer=(
            "Last year we were building a new microservice and my teammate wanted to use GraphQL while I wanted REST. "
            "It was a really intense project with tight deadlines and we had a lot of meetings about it."
        ),
        expected_characteristics={
            "min_score": 40.0,
            "max_score": 75.0,
            "expected_star": {
                "situation": True,
                "task": True,
                "action": False,
                "result": False
            }
        },
        expected_issues=["Missing Action", "Missing Result"]
    ),
    EvalDatasetItem(
        id="eval_03_technical_http_misconception",
        category="technical",
        question="Explain your backend architecture and what protocols/languages you used.",
        answer=(
            "We built our backend API service using FastAPI. HTTP is a programming language that we used to code our controller logic, "
            "and we used PostgreSQL for data persistence."
        ),
        expected_characteristics={
            "min_score": 30.0,
            "max_score": 75.0,
            "expect_technical_warning": True
        },
        expected_issues=["HTTP is a communication protocol, not a programming language."]
    ),
    EvalDatasetItem(
        id="eval_04_technical_complete_architecture",
        category="technical",
        question="How do you approach database selection, indexing, and caching for high-concurrency systems?",
        answer=(
            "I select PostgreSQL for relational data requiring strong ACID compliance, utilizing B-tree composite indexes on high-frequency query paths. "
            "For read-heavy endpoints, I implement Redis as an in-memory caching layer with TTL eviction to reduce DB load."
        ),
        expected_characteristics={
            "min_score": 80.0,
            "max_score": 100.0,
            "expect_technical_warning": False
        },
        expected_issues=[]
    ),
    EvalDatasetItem(
        id="eval_05_project_vague_individual_role",
        category="project",
        question="Walk me through your most impactful recent project and your specific role.",
        answer=(
            "We built a massive machine learning pipeline for customer churn prediction. Our team worked together and we deployed the model to AWS "
            "and everyone did a great job finishing the project."
        ),
        expected_characteristics={
            "min_score": 50.0,
            "max_score": 75.0
        },
        expected_issues=["Vague personal contribution", "Missing quantitative metrics"]
    ),
    EvalDatasetItem(
        id="eval_06_hr_filler_language",
        category="hr",
        question="What are your main professional strengths and one area you work to improve?",
        answer=(
            "Um, so basically, like, I think my main strength is that I'm really adaptable. Um, like whenever a problem pops up, "
            "basically I just dive right in and figure it out."
        ),
        expected_characteristics={
            "min_score": 50.0,
            "max_score": 80.0
        },
        expected_issues=["Filler words detected: um, basically, like"]
    )
]
