"""Integration Test Suite for Deployed Cloud Run ReleaseOps AI Application.

Tests:
1. Health check endpoint (`GET /health`)
2. CI/CD Failure Analysis query (`POST /chat`)
3. Release Readiness governance query (`POST /chat`)
4. Runbook retrieval / emergency release RAG query (`POST /chat`)
5. Cross-session Memory Bank context recall (`POST /chat`)
"""

import sys
import json
import time
import requests

CLOUD_RUN_URL = sys.argv[1] if len(sys.argv) > 1 else ""

if not CLOUD_RUN_URL:
    print("Usage: python3 tests/test_cloud_run_deployed.py <CLOUD_RUN_SERVICE_URL>")
    sys.exit(1)

CLOUD_RUN_URL = CLOUD_RUN_URL.rstrip("/")

print(f"==================================================")
print(f"Testing Deployed Cloud Run Service: {CLOUD_RUN_URL}")
print(f"==================================================\n")

# 1. Health Check Test
health_url = f"{CLOUD_RUN_URL}/health"
print(f"[1/5] Probing Health Endpoint: {health_url}...")
try:
    resp = requests.get(health_url, timeout=15)
    print(f"Health Status Code: {resp.status_code}")
    print(f"Health Response: {resp.text}\n")
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}"
    health_data = resp.json()
    assert health_data.get("status") == "healthy", "Expected status healthy"
    print("✅ HEALTH CHECK PASSED!\n")
except Exception as e:
    print(f"❌ HEALTH CHECK FAILED: {e}\n")

# 2. CI/CD Failure Analysis Query
chat_url = f"{CLOUD_RUN_URL}/chat"
print(f"[2/5] Testing Query 1: GitHub Actions Failure Analysis...")
q1_payload = {
    "user_id": "cloud-run-verifier",
    "message": "Why did GitHub Actions run 35428930729 fail in repository ctssddevopsengineer/wedding-invitation-site?"
}
try:
    resp = requests.post(chat_url, json=q1_payload, timeout=60)
    print(f"Q1 Status Code: {resp.status_code}")
    q1_data = resp.json()
    print("Q1 Response Parts:")
    for part in q1_data.get("parts", []):
        if part.get("kind") == "text":
            print(f"- Text: {part.get('text')[:300]}...")
        elif part.get("kind") == "a2ui":
            print(f"- A2UI Component: {json.dumps(part.get('data'))[:200]}...")
    print("✅ Q1 PASSED!\n")
except Exception as e:
    print(f"❌ Q1 FAILED: {e}\n")

# 3. Release Readiness Query
print(f"[3/5] Testing Query 2: Release Readiness Check...")
q2_payload = {
    "user_id": "cloud-run-verifier",
    "message": "Check release readiness for auth-service in UAT"
}
try:
    resp = requests.post(chat_url, json=q2_payload, timeout=60)
    print(f"Q2 Status Code: {resp.status_code}")
    q2_data = resp.json()
    print("Q2 Response Parts:")
    for part in q2_data.get("parts", []):
        if part.get("kind") == "text":
            print(f"- Text: {part.get('text')[:300]}...")
        elif part.get("kind") == "a2ui":
            print(f"- A2UI Component: {json.dumps(part.get('data'))[:200]}...")
    print("✅ Q2 PASSED!\n")
except Exception as e:
    print(f"❌ Q2 FAILED: {e}\n")

# 4. RAG Runbook Query
print(f"[4/5] Testing Query 3: Emergency Release Procedure (RAG)...")
q3_payload = {
    "user_id": "cloud-run-verifier",
    "message": "What is our emergency release procedure?"
}
try:
    resp = requests.post(chat_url, json=q3_payload, timeout=60)
    print(f"Q3 Status Code: {resp.status_code}")
    q3_data = resp.json()
    print("Q3 Response Parts:")
    for part in q3_data.get("parts", []):
        if part.get("kind") == "text":
            print(f"- Text: {part.get('text')[:300]}...")
        elif part.get("kind") == "a2ui":
            print(f"- A2UI Component: {json.dumps(part.get('data'))[:200]}...")
    print("✅ Q3 PASSED!\n")
except Exception as e:
    print(f"❌ Q3 FAILED: {e}\n")

# 5. Cross-Session Memory Bank Recall Query
print(f"[5/5] Testing Query 4: Cross-Session Memory Bank Context Recall...")
q4_payload = {
    "user_id": "cloud-run-verifier",
    "message": "What service and environment are we currently discussing?"
}
try:
    resp = requests.post(chat_url, json=q4_payload, timeout=60)
    print(f"Q4 Status Code: {resp.status_code}")
    q4_data = resp.json()
    print("Q4 Response Parts:")
    for part in q4_data.get("parts", []):
        if part.get("kind") == "text":
            print(f"- Text: {part.get('text')[:300]}...")
        elif part.get("kind") == "a2ui":
            print(f"- A2UI Component: {json.dumps(part.get('data'))[:200]}...")
    print("✅ Q4 PASSED!\n")
except Exception as e:
    print(f"❌ Q4 FAILED: {e}\n")

print("==================================================")
print("ALL DEPLOYED CLOUD RUN TESTS EXECUTED!")
print("==================================================")
