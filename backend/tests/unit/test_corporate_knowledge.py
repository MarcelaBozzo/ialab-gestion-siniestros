from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app import corporate_knowledge
from app.schemas import CorporateSourceType


CORPORATE_PAYLOAD = {
    "document_id": "AUTO_STANDARD_2026",
    "document_type": "POLICY_CONDITIONS",
    "product_code": "AUTO_STANDARD",
    "coverage_cd": "COLLISION",
    "section": "Cobertura de colisión",
    "page": 4,
    "chunk_index": 2,
    "content": "Daños por colisión sujetos a las condiciones indicadas.",
}


def configure_qdrant(monkeypatch, *, exists=True, points=None):
    client = SimpleNamespace(
        collection_exists=AsyncMock(return_value=exists),
        query_points=AsyncMock(
            return_value=SimpleNamespace(points=points or [])
        ),
    )
    monkeypatch.setattr(corporate_knowledge, "qdrant_client", client)
    return client


@pytest.mark.asyncio
async def test_search_applies_all_filters_without_cross_product_fallback(
    monkeypatch,
):
    point = SimpleNamespace(payload=CORPORATE_PAYLOAD)
    client = configure_qdrant(monkeypatch, points=[point])
    monkeypatch.setattr(
        corporate_knowledge,
        "create_query_embedding",
        AsyncMock(return_value=[0.1, 0.2]),
    )

    result = await corporate_knowledge.search_corporate_knowledge(
        query="colisión",
        product_code="AUTO_STANDARD",
        coverage_cd="COLLISION",
        document_type=CorporateSourceType.POLICY_CONDITIONS,
        limit=3,
    )

    query_filter = client.query_points.await_args.kwargs["query_filter"]
    filters = {
        condition.key: condition.match.value
        for condition in query_filter.must
    }
    assert filters == {
        "product_code": "AUTO_STANDARD",
        "coverage_cd": "COLLISION",
        "document_type": "POLICY_CONDITIONS",
    }
    assert result[0].document_id == "AUTO_STANDARD_2026"
    assert result[0].page == 4
    assert result[0].chunk_index == 2


@pytest.mark.asyncio
async def test_search_without_matches_is_valid_empty_result(monkeypatch):
    configure_qdrant(monkeypatch, points=[])
    monkeypatch.setattr(
        corporate_knowledge,
        "create_query_embedding",
        AsyncMock(return_value=[0.1]),
    )

    result = await corporate_knowledge.search_corporate_knowledge(
        query="sin coincidencias",
    )

    assert result == []


@pytest.mark.asyncio
async def test_search_fails_when_collection_is_not_initialized(monkeypatch):
    configure_qdrant(monkeypatch, exists=False)
    embedding = AsyncMock(return_value=[0.1])
    monkeypatch.setattr(
        corporate_knowledge,
        "create_query_embedding",
        embedding,
    )

    with pytest.raises(
        RuntimeError,
        match="Corporate knowledge collection is not initialized",
    ):
        await corporate_knowledge.search_corporate_knowledge(query="colisión")

    embedding.assert_not_awaited()


@pytest.mark.asyncio
async def test_search_propagates_embedding_unavailability(monkeypatch):
    configure_qdrant(monkeypatch)
    unavailable = RuntimeError("embedding unavailable")
    monkeypatch.setattr(
        corporate_knowledge,
        "create_query_embedding",
        AsyncMock(side_effect=unavailable),
    )

    with pytest.raises(RuntimeError, match="embedding unavailable"):
        await corporate_knowledge.search_corporate_knowledge(query="colisión")


@pytest.mark.parametrize(
    ("filename", "expected_type", "expected_product"),
    [
        (
            "AUTO_STANDARD_2026.pdf",
            "POLICY_CONDITIONS",
            "AUTO_STANDARD",
        ),
        (
            "CONDICIONES_GENERALES_AUTO.pdf",
            "GENERAL_CONDITIONS",
            None,
        ),
        (
            "PROCEDIMIENTO_SINIESTROS_AUTO_2026.pdf",
            "CLAIMS_PROCEDURE",
            None,
        ),
    ],
)
def test_document_metadata_distinguishes_source_types(
    filename,
    expected_type,
    expected_product,
):
    document_type, product_code = corporate_knowledge.get_document_metadata(
        corporate_knowledge.Path(filename)
    )

    assert document_type == expected_type
    assert product_code == expected_product
