import uuid

from qdrant_client import AsyncQdrantClient, models

from app.config import QDRANT_CLAIM_COLLECTION, QDRANT_URL
from app.embeddings import create_document_embedding
from app.schemas import DocumentChunk


qdrant_client = AsyncQdrantClient(url=QDRANT_URL)


async def ensure_claim_collection(vector_size: int) -> None:
    exists = await qdrant_client.collection_exists(
        QDRANT_CLAIM_COLLECTION
    )

    if exists:
        return

    await qdrant_client.create_collection(
        collection_name=QDRANT_CLAIM_COLLECTION,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE,
        ),
    )


def create_chunk_point_id(
    document_id: str,
    chunk_index: int,
) -> str:
    value = f"{document_id}:{chunk_index}"
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            value,
        )
    )


async def delete_document_chunks(document_id: str) -> None:
    await qdrant_client.delete(
        collection_name=QDRANT_CLAIM_COLLECTION,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(
                            value=document_id
                        ),
                    )
                ]
            )
        ),
    )


async def index_document_chunks(
    chunks: list[DocumentChunk],
) -> None:
    if not chunks:
        return

    first_embedding = await create_document_embedding(
        chunks[0].content
    )

    await ensure_claim_collection(len(first_embedding))

    points: list[models.PointStruct] = []
    first_chunk = chunks[0]

    points.append(
        models.PointStruct(
            id=create_chunk_point_id(
                first_chunk.document_id,
                first_chunk.chunk_index,
            ),
            vector=first_embedding,
            payload=first_chunk.model_dump(mode="json"),
        )
    )

    for chunk in chunks[1:]:
        embedding = await create_document_embedding(
            chunk.content
        )
        points.append(
            models.PointStruct(
                id=create_chunk_point_id(
                    chunk.document_id,
                    chunk.chunk_index,
                ),
                vector=embedding,
                payload=chunk.model_dump(mode="json"),
            )
        )

    await qdrant_client.upsert(
        collection_name=QDRANT_CLAIM_COLLECTION,
        points=points,
        wait=True,
    )


async def replace_document_chunks(
    chunks: list[DocumentChunk],
) -> None:
    if not chunks:
        return

    document_id = chunks[0].document_id

    if await qdrant_client.collection_exists(
        QDRANT_CLAIM_COLLECTION
    ):
        await delete_document_chunks(document_id)

    await index_document_chunks(chunks)
