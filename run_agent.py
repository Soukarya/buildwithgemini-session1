"""Runner script to test the Multi-Agent DevOps Release Assistant with GitHub Actions integration."""

import os
# Ensure Vertex AI environment variables are set before importing google.adk
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-6a55309796e4")
os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

import asyncio
from dotenv import load_dotenv
load_dotenv()

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import VertexAiMemoryBankService, InMemoryMemoryService

from app.agent import root_agent
from app.memory_config import MEMORY_BANK_ID

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-6a55309796e4")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
APP_NAME = "releaseops_github_agent_app"


def create_runner_with_memory():
    session_service = InMemorySessionService()
    try:
        print(f"Connecting to Vertex AI Memory Bank (AgentEngine ID: {MEMORY_BANK_ID})...")
        memory_service = VertexAiMemoryBankService(
            project=PROJECT_ID,
            location=LOCATION,
            agent_engine_id=MEMORY_BANK_ID,
        )
    except Exception as e:
        print(f"Notice connecting to Vertex AI Memory Bank: {e}, falling back to InMemoryMemoryService...")
        memory_service = InMemoryMemoryService()

    return Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )


async def send_message(runner: Runner, user_id: str, session_id: str, prompt: str):
    print(f"\n==========================================")
    print(f"USER PROMPT: {prompt}")
    print(f"==========================================\n")

    user_msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)]
    )

    handling_agent = None
    tools_called = []
    response_text = ""

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_msg):
        if event.author:
            handling_agent = event.author
        if event.content:
            for part in event.content.parts:
                if part.function_call:
                    tools_called.append(part.function_call.name)
                    print(f"🛠️  [{event.author}] TOOL CALL: {part.function_call.name}({part.function_call.args})")
                elif part.text:
                    response_text += part.text + "\n"

    print(f"🤖 RESPONSE (Handled by: {handling_agent}):\n{response_text.strip()}\n")
    return {
        "handling_agent": handling_agent,
        "tools_called": tools_called,
        "response_text": response_text,
    }


async def main():
    print("=== Multi-Agent DevOps Release Assistant (GitHub Actions Test) ===\n")
    runner = create_runner_with_memory()
    user_id = "devops_engineer_charlie"
    session = await runner.session_service.create_session(app_name=APP_NAME, user_id=user_id)

    # --- GitHub Actions Troubleshooting Request ---
    prompt = "Why did GitHub Actions run 35428930729 fail in repository ctssddevopsengineer/wedding-invitation-site?"
    res = await send_message(runner, user_id, session.id, prompt)

    print("\n==========================================")
    print("VERIFICATION SUMMARY:")
    print("==========================================")
    print(f"Handling Agent: {res['handling_agent']}")
    print(f"Tools Called: {res['tools_called']}")
    has_evidence = "EVIDENCE" in res['response_text'].upper()
    has_inference = "INFERENCE" in res['response_text'].upper()
    print(f"Includes EVIDENCE section: {has_evidence}")
    print(f"Includes INFERENCE section: {has_inference}")


if __name__ == "__main__":
    asyncio.run(main())
