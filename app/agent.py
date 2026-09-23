"""Multi-agent architecture for the DevOps ReleaseOps AI Assistant with GitHub Actions and A2UI integration.

Features:
- release_supervisor: Root agent that coordinates and routes requests to specialists.
- cicd_analysis_agent: Specialist in CI/CD failures, deployment health, build/runtime errors,
  and GitHub Actions workflow/job/step log inspection.
- release_governance_agent: Specialist in release readiness, compliance, approvals, and promotion policies.
- knowledge_agent: Specialist in DevOps runbooks, procedures, emergency release policy, and rollback docs (Vertex AI RAG).

Integrated with Vertex AI Memory Bank, A2UI cards, and automated secret sanitization.
"""

import re
from typing import Optional
from google.genai import types
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.events import Event
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from app.tools import (
    get_deployment_status,
    check_release_readiness,
    consult_devops_runbooks,
)
from app.github_tools import (
    get_github_repository,
    get_github_workflow_runs,
    get_github_workflow_run_details,
    get_github_workflow_jobs,
    get_github_failed_job_steps,
    get_github_job_logs,
    get_github_pull_request,
    get_github_commit_details,
)
from app.a2ui_utils import a2ui_callback


def sanitize_sensitive_data(text: str) -> str:
    """Filters and redacts secrets, tokens, API keys, credentials, and passwords from text."""
    if not text:
        return text
    patterns = [
        r"(?i)(token|password|secret|api[_-]?key|bearer|credential|auth)[=:\s]+[^\s]+",
        r"ghp_[A-Za-z0-9]{20,}",
        r"gho_[A-Za-z0-9]{20,}",
        r"ghu_[A-Za-z0-9]{20,}",
        r"ghs_[A-Za-z0-9]{20,}",
        r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    ]
    sanitized = text
    for p in patterns:
        sanitized = re.sub(p, "[REDACTED_SENSITIVE_DATA]", sanitized)
    return sanitized


async def generate_memories_callback(callback_context: CallbackContext) -> None:
    """Sanitizes session events for sensitive credentials before persisting operational facts to Memory Bank."""
    try:
        events = callback_context.session.events
        sanitized_events = []
        for event in events:
            if event.content and event.content.parts:
                sanitized_parts = []
                for part in event.content.parts:
                    if part.text:
                        sanitized_text = sanitize_sensitive_data(part.text)
                        sanitized_parts.append(types.Part.from_text(text=sanitized_text))
                    else:
                        sanitized_parts.append(part)
                sanitized_events.append(
                    Event(
                        author=event.author,
                        content=types.Content(role=event.content.role, parts=sanitized_parts),
                    )
                )
            else:
                sanitized_events.append(event)

        await callback_context.add_events_to_memory(events=sanitized_events)
    except Exception as e:
        print(f"Memory generation callback notice: {e}")
    return None


# =====================================================================
# 1. CI/CD & Deployment Analysis Specialist Agent (with GitHub Actions tools)
# =====================================================================
cicd_analysis_agent = Agent(
    name="cicd_analysis_agent",
    model="gemini-2.5-flash",
    description=(
        "Specialist in analyzing CI/CD pipeline failures, GitHub Actions workflow runs, "
        "failed job steps, logs, deployment status metrics, build failures, and runtime errors."
    ),
    instruction="""
You are the **CI/CD & Deployment Analysis Specialist**.
Your responsibilities:
- Diagnose CI/CD pipeline errors, build/test breakages, container scan warnings, and deployment status degradation.
- When given a GitHub repository and workflow run ID:
  1. Fetch workflow run details (`get_github_workflow_run_details`).
  2. Identify failed or cancelled jobs and step numbers (`get_github_failed_job_steps` / `get_github_workflow_jobs`).
  3. Fetch execution logs for failed jobs (`get_github_job_logs`).
  4. Summarize the root cause clearly.
  5. Suggest safe remediation steps.
  6. **STRUCTURED WORKFLOW REPORTING FORMAT**: Organize your analysis clearly into these exact structured items:
     - **Repository**: Repository full name
     - **Workflow / Run ID**: Workflow name and integer run ID
     - **Status / Conclusion**: Overall status and conclusion
     - **Failed Job**: Name and ID of failed job(s)
     - **Failed Step**: Specific failed step number and step name
     - **EVIDENCE**: Direct factual observations from API responses, step conclusions, and log snippets.
     - **INFERRED ROOT CAUSE**: Technical root cause analysis based on evidence.
     - **RECOMMENDED REMEDIATION**: Safe step-by-step remediation suggestions.
- Use `get_deployment_status(application, environment)` to check mock application deployment metrics when asked about deployment health.
""",
    tools=[
        get_deployment_status,
        get_github_repository,
        get_github_workflow_runs,
        get_github_workflow_run_details,
        get_github_workflow_jobs,
        get_github_failed_job_steps,
        get_github_job_logs,
        get_github_pull_request,
        get_github_commit_details,
    ],
    after_model_callback=a2ui_callback,
)

