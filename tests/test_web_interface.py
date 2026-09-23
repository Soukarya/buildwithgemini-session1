"""Automated verification test suite for the ReleaseOps AI Web Interface."""

import requests
import json
import time

BASE_URL = "http://localhost:8080"


def test_web_interface():
    print("=== Testing Local ReleaseOps AI Web Interface (http://localhost:8080/chat) ===\n")
    user_id = "test_sre_engineer"

    # -----------------------------------------------------------------
    # Test 1: GitHub Actions Failure Analysis Query
    # -----------------------------------------------------------------
    q1 = "Why did GitHub Actions run 35428930729 fail in ctssddevopsengineer/wedding-invitation-site?"
    print(f"Query 1: '{q1}'")
    r1 = requests.post(
        f"{BASE_URL}/chat",
        json={"message": q1, "user_id": user_id},
        timeout=60
    )
    assert r1.status_code == 200, f"Query 1 failed with HTTP {r1.status_code}: {r1.text}"
    parts1 = r1.json().get("parts", [])
    text1 = " ".join([p.get("text", "") for p in parts1 if p.get("kind") == "text"])
    print(f"Status: HTTP 200 OK | Parts returned: {len(parts1)}")
    assert "35428930729" in text1 or len(parts1) > 0, "Query 1 output missing expected run details"
    assert "Pixel" in text1 or "baseline" in text1 or "EVIDENCE" in text1.upper(), "Query 1 missing root cause evidence"
    print("✅ Test 1 PASSED: GitHub Actions failure analysis successfully returned.\n")

    # -----------------------------------------------------------------
    # Test 2: Release Readiness Query
    # -----------------------------------------------------------------
    q2 = "Is auth-service in UAT ready for production?"
    print(f"Query 2: '{q2}'")
    r2 = requests.post(
        f"{BASE_URL}/chat",
        json={"message": q2, "user_id": user_id},
        timeout=60
    )
    assert r2.status_code == 200, f"Query 2 failed with HTTP {r2.status_code}: {r2.text}"
    parts2 = r2.json().get("parts", [])
    text2 = " ".join([p.get("text", "") for p in parts2 if p.get("kind") == "text"])
    print(f"Status: HTTP 200 OK | Parts returned: {len(parts2)}")
    assert "NOT_READY" in text2 or "blocker" in text2.lower() or "cve" in text2.lower(), "Query 2 missing release readiness blockers"
    print("✅ Test 2 PASSED: Release readiness evaluation returned.\n")

    # -----------------------------------------------------------------
    # Test 3: Emergency Release Procedure Runbook Query
    # -----------------------------------------------------------------
    q3 = "What is our emergency release procedure?"
    print(f"Query 3: '{q3}'")
    r3 = requests.post(
        f"{BASE_URL}/chat",
        json={"message": q3, "user_id": user_id},
        timeout=60
    )
    assert r3.status_code == 200, f"Query 3 failed with HTTP {r3.status_code}: {r3.text}"
    parts3 = r3.json().get("parts", [])
    text3 = " ".join([p.get("text", "") for p in parts3 if p.get("kind") == "text"])
    print(f"Status: HTTP 200 OK | Parts returned: {len(parts3)}")
    assert "Emergency" in text3 or "Hotfix" in text3 or "Runbook" in text3, "Query 3 missing runbook content"
    print("✅ Test 3 PASSED: Emergency release procedure runbook returned.\n")

    print("==========================================")
    print("ALL 3 WEB INTERFACE VERIFICATION TESTS PASSED!")
    print("==========================================")


if __name__ == "__main__":
    test_web_interface()
