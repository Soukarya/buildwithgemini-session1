"""FastAPI Proxy & Web Server for the ReleaseOps AI Multi-Agent Assistant.

Serves the chat UI and communicates with the underlying ADK multi-agent backend
(`release_supervisor`, `cicd_analysis_agent`, `release_governance_agent`, `knowledge_agent`)
via local Runner + Vertex AI Memory Bank or A2A protocol.
"""

import os
import sys
import json
import uuid
import asyncio
from typing import Dict, Any

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure Vertex AI environment variables are set
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-6a55309796e4")
os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import VertexAiMemoryBankService, InMemoryMemoryService

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.agent import root_agent
from app.memory_config import MEMORY_BANK_ID

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-6a55309796e4")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
APP_NAME = "releaseops_web_frontend"

# Initialize local ADK Runner with Vertex AI Memory Bank
session_service = InMemorySessionService()
try:
    print(f"Frontend proxy connecting to Vertex AI Memory Bank ID: {MEMORY_BANK_ID}...")
    memory_service = VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=MEMORY_BANK_ID,
    )
except Exception as e:
    print(f"Notice connecting to Memory Bank: {e}, falling back to InMemoryMemoryService...")
    memory_service = InMemoryMemoryService()

local_runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
    memory_service=memory_service,
)

# Store user session IDs across chat turns
_user_sessions: Dict[str, str] = {}

app = FastAPI(title="ReleaseOps AI Multi-Agent Assistant")


@app.get("/health")
async def health_check():
    """Explicit health check endpoint for Cloud Run and monitoring probes."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "app": "ReleaseOps AI Multi-Agent Assistant",
            "project_id": PROJECT_ID,
            "region": LOCATION,
            "memory_bank_id": MEMORY_BANK_ID,
            "backend": "google-adk",
        },
    )


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    """Ensure all exceptions return formatted JSON instead of HTML error pages."""
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )


@app.post("/chat")
async def chat(req: Request):
    """Handle chat messages from web frontend and route through ADK Runner."""
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "devops-engineer"

    if user_id not in _user_sessions:
        session = await local_runner.session_service.create_session(app_name=APP_NAME, user_id=user_id)
        _user_sessions[user_id] = session.id

    session_id = _user_sessions[user_id]

    user_msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text=message)]
    )

    parts = []
    
    async for event in local_runner.run_async(user_id=user_id, session_id=session_id, new_message=user_msg):
        if event.content:
            for part in event.content.parts:
                if part.text:
                    text = part.text.strip()
                    if not text:
                        continue
                    # Detect A2UI payload or normal markdown text
                    if "beginRendering" in text or "surfaceUpdate" in text:
                        try:
                            clean_text = text.replace("<a2a_datapart_json>", "").replace("</a2a_datapart_json>", "").strip()
                            if clean_text.startswith("```json"):
                                clean_text = clean_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                            a2ui_data = json.loads(clean_text)
                            parts.append({"kind": "a2ui", "data": a2ui_data})
                        except Exception:
                            parts.append({"kind": "text", "text": text})
                    else:
                        parts.append({"kind": "text", "text": text})

    if not parts:
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]

    return JSONResponse({"parts": parts})


# Mount static directory for frontend web UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"\n🚀 ReleaseOps AI Web Interface running at http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
