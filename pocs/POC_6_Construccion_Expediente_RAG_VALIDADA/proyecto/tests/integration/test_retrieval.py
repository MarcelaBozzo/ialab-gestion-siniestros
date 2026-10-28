import uuid

import pytest

from app.config import QDRANT_CLAIM_COLLECTION
from app.retrieval import search_claim_documents
from app.schemas import DocumentChunk, DocumentType
from app.vector_store import (
    delete_document_chunks,
    index_document_chunks,
    qdrant_client,
)


@pytest.mark.asyncio
async def test_search_claim_documents_isolated_by_claim():
    document_a = "TEST-A-" + str(uuid.uuid4())
    document_b = "TEST-B-" + str(uuid.uuid4())

    chunks = [
        DocumentChunk(
            claim_number="CLM-TEST-A",
            document_id=document_a,
            document_type=DocumentType.CLAIM_REPORT,
            page=1,
            chunk_index=0,
            content=(
                "El accidente ocurrió "
                "en Avenida Providencia, Santiago."
            ),
        ),
        DocumentChunk(
            claim_number="CLM-TEST-B",
            document_id=document_b,
            document_type=DocumentType.CLAIM_REPORT,
            page=1,
            chunk_index=0,
            content=(
                "El accidente ocurrió "
                "en Avenida Providencia, Santiago."
            ),
        ),
    ]

    try:
        await index_document_chunks(chunks)

        results = await search_claim_documents(
            claim_number="CLM-TEST-A",
            query="¿Dónde ocurrió el accidente?",
            limit=5,
        )

        assert len(results) > 0
        assert all(
            result.claim_number == "CLM-TEST-A"
            for result in results
        )
    finally:
        if await qdrant_client.collection_exists(
            QDRANT_CLAIM_COLLECTION
        ):
            await delete_document_chunks(document_a)
            await delete_document_chunks(document_b)
