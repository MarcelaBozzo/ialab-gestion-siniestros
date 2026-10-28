import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import CLAIMS_STORAGE_PATH, MAX_DOCUMENT_SIZE_MB
from app.schemas import ClaimDocument, DocumentType


ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}

CLAIM_NUMBER_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
DOCUMENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def validate_claim_number(claim_number: str) -> None:
    if not CLAIM_NUMBER_PATTERN.fullmatch(claim_number):
        raise ValueError("Invalid ClaimNumber")


def validate_document_id(document_id: str) -> None:
    if not DOCUMENT_ID_PATTERN.fullmatch(document_id):
        raise ValueError("Invalid document_id")


def get_claim_documents_path(claim_number: str) -> Path:
    validate_claim_number(claim_number)
    return CLAIMS_STORAGE_PATH / claim_number / "documents"


async def save_claim_document(
    claim_number: str,
    document_type: DocumentType,
    file: UploadFile,
) -> ClaimDocument:
    validate_claim_number(claim_number)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("Unsupported document type")

    content = await file.read()
    max_size = MAX_DOCUMENT_SIZE_MB * 1024 * 1024

    if len(content) > max_size:
        raise ValueError("Document exceeds maximum allowed size")

    document_id = str(uuid4())
    suffix = {
        "application/pdf": ".pdf",
        "image/jpeg": ".jpg",
        "image/png": ".png",
    }[file.content_type]

    documents_path = get_claim_documents_path(claim_number)
    documents_path.mkdir(parents=True, exist_ok=True)

    document_path = documents_path / f"{document_id}{suffix}"
    document_path.write_bytes(content)

    metadata = ClaimDocument(
        document_id=document_id,
        claim_number=claim_number,
        document_type=document_type,
        original_filename=file.filename or "unnamed",
        content_type=file.content_type,
        size_bytes=len(content),
        created_at=datetime.now(timezone.utc),
    )

    metadata_path = documents_path / f"{document_id}.metadata.json"
    metadata_path.write_text(
        metadata.model_dump_json(indent=2),
        encoding="utf-8",
    )

    return metadata


def list_claim_documents(claim_number: str) -> list[ClaimDocument]:
    documents_path = get_claim_documents_path(claim_number)

    if not documents_path.exists():
        return []

    documents: list[ClaimDocument] = []

    for metadata_path in documents_path.glob("*.metadata.json"):
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        documents.append(ClaimDocument.model_validate(data))

    return documents


def get_claim_document(
    claim_number: str,
    document_id: str,
) -> ClaimDocument | None:
    validate_document_id(document_id)
    documents = list_claim_documents(claim_number)
    return next(
        (
            document
            for document in documents
            if document.document_id == document_id
        ),
        None,
    )


def get_document_path(
    claim_number: str,
    document_id: str,
) -> Path | None:
    validate_document_id(document_id)

    document = get_claim_document(
        claim_number=claim_number,
        document_id=document_id,
    )

    if document is None:
        return None

    document_path = (
        get_claim_documents_path(claim_number)
        / document.stored_filename
    )

    if not document_path.is_file():
        return None

    return document_path


def delete_claim_document(
    claim_number: str,
    document_id: str,
) -> bool:
    validate_document_id(document_id)
    documents_path = get_claim_documents_path(claim_number)

    if not documents_path.exists():
        return False

    matches = list(documents_path.glob(f"{document_id}*"))

    if not matches:
        return False

    for path in matches:
        if path.is_file():
            path.unlink()

    return True
