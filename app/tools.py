"""Mock and RAG retrieval tools for the DevOps Release Assistant.

Provides read-only tools to fetch deployment status, perform release readiness checks,
and consult DevOps runbooks / documentation via Vertex AI RAG Engine.
"""

import os
from typing import Dict, Any

CORPUS_NAME = "projects/qwiklabs-gcp-03-6a55309796e4/locations/us-central1/ragCorpora/57060255435063296"


def get_deployment_status(application: str, environment: str) -> Dict[str, Any]:
    """Retrieves current deployment status and health metrics for a target application and environment.

    Args:
        application: Name of the application service (e.g., 'payments-service', 'auth-service', 'frontend-web').
        environment: Target deployment environment (e.g., 'staging', 'production', 'dev').

    Returns:
        Dict containing deployment state, active version, replica status, health check status, and last build ID.
    """
    app_lower = application.lower()
    env_lower = environment.lower()

    if env_lower == "production":
        if "payment" in app_lower:
            return {
                "application": application,
                "environment": environment,
                "status": "HEALTHY",
                "active_version": "v2.14.0",
                "desired_replicas": 5,
                "ready_replicas": 5,
                "health_check": "PASSING",
                "last_build_id": "build-8902",
                "last_deployed_at": "2026-09-22T18:30:00Z",
                "error_rate_percentage": 0.02,
            }
        elif "auth" in app_lower:
            return {
                "application": application,
                "environment": environment,
                "status": "DEGRADED",
                "active_version": "v1.8.2",
                "desired_replicas": 4,
                "ready_replicas": 2,
                "health_check": "FAILING_HTTP_500",
                "last_build_id": "build-8915",
                "last_deployed_at": "2026-09-23T08:15:00Z",
                "error_rate_percentage": 4.85,
            }
    elif env_lower == "staging":
        return {
            "application": application,
            "environment": environment,
            "status": "HEALTHY",
            "active_version": "v2.15.0-rc1",
            "desired_replicas": 2,
            "ready_replicas": 2,
            "health_check": "PASSING",
            "last_build_id": "build-8920",
            "last_deployed_at": "2026-09-23T09:00:00Z",
            "error_rate_percentage": 0.00,
        }

    return {
        "application": application,
        "environment": environment,
        "status": "HEALTHY",
        "active_version": "v1.0.0",
        "desired_replicas": 2,
        "ready_replicas": 2,
        "health_check": "PASSING",
        "last_build_id": "build-8800",
        "last_deployed_at": "2026-09-20T10:00:00Z",
        "error_rate_percentage": 0.00,
    }


def check_release_readiness(application: str, environment: str) -> Dict[str, Any]:
    """Evaluates release prerequisites and policy compliance for deploying an application to an environment.

    Args:
        application: Name of the application service (e.g., 'payments-service', 'auth-service', 'frontend-web').
        environment: Target deployment environment (e.g., 'staging', 'production', 'dev').

    Returns:
        Dict containing readiness verdict, test coverage results, security scan findings, approval statuses, and freeze window status.
    """
    app_lower = application.lower()
    env_lower = environment.lower()

    if env_lower == "production":
        if "auth" in app_lower:
            return {
                "application": application,
                "environment": environment,
                "readiness_verdict": "NOT_READY",
                "checks": {
                    "unit_tests": {"status": "PASSED", "coverage_percentage": 88.5},
                    "integration_tests": {"status": "PASSED", "passed_count": 142, "failed_count": 0},
                    "security_vulnerability_scan": {
                        "status": "FAILED",
                        "critical_vulnerabilities": 1,
                        "high_vulnerabilities": 3,
                        "details": "CVE-2026-3829 found in base container image",
                    },
                    "manager_approval": {"status": "PENDING", "approver": "sre-lead@company.com"},
                    "change_freeze_window": {"is_active": False},
                },
                "blockers": [
                    "Critical vulnerability CVE-2026-3829 must be remediated or exempted.",
                    "SRE Lead approval pending.",
                ],
            }
        else:
            return {
                "application": application,
                "environment": environment,
                "readiness_verdict": "READY",
                "checks": {
                    "unit_tests": {"status": "PASSED", "coverage_percentage": 92.1},
                    "integration_tests": {"status": "PASSED", "passed_count": 210, "failed_count": 0},
                    "security_vulnerability_scan": {
                        "status": "PASSED",
                        "critical_vulnerabilities": 0,
                        "high_vulnerabilities": 0,
                    },
                    "manager_approval": {"status": "APPROVED", "approved_by": "devops-lead@company.com"},
                    "change_freeze_window": {"is_active": False},
                },
                "blockers": [],
            }

    return {
        "application": application,
        "environment": environment,
        "readiness_verdict": "READY",
        "checks": {
            "unit_tests": {"status": "PASSED", "coverage_percentage": 90.0},
            "integration_tests": {"status": "PASSED", "passed_count": 50, "failed_count": 0},
            "security_vulnerability_scan": {
                "status": "PASSED",
                "critical_vulnerabilities": 0,
                "high_vulnerabilities": 0,
            },
            "manager_approval": {"status": "NOT_REQUIRED_FOR_STAGING"},
            "change_freeze_window": {"is_active": False},
        },
        "blockers": [],
    }


def _local_runbook_search(query: str) -> str:
    """Local fallback search across DevOps runbooks."""
    candidate_dirs = [
        "/config/Desktop/Session1/app/devops_runbooks",
        "/config/Desktop/Session1/docs",
        os.path.join(os.path.dirname(__file__), "devops_runbooks"),
        os.path.join(os.path.dirname(__file__), "..", "docs"),
    ]

    docs_dir = None
    for d in candidate_dirs:
        if os.path.exists(d) and os.path.isdir(d):
            docs_dir = d
            break

    query_lower = query.lower()
    matches = []

    if docs_dir:
        for filename in sorted(os.listdir(docs_dir)):
            if filename.endswith(".md"):
                filepath = os.path.join(docs_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    terms = [t for t in query_lower.split() if len(t) > 3]
                    if not terms or any(term in content.lower() for term in terms):
                        matches.append(f"--- Document: {filename} ---\n{content}")

    return "\n\n".join(matches) if matches else "No relevant runbook passage found."


def consult_devops_runbooks(query: str) -> str:
    """Search the DevOps runbooks knowledge base for procedures, checklists, prerequisites, rollback steps, and emergency policies.

    Args:
        query: Search term or question regarding DevOps procedures (e.g., 'release prerequisites', 'production deployment checklist', 'rollback procedure', 'emergency release').

    Returns:
        Relevant passages and policy instructions retrieved from the DevOps runbook corpus.
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-6a55309796e4")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    try:
        import vertexai
        from vertexai.preview import rag

        vertexai.init(project=project_id, location=location)
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
        contexts = getattr(resp.contexts, "contexts", [])
        passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
        if passages:
            return "\n\n---\n\n".join(passages)
    except Exception as e:
        print(f"Vertex AI RAG query notice: {e}")

    # Fallback to local runbooks search if corpus is indexing or unavailable
    return _local_runbook_search(query)