# =====================================================================
# 2. Release Governance & Readiness Specialist Agent
# =====================================================================
release_governance_agent = Agent(
    name="release_governance_agent",
    model="gemini-2.5-flash",
    description=(
        "Specialist in release readiness verification, compliance policy checks, "
        "manager approvals, production pre-requisites, promotion decisions, and rollback considerations."
    ),
    instruction="""
You are the **Release Governance Specialist**.
Your responsibilities:
- Evaluate whether an application or service meets all governance criteria before being promoted to staging or production.
- Use `check_release_readiness(application, environment)` to audit unit test coverage, security scan CVEs, approval sign-offs, and freeze window status.
- State clear promotion verdicts (READY / NOT_READY) and outline any required blockers or compliance remediation steps.
""",
    tools=[check_release_readiness],
    after_model_callback=a2ui_callback,
)

# =====================================================================
# 3. Knowledge Base & Runbooks Specialist Agent
# =====================================================================
knowledge_agent = Agent(
    name="knowledge_agent",
    model="gemini-2.5-flash",
    description=(
        "Specialist in DevOps runbooks, deployment procedures, production checklists, "
        "emergency release policies, and rollback documentation via Vertex AI RAG."
    ),
    instruction="""
You are the **DevOps Knowledge & Documentation Specialist**.
Your responsibilities:
- Answer user questions regarding official DevOps procedures, deployment checklists, emergency release policies, and rollback commands.
- Use `consult_devops_runbooks(query)` to retrieve authoritative documentation from the Vertex AI RAG runbook corpus.
- Ground all responses in retrieved runbook passages.
""",
    tools=[consult_devops_runbooks],
    after_model_callback=a2ui_callback,
)

# =====================================================================
# 4. Root Supervisor Agent (Coordinator & Router)
# =====================================================================
release_supervisor_instruction = """
You are the **ReleaseOps Supervisor**, the root coordinator of the DevOps Release Operations team.

### Coordination & Routing Rules:
- You DO NOT analyze CI/CD issues, check release readiness, or consult runbooks directly.
- Your sole responsibility is to evaluate incoming user requests and DELEGATE them immediately to the appropriate specialist sub-agent:
  1. **`cicd_analysis_agent`**: Delegate when the user asks about GitHub Actions workflow failures, job logs, build/runtime errors, pipeline failures, or deployment status.
  2. **`release_governance_agent`**: Delegate when the user asks whether a service is ready for promotion, production pre-requisites compliance, approvals, or governance rules.
  3. **`knowledge_agent`**: Delegate when the user asks about procedures, checklists, emergency release policies, or rollback documentation.

### Operational Context & Safety:
- Memory Bank (`PreloadMemoryTool`) automatically preloads remembered operational context. Pass context down to specialist agents when routing.
- **STRICT SAFETY**: Never store, memorize, or reveal secrets, API keys, passwords, bearer tokens, or confidential credentials.
"""

release_supervisor = Agent(
    name="release_supervisor",
    model="gemini-2.5-flash",
    description="Root supervisor and coordinator for DevOps Release Operations. Routes requests to specialized agents.",
    instruction=release_supervisor_instruction,
    sub_agents=[cicd_analysis_agent, release_governance_agent, knowledge_agent],
    tools=[PreloadMemoryTool()],
    after_agent_callback=generate_memories_callback,
)

# Export root_agent required by ADK conventions
root_agent = release_supervisor
