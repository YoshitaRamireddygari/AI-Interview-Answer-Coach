#!/usr/bin/env python3
import sys
import os
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.eval.evaluator import AIReliabilityEvaluator


def main():
    print("==========================================================================")
    print("          AI INTERVIEW COACH - RELIABILITY EVALUATION RUNNER            ")
    print("==========================================================================")
    
    report = AIReliabilityEvaluator.run_evaluation()
    m = report.metrics

    print(f"\nTimestamp: {report.timestamp}")
    print(f"Total Evaluation Test Items: {m.total_eval_items}\n")

    print("--------------------------------------------------------------------------")
    print("                    MEASURED RELIABILITY METRICS                          ")
    print("--------------------------------------------------------------------------")
    print(f"  • Valid JSON Response Rate:           {m.valid_json_response_rate}%")
    print(f"  • Schema Validation Success Rate:     {m.schema_validation_success_rate}%")
    print(f"  • Score Range Validity (0-10/0-100): {m.score_range_validity_rate}%")
    print(f"  • Score Consistency & Determinism:    {m.consistency_rate}%")
    print(f"  • Feedback Coverage (Strengths/Imp):  {m.missing_feedback_coverage_rate}%")
    print(f"  • Anti-Fabrication Pass Rate:         {m.hallucination_detection_pass_rate}%")
    print("--------------------------------------------------------------------------\n")

    print("--------------------------------------------------------------------------")
    print("                   ENGINEERING DISCLAIMER                                 ")
    print("--------------------------------------------------------------------------")
    print(report.disclaimer)
    print("==========================================================================\n")

    # Optionally save evaluation report artifact
    artifact_path = os.path.join(os.path.dirname(__file__), "eval_report_output.json")
    with open(artifact_path, "w") as f:
        json.dump(report.model_dump(), f, indent=2)
    print(f"Full JSON evaluation report saved to: {artifact_path}\n")


if __name__ == "__main__":
    main()
