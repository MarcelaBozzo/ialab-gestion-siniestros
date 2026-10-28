import os


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
