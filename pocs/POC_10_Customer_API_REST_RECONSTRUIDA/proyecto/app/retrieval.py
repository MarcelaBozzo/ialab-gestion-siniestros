from qdrant_client import models

from app.config import QDRANT_CLAIM_COLLECTION
from app.embeddings import create_query_embedding
from app.schemas import DocumentChunk
from app.vector_store import qdrant_client


async def search_claim_documents(
    claim_number: str,
    query: str,
    limit: int = 5,
) -> list[DocumentChunk]:
    exists = await qdrant_client.collection_exists(
        QDRANT_CLAIM_COLLECTION
    )

    if not exists:
        return []

    query_vector = await create_query_embedding(query)

    result = await qdrant_client.query_points(
        collection_name=QDRANT_CLAIM_COLLECTION,
        query=query_vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="claim_number",
                    match=models.MatchValue(
                        value=claim_number
                    ),
                )
            ]
        ),
        limit=limit,
        with_payload=True,
    )

    chunks: list[DocumentChunk] = []

    for point in result.points:
        if point.payload is None:
            continue
        chunks.append(
            DocumentChunk.model_validate(point.payload)
        )

    return chunks
