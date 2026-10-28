import os
from pathlib import Path


LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "qwen2.5-instruct:7b",
)

EXTRACTION_MODEL = os.getenv(
    "EXTRACTION_MODEL",
    "qwen2.5-extraction:1.5b",
)

LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "http://localhost:11434/v1",
)

LLM_API_KEY = os.getenv(
    "LLM_API_KEY",
    "local-dev",
)

CLAIMS_STORAGE_PATH = Path(
    os.getenv(
        "CLAIMS_STORAGE_PATH",
        "./data/claims",
    )
)

MAX_DOCUMENT_SIZE_MB = int(
    os.getenv(
        "MAX_DOCUMENT_SIZE_MB",
        "10",
    )
)

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333",
)

QDRANT_CLAIM_COLLECTION = os.getenv(
    "QDRANT_CLAIM_COLLECTION",
    "claim-documents-embeddinggemma",
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "embeddinggemma",
)

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
)

CHUNK_SIZE = int(
    os.getenv(
        "CHUNK_SIZE",
        "1000",
    )
)

CHUNK_OVERLAP = int(
    os.getenv(
        "CHUNK_OVERLAP",
        "150",
    )
)

POLICY_CORE_BASE_URL = os.getenv(
    "POLICY_CORE_BASE_URL",
    "http://localhost:8001",
)

QDRANT_CORPORATE_COLLECTION = os.getenv(
    "QDRANT_CORPORATE_COLLECTION",
    "corporate-knowledge",
)
