from app.config import CHUNK_OVERLAP, CHUNK_SIZE
from app.schemas import DocumentChunk, ProcessedDocument


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    if not text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def create_document_chunks(
    document: ProcessedDocument,
) -> list[DocumentChunk]:
    result: list[DocumentChunk] = []
    chunk_index = 0

    for page_number, page_text in enumerate(
        document.pages,
        start=1,
    ):
        page_chunks = chunk_text(page_text)

        for content in page_chunks:
            result.append(
                DocumentChunk(
                    claim_number=document.claim_number,
                    document_id=document.document_id,
                    document_type=document.document_type,
                    page=page_number,
                    chunk_index=chunk_index,
                    content=content,
                )
            )
            chunk_index += 1

    return result
