#!/usr/bin/env python3
"""
Standalone execution test script for Gemini AI Evaluation Service.
Tests Gemini service independently with a sample interview question and answer.
"""

import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add backend root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.gemini_service import GeminiService, gemini_service, GeminiServiceError
from app.schemas.gemini import GeminiEvaluationResult, CriterionEvaluation


def run_standalone_test():
    print("=" * 70)
    print("STAGE 4: STANDALONE GEMINI SERVICE EVALUATION TEST")
    print("=" * 70)

    sample_question = "Tell me about a time you had to optimize a slow backend API endpoint."
    sample_answer = (
        "In my previous project, our user search endpoint was taking over 3 seconds. "
        "I analyzed the SQL queries using EXPLAIN ANALYZE and discovered missing indexes on the search columns "
        "as well as N+1 query loading issues. I added a composite index, refactored SQLAlchemy joins to use eager loading, "
        "and added a Redis cache layer for popular queries. Response time dropped to under 80ms."
    )
    sample_category = "technical"

    print(f"\n[Sample Input]")
    print(f"Category: {sample_category}")
    print(f"Question: {sample_question}")
    print(f"User Answer: {sample_answer}\n")

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    is_live_key = len(api_key) > 0 and api_key not in ["your_gemini_api_key_here", "YOUR_GEMINI_API_KEY"]

    if is_live_key:
        print("[Mode] LIVE API KEY DETECTED - Calling Gemini remote API...")
        try:
            service = GeminiService()
            result = service.evaluate_answer(
                question=sample_question,
                answer=sample_answer,
                category=sample_category
            )
            print("\n[LIVE GEMINI RESPONSE RECEIVED]")
        except GeminiServiceError as err:
            print(f"[Error calling Live Gemini API]: {err}")
            sys.exit(1)
    else:
        print("[Mode] NO LIVE API KEY FOUND - Executing with Mocked Gemini API response...")
        service = GeminiService(api_key="mock_test_key_stage4")
        
        mock_raw_json = json.dumps({
            "relevance": {
                "score": 10,
                "reason": "Directly addresses backend API performance optimization with clear context."
            },
            "completeness": {
                "score": 9,
                "reason": "Thoroughly details problem (3s latency), root cause (missing indexes/N+1), actions (EXPLAIN ANALYZE, composite index, Redis), and result (80ms)."
            },
            "clarity": {
                "score": 9,
                "reason": "Concise, precise technical narrative without unnecessary filler words."
            },
            "structure": {
                "score": 9,
                "reason": "Follows STAR framework clearly (Situation -> Task -> Action -> Result)."
            },
            "technical_accuracy": {
                "score": 10,
                "reason": "Technical concepts (EXPLAIN ANALYZE, SQLAlchemy eager loading, Redis caching) are used accurately."
            },
            "strengths": [
                "Quantified results before (3s) and after (80ms).",
                "Demonstrates deep database and caching expertise.",
                "Structured STAR delivery."
            ],
            "improvements": [
                "Mention peak request volume handled if applicable [Insert peak throughput]."
            ],
            "improved_answer": (
                "In my previous role, our search endpoint latency exceeded 3 seconds during peak traffic. "
                "I profiled query execution using EXPLAIN ANALYZE, identifying unindexed columns and N+1 query patterns. "
                "I introduced a composite index, optimized ORM joins with eager loading, and implemented Redis caching, "
                "which successfully reduced latency to under 80ms."
            ),
            "technical_warnings": []
        })

        mock_resp = MagicMock()
        mock_resp.text = mock_raw_json
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_resp

        with patch.object(service, "_get_client", return_value=mock_client):
            result = service.evaluate_answer(
                question=sample_question,
                answer=sample_answer,
                category=sample_category
            )
        print("\n[MOCKED GEMINI EVALUATION COMPLETED]")

    # Display and validate evaluation output
    print("-" * 70)
    print("EVALUATION RESULT BREAKDOWN:")
    print("-" * 70)
    print(f"Relevance          : {result.relevance.score}/10 -> Reason: {result.relevance.reason}")
    print(f"Completeness       : {result.completeness.score}/10 -> Reason: {result.completeness.reason}")
    print(f"Clarity            : {result.clarity.score}/10 -> Reason: {result.clarity.reason}")
    print(f"Structure          : {result.structure.score}/10 -> Reason: {result.structure.reason}")
    print(f"Technical Accuracy : {result.technical_accuracy.score}/10 -> Reason: {result.technical_accuracy.reason}")
    print("-" * 70)
    print("Strengths:")
    for s in result.strengths:
        print(f"  + {s}")
    print("\nImprovements:")
    for imp in result.improvements:
        print(f"  - {imp}")
    print(f"\nImproved Answer (Grounded in user's stated experience):\n{result.improved_answer}")
    if result.technical_warnings:
        print("\nTechnical Warnings:")
        for w in result.technical_warnings:
            print(f"  ! {w}")
    print("=" * 70)
    print("✓ STAGE 4 STANDALONE GEMINI SERVICE TEST PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_standalone_test()
