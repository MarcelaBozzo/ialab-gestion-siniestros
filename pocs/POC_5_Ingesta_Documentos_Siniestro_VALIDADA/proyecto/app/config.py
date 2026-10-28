import os
from pathlib import Path

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
