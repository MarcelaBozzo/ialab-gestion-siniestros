import uuid

import pytest

from app.config import QDRANT_CLAIM_COLLECTION
from app.schemas import DocumentChunk, DocumentType
from app.vector_store import (
    delete_document_chunks,
    index_document_chunks,
    qdrant_client,
)


@pytest.mark.asyncio
async def test_index_document_chunks():
    document_id = "TEST-" + str(uuid.uuid4())

    chunks = [
        DocumentChunk(
            claim_number="CLM-TEST-001",
            document_id=document_id,
            document_type=DocumentType.CLAIM_REPORT,
            page=1,
            chunk_index=0,
            content=(
                "El accidente ocurrió "
                "en Avenida Providencia."
            ),
        )
    ]

    try:
        await index_document_chunks(chunks)

        exists = await qdrant_client.collection_exists(
            QDRANT_CLAIM_COLLECTION
        )

        assert exists is True
    finally:
        if await qdrant_client.collection_exists(
            QDRANT_CLAIM_COLLECTION
        ):
            await delete_document_chunks(document_id)
