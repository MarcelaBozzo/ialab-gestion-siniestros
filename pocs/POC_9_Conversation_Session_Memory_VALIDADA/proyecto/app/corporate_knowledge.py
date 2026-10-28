import re
import uuid
from pathlib import Path

from qdrant_client import AsyncQdrantClient, models

from app.chunking import chunk_text
from app.config import QDRANT_CORPORATE_COLLECTION, QDRANT_URL
from app.document_processing import process_pdf
from app.embeddings import create_document_embedding, create_query_embedding
from app.schemas import CorporateKnowledgeChunk


CONDITIONS_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "corporate"
    / "conditions"
)

qdrant_client = AsyncQdrantClient(url=QDRANT_URL)


COVERAGE_TERMS = {
    "COLLISION": ("COLLISION", "colisión", "colision"),
    "GLASS": ("GLASS", "cristales", "parabrisas", "luneta"),
    "THEFT": ("THEFT", "robo", "hurto"),
    "LIABILITY": (
        "LIABILITY",
        "responsabilidad civil",
        "daños a terceros",
    ),
}


def get_document_metadata(path: Path) -> tuple[str, str | None]:
    tokens = path.stem.upper().split("_")

    if "PROCEDIMIENTO" in tokens:
        return "CLAIMS_PROCEDURE", None

    if "MATRIZ" in tokens and "COBERTURAS" in tokens:
        return "COVERAGE_MATRIX", None

    if "CONDICIONES" in tokens and "GENERALES" in tokens:
        return "GENERAL_CONDITIONS", None

    if len(tokens) >= 2 and len(tokens[-1]) == 4 and tokens[-1].isdigit():
        product_code = "_".join(tokens[:-1])
        return "POLICY_CONDITIONS", product_code

    return "CORPORATE_KNOWLEDGE", None


def resolve_coverage_cd(text: str) -> str | None:
    matches = {
        coverage_cd
        for coverage_cd, terms in COVERAGE_TERMS.items()
        if any(
            re.search(
                rf"(?<!\w){re.escape(term)}(?!\w)",
                text,
                flags=re.IGNORECASE,
            )
            for term in terms
        )
    }
    return next(iter(matches)) if len(matches) == 1 else None


def create_document_chunks(path: Path) -> list[CorporateKnowledgeChunk]:
    document_id = path.stem
    document_type, product_code = get_document_metadata(path)
    pages = process_pdf(path)
    chunks: list[CorporateKnowledgeChunk] = []
    chunk_index = 0

    for page_number, page_text in enumerate(pages, start=1):
        for content in chunk_text(page_text):
            coverage_cd = resolve_coverage_cd(content)
            chunks.append(
                CorporateKnowledgeChunk(
                    document_id=document_id,
                    document_type=document_type,
                    product_code=product_code,
                    coverage_cd=coverage_cd,
                    section=None,
                    page=page_number,
                    chunk_index=chunk_index,
                    content=content,
                )
            )
            chunk_index += 1

    return chunks


def create_point_id(chunk: CorporateKnowledgeChunk) -> str:
    key = f"{chunk.document_id}:{chunk.page}:{chunk.chunk_index}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


async def ensure_corporate_collection(vector_size: int) -> None:
    exists = await qdrant_client.collection_exists(
        collection_name=QDRANT_CORPORATE_COLLECTION
    )
    if exists:
        return

    await qdrant_client.create_collection(
        collection_name=QDRANT_CORPORATE_COLLECTION,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE,
        ),
    )


async def delete_document_chunks(document_id: str) -> None:
    if not await qdrant_client.collection_exists(
        collection_name=QDRANT_CORPORATE_COLLECTION
    ):
        return

    await qdrant_client.delete(
        collection_name=QDRANT_CORPORATE_COLLECTION,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id),
                    )
                ]
            )
        ),
        wait=True,
    )


async def replace_document_chunks(
    chunks: list[CorporateKnowledgeChunk],
) -> int:
    if not chunks:
        return 0

    vectors = [
        await create_document_embedding(chunk.content)
        for chunk in chunks
    ]
    await ensure_corporate_collection(len(vectors[0]))
    await delete_document_chunks(chunks[0].document_id)

    points = [
        models.PointStruct(
            id=create_point_id(chunk),
            vector=vector,
            payload=chunk.model_dump(mode="json"),
        )
        for chunk, vector in zip(chunks, vectors)
    ]
    await qdrant_client.upsert(
        collection_name=QDRANT_CORPORATE_COLLECTION,
        points=points,
        wait=True,
    )
    return len(points)


async def index_corporate_documents() -> dict[str, int | str]:
    if not CONDITIONS_DIR.is_dir():
        raise FileNotFoundError(
            f"Conditions directory does not exist: {CONDITIONS_DIR}"
        )

    pdf_paths = sorted(
        path for path in CONDITIONS_DIR.glob("*.pdf")
        if path.is_file()
    )
    indexed_documents = 0
    indexed_chunks = 0
    skipped_documents = 0

    for path in pdf_paths:
        chunks = create_document_chunks(path)
        if not chunks:
            await delete_document_chunks(path.stem)
            skipped_documents += 1
            continue

        indexed_chunks += await replace_document_chunks(chunks)
        indexed_documents += 1

    return {
        "collection": QDRANT_CORPORATE_COLLECTION,
        "indexed_documents": indexed_documents,
        "indexed_chunks": indexed_chunks,
        "skipped_documents": skipped_documents,
    }


async def search_corporate_knowledge(
    query: str,
    product_code: str | None = None,
    coverage_cd: str | None = None,
    limit: int = 5,
) -> list[CorporateKnowledgeChunk]:
    if not query.strip():
        raise ValueError("query must not be empty")
    if limit <= 0:
        raise ValueError("limit must be positive")

    exists = await qdrant_client.collection_exists(
        collection_name=QDRANT_CORPORATE_COLLECTION
    )
    if not exists:
        return []

    query_vector = await create_query_embedding(query)
    conditions: list[models.FieldCondition] = []

    if product_code is not None:
        conditions.append(
            models.FieldCondition(
                key="product_code",
                match=models.MatchValue(value=product_code),
            )
        )

    if coverage_cd is not None:
        conditions.append(
            models.FieldCondition(
                key="coverage_cd",
                match=models.MatchValue(value=coverage_cd),
            )
        )

    query_filter = models.Filter(must=conditions) if conditions else None

    result = await qdrant_client.query_points(
        collection_name=QDRANT_CORPORATE_COLLECTION,
        query=query_vector,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    )

    chunks: list[CorporateKnowledgeChunk] = []
    for point in result.points:
        if point.payload is None:
            continue
        chunks.append(CorporateKnowledgeChunk.model_validate(point.payload))

    return chunks
