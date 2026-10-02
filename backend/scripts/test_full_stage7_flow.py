#!/usr/bin/env python3
"""
Full End-to-End Flow Test Script for STAGE 7.
Simulates React Frontend API Request -> FastAPI Backend (/api/analyze) -> Gemini AI Service -> Deterministic Scoring Engine -> SQLite Database Persistence.
"""

import os
import sys
import json

# Add backend root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

def run_stage7_e2e_flow_test():
    print("=" * 75)
    print("STAGE 7: FULL END-TO-END FRONTEND -> BACKEND -> GEMINI -> DATABASE FLOW TEST")
    print("=" * 75)

    client = TestClient(app)

    # Simulated React Frontend payload matching App.jsx state & POST /api/analyze request
    frontend_request_payload = {
        "question": "Tell me about a time you had to lead a project under tight deadlines.",
        "answer": (
            "In my previous engineering role, we had a critical 3-week deadline to launch a new payments microservice. "
            "I organized daily standups, prioritized essential API endpoints, automated integration testing, and delegated "
            "database optimization tasks. We deployed 2 days ahead of schedule with zero high-severity incidents."
        ),
        "category": "behavioral"
    }

    print("\n1. [Frontend Output -> HTTP Request]")
    print(f"Target Endpoint : POST /api/analyze")
    print(f"Category        : {frontend_request_payload['category']}")
    print(f"Question        : {frontend_request_payload['question']}")
    print(f"Answer Length   : {len(frontend_request_payload['answer'])} characters")

    # Execute HTTP POST request
    response = client.post("/api/analyze", json=frontend_request_payload)
    
    print("\n2. [FastAPI Pipeline Response]")
    print(f"HTTP Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

    data = response.json()
    print("\n3. [Returned Analysis Payload received by Frontend Component]")
    print(f"  + Database Record ID : #{data.get('id')}")
    print(f"  + Session ID         : #{data.get('session_id')}")
    print(f"  + Execution Status   : {data.get('status')}")
    print(f"  + Weighted Score     : {data.get('calculated_score')}% ({data.get('score_10')} / 10)")
    print(f"  + Weights Config     : {data.get('weights_config')}")
    print(f"  + Score Breakdown    : {data.get('score_breakdown')}")

    print("\n4. [Criteria Scores Breakdown]")
    for comp, details in data.get("criteria_scores", {}).items():
        print(f"  - {comp.capitalize():20s}: {details['score']}/100 -> {details['feedback']}")

    print("\n5. [Grounded Feedback]")
    print("  + Strengths Identified:")
    for s in data.get("strengths", []):
        print(f"    * {s}")
    print("  + Areas for Improvement:")
    for imp in data.get("improvements", []):
        print(f"    * {imp}")
    print(f"\n  + Improved Answer Suggestion:\n    {data.get('improved_answer')}")

    # 6. Verify SQLite DB Persistence by querying GET /api/analyses/{id}
    record_id = data.get("id")
    assert record_id is not None, "Database record ID must not be None"

    db_fetch_res = client.get(f"/api/analyses/{record_id}")
    print(f"\n6. [SQLite Persistence Verification via GET /api/analyses/{record_id}]")
    print(f"Fetch Status Code: {db_fetch_res.status_code}")
    assert db_fetch_res.status_code == 200
    db_data = db_fetch_res.json()
    assert db_data["id"] == record_id
    assert db_data["question"] == frontend_request_payload["question"]
    print(f"✓ Record #{record_id} successfully retrieved from SQLite database!")

    print("\n" + "=" * 75)
    print("✓ STAGE 7 FULL FRONTEND -> BACKEND -> GEMINI -> DATABASE FLOW VERIFIED!")
    print("=" * 75)

if __name__ == "__main__":
    run_stage7_e2e_flow_test()
