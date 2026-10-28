import pytest

from app.embeddings import (
    create_document_embedding,
    create_query_embedding,
)


@pytest.mark.asyncio
async def test_embeddinggemma_document_and_query():
    document_embedding = await create_document_embedding(
        "El accidente ocurrió en Avenida Providencia."
    )
    query_embedding = await create_query_embedding(
        "¿Dónde ocurrió el accidente?"
    )

    assert len(document_embedding) > 0
    assert len(query_embedding) > 0
    assert len(document_embedding) == len(query_embedding)
    assert all(
        isinstance(value, float)
        for value in document_embedding
    )
