import logging

from app.corporate_knowledge import search_corporate_knowledge
from app.guardrails import classify_content
from app.retrieval import search_claim_documents
from app.schemas import (
    ContentClassification,
    CorporateKnowledgeChunk,
    DocumentChunk,
    EvidenceReference,
    EvidenceType,
)


logger = logging.getLogger(__name__)


async def secure_search_claim_documents(
    claim_number: str,
    query: str,
    limit: int = 5,
) -> list[DocumentChunk]:
    chunks = await search_claim_documents(
        claim_number=claim_number,
        query=query,
        limit=limit,
    )
    return await filter_safe_chunks(
        chunks,
        claim_number=claim_number,
    )


async def secure_search_corporate_knowledge(
    query: str,
    product_code: str | None = None,
    coverage_cd: str | None = None,
    limit: int = 5,
) -> list[CorporateKnowledgeChunk]:
    chunks = await search_corporate_knowledge(
        query=query,
        product_code=product_code,
        coverage_cd=coverage_cd,
        limit=limit,
    )
    return await filter_safe_chunks(chunks)


async def filter_safe_chunks(chunks, claim_number=None):
    safe_chunks = []
    for chunk in chunks:
        decision = await classify_content(chunk.content)
        if decision.classification == ContentClassification.SAFE:
            safe_chunks.append(chunk)
        else:
            log_content_blocked(
                chunk,
                claim_number,
                decision.reason,
            )
    return safe_chunks


def log_content_blocked(
    chunk: DocumentChunk | CorporateKnowledgeChunk,
    claim_number: str | None,
    reason: str,
) -> None:
    event = {
        "event": "CONTENT_BLOCKED",
        "claim_number": claim_number,
        "document_id": getattr(chunk, "document_id", None),
        "page": getattr(chunk, "page", None),
        "chunk_index": getattr(chunk, "chunk_index", None),
        "reason": reason,
    }
    try:
        logger.warning(
            "CONTENT_BLOCKED",
            extra={"security_event": event},
        )
    except Exception:
        return


def evidence_from_claim_chunk(
    chunk: DocumentChunk,
) -> EvidenceReference:
    return EvidenceReference(
        evidence_type=EvidenceType.CLAIM_DOCUMENT,
        document_id=chunk.document_id,
        document_type=str(chunk.document_type.value),
        page=chunk.page,
        section=chunk.section,
        chunk_index=chunk.chunk_index,
        claim_number=chunk.claim_number,
        content=chunk.content,
    )


def evidence_from_corporate_chunk(
    chunk: CorporateKnowledgeChunk,
) -> EvidenceReference:
    return EvidenceReference(
        evidence_type=EvidenceType.CORPORATE_DOCUMENT,
        document_id=chunk.document_id,
        document_type=chunk.document_type,
        page=chunk.page,
        section=chunk.section,
        chunk_index=chunk.chunk_index,
        product_code=chunk.product_code,
        coverage_cd=chunk.coverage_cd,
        content=chunk.content,
    )


def build_grounded_context(
    query: str,
    chunks: list[DocumentChunk],
) -> str:
    evidence = "\n\n".join(
        (
            f"document_id={chunk.document_id}\n"
            f"page={chunk.page}\n"
            f"section={chunk.section}\n"
            f"content={chunk.content}"
        )
        for chunk in chunks
    )
    return (
        "Answer the user query using only the evidence below.\n"
        "If the evidence is insufficient, say so explicitly.\n"
        f"USER QUERY\n{query}\n\n"
        "<untrusted_claim_evidence>\n"
        f"{evidence}\n"
        "</untrusted_claim_evidence>"
    )
