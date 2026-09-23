"""Script to create a Vertex AI RAG corpus in serverless mode and import DevOps runbooks."""

import os
import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-6a55309796e4")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GCS_PATH = f"gs://{PROJECT_ID}-rag/docs/"

PARSING_PROMPT = (
    "Extract all DevOps procedures, release prerequisites, deployment checklists, "
    "rollback steps, troubleshooting actions, and emergency release policies. "
    "Output clean, structured, self-contained facts and instructions."
)


def create_corpus():
    print(f"Initializing Vertex AI for project={PROJECT_ID}, location={LOCATION}")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # 1. Switch region RAG managed DB to serverless mode
    cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    try:
        rag.update_rag_engine_config(
            rag_engine_config=rag.RagEngineConfig(
                name=cfg,
                rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
            )
        )
        print("Set RAG Engine config to serverless mode.")
    except Exception as e:
        print(f"Serverless config update info/notice: {e}")

    # 2. Create corpus
    print("Creating RAG corpus 'devops-releaseops-runbooks'...")
    corpus = rag.create_corpus(
        display_name="devops-releaseops-runbooks",
        embedding_model_config=rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-005"
        ),
    )
    print(f"Corpus created successfully: {corpus.name}")

    # 3. Import and parse files
    print(f"Importing documents from {GCS_PATH}...")
    try:
        resp = rag.import_files(
            corpus_name=corpus.name,
            paths=[GCS_PATH],
            transformation_config=rag.TransformationConfig(
                chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
            ),
            llm_parser=rag.LlmParserConfig(
                model_name="gemini-2.5-flash",
                custom_parsing_prompt=PARSING_PROMPT,
            ),
        )
        print(f"Import complete! Imported files count: {getattr(resp, 'imported_rag_files_count', 'OK')}")
    except Exception as e:
        print(f"Import with LLM parser notice: {e}, falling back to default parser...")
        resp = rag.import_files(
            corpus_name=corpus.name,
            paths=[GCS_PATH],
            transformation_config=rag.TransformationConfig(
                chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
            ),
        )
        print(f"Import complete! Imported files count: {getattr(resp, 'imported_rag_files_count', 'OK')}")

    # Save corpus name to a config file for tools.py
    os.makedirs("/config/Desktop/Session1/app", exist_ok=True)
    with open("/config/Desktop/Session1/app/rag_config.py", "w") as f:
        f.write(f'CORPUS_NAME = "{corpus.name}"\n')
    print(f"Saved CORPUS_NAME to app/rag_config.py")

    return corpus.name


if __name__ == "__main__":
    create_corpus()
