# My agent: Enterprise DevOps Release Assistant (ReleaseOps AI)

One-liner: A stateful conversational agent that helps DevOps engineers, SREs, and Release Managers analyze CI/CD pipeline failures, query deployment procedures grounded in SRE runbooks via RAG, enforce release governance, and maintain session memory.

## Tool coverage

- **Memory**: Remembers user preferences, active cloud environments (staging/prod), deployment targets, past incident history, and resolution context across sessions (powered by Vertex AI Memory Bank).
- **Tools**:
  - `analyze_ci_build_log`: Parses build/deployment logs to extract errors and stack traces.
  - `search_sre_runbooks`: Grounded retrieval of SOPs, troubleshooting guides, and architecture specs (Vertex AI RAG Engine).
  - `check_release_governance`: Evaluates deployment readiness against security, compliance, and approval policies.
  - `get_pipeline_status`: Fetches live status of CI/CD builds and environments.
- **Catalog/UI**: Build pipeline summary tables, deployment environment cards, runbook search results, and governance checklist cards (rendered via A2UI).
- **Image gen**: Generates visual release status badges, deployment topology diagrams, and incident severity cards.
- **Sandbox**: Computes pipeline performance telemetry, MTTR (Mean Time to Recovery), build failure rates, and log metric distributions.

---

## Core Rails & Stretch Menu

- **Core rails (everyone)**: Vertex AI Memory Bank, custom function tools, evaluation dataset, deployment to Agent Runtime, Cloud Run frontend.
- **My stretch menu (pick later)**:
  - Specialized multi-agent architecture (CI Analysis Subagent, Governance Subagent, RAG Subagent).
  - Vertex AI RAG Engine for SRE markdown runbooks.
  - A2UI cards for build status and incident diagnostics.
  - Code sandbox for log telemetry parsing.

---

## First Eval Question

> **Query**: "Build #402 in `prod-release` failed during the database migration step. What caused the failure, is it safe to retry, and what does the SRE runbook recommend?"  
> **Expected Output**: The agent identifies the missing schema migration lock, cites section 4.2 of the Postgres Runbook, checks that governance permits a retry with rollback strategy, and formats the output into a diagnostic card with clear remediation steps.

---

## Proposed System Architecture

```
                                 ┌─────────────────────────────────────────┐
                                 │              User / Browser             │
                                 └────────────────────┬────────────────────┘
                                                      │ HTTP / WebSocket
                                                      ▼
                                 ┌─────────────────────────────────────────┐
                                 │     FastAPI Proxy + A2UI Frontend       │
                                 │             (Cloud Run)                 │
                                 └────────────────────┬────────────────────┘
                                                      │ A2A Protocol
                                                      ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Agent Platform / Agent Runtime                                       │
│                                                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                               DevOps Release Assistant (Orchestrator)                            │  │
│  │                                        (ADK / Python)                                            │  │
│  └──────┬────────────────────┬─────────────────────────────┬───────────────────────────┬────────────┘  │
│         │                    │                             │                           │               │
│         ▼                    ▼                             ▼                           ▼               │
│  ┌──────────────┐   ┌─────────────────┐           ┌───────────────────┐       ┌─────────────────┐      │
│  │ CI Analysis  │   │   Release       │           │   Documentation   │       │  Code Sandbox   │      │
│  │   Subagent   │   │ Governance Agent│           │    (RAG) Agent    │       │ (Log Telemetry) │      │
│  └──────┬───────┘   └────────┬────────┘           └─────────┬─────────┘       └─────────────────┘      │
│         │                    │                              │                                          │
└─────────┼────────────────────┼──────────────────────────────┼──────────────────────────────────────────┘
          │                    │                              │
          ▼                    ▼                              ▼
  ┌──────────────┐   ┌──────────────────┐           ┌───────────────────┐       ┌─────────────────┐
  │  Firestore   │   │ IAM & Governance │           │ Vertex AI RAG     │       │ Vertex AI       │
  │ (Build logs, │   │    Policies      │           │ Engine (Runbooks) │       │ Memory Bank     │
  │  incidents)  │   └──────────────────┘           └───────────────────┘       └─────────────────┘
  └──────────────┘
```

### Component Breakdown
1. **Orchestrator Agent**: Primary ADK agent maintaining conversation flow, delegating specialized queries to subagents or direct tools.
2. **CI Analysis Subagent**: Specialized agent focusing on parsing log traces, identifying root causes, and categorizing failure types.
3. **Release Governance Agent**: Enforces policy gates, checks approval requirements, and verifies change-window windows.
4. **Documentation / RAG Agent**: Grounded retrieval from Vertex AI RAG Engine populated with enterprise SOPs, deployment runbooks, and cloud architecture docs.
5. **Memory Layer**: Vertex AI Memory Bank for cross-session persistent recall of environment configs and team preferences.
6. **Data & Storage**: Firestore for structured pipeline metadata and incident history; Cloud Storage for log blobs and generated visual assets.
