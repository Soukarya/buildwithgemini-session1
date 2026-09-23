"""Script to provision or list a Vertex AI Memory Bank (Agent Engine) instance."""

import os
import vertexai

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-6a55309796e4")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")


def get_or_create_memory_bank():
    print(f"Initializing Vertex AI Client for project={PROJECT_ID}, location={LOCATION}")
    client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

    try:
        engines = list(client.agent_engines.list())
        if engines:
            engine_name = engines[0].api_resource.name
            engine_id = engine_name.split("/")[-1]
            print(f"Using existing Memory Bank instance: {engine_name}")
            print(f"MEMORY_BANK_ID: {engine_id}")
            return engine_id
    except Exception as e:
        print(f"Notice listing agent_engines: {e}")

    print("Creating new Memory Bank instance (Agent Engine)...")
    engine = client.agent_engines.create()
    engine_name = engine.api_resource.name
    engine_id = engine_name.split("/")[-1]
    print(f"Created Memory Bank instance: {engine_name}")
    print(f"MEMORY_BANK_ID: {engine_id}")
    return engine_id


if __name__ == "__main__":
    bank_id = get_or_create_memory_bank()
    # Save memory bank ID to config file
    with open("/config/Desktop/Session1/app/memory_config.py", "w") as f:
        f.write(f'MEMORY_BANK_ID = "{bank_id}"\n')
    print("Saved MEMORY_BANK_ID to app/memory_config.py")
