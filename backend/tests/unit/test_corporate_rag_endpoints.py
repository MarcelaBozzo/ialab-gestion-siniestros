from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app import main
from app.schemas import (
    CorporateKnowledgeSearchRequest,
    CorporateSourceType,
    SecureCorporateSearchRequest,
)


@pytest.mark.asyncio
async def test_corporate_search_endpoint_forwards_document_type(monkeypatch):
    search = AsyncMock(return_value=[])
    monkeypatch.setattr(main, "search_corporate_knowledge", search)
    request = CorporateKnowledgeSearchRequest(
        query="colisión",
        product_code="AUTO_STANDARD",
        coverage_cd="COLLISION",
        document_type=CorporateSourceType.POLICY_CONDITIONS,
        limit=3,
    )

    result = await main.search_corporate_knowledge_endpoint(request)

    assert result == []
    search.assert_awaited_once_with(
        query="colisión",
        product_code="AUTO_STANDARD",
        coverage_cd="COLLISION",
        document_type=CorporateSourceType.POLICY_CONDITIONS,
        limit=3,
    )


@pytest.mark.asyncio
async def test_secure_search_endpoint_forwards_document_type(monkeypatch):
    search = AsyncMock(return_value=[])
    monkeypatch.setattr(main, "secure_search_corporate_knowledge", search)
    request = SecureCorporateSearchRequest(
        query="condiciones generales",
        document_type=CorporateSourceType.GENERAL_CONDITIONS,
    )

    result = await main.secure_corporate_search_endpoint(request)

    assert result == []
    search.assert_awaited_once_with(
        query="condiciones generales",
        product_code=None,
        coverage_cd=None,
        document_type=CorporateSourceType.GENERAL_CONDITIONS,
    )


@pytest.mark.parametrize(
    (
        "dependency_name",
        "endpoint_name",
        "request_model",
        "expected_detail",
    ),
    [
        (
            "search_corporate_knowledge",
            "search_corporate_knowledge_endpoint",
            CorporateKnowledgeSearchRequest(query="colisión"),
            "Corporate retrieval is unavailable",
        ),
        (
            "secure_search_corporate_knowledge",
            "secure_corporate_search_endpoint",
            SecureCorporateSearchRequest(query="colisión"),
            "Secure corporate retrieval is unavailable",
        ),
    ],
)
@pytest.mark.asyncio
async def test_corporate_endpoints_expose_dependency_unavailability_as_503(
    monkeypatch,
    dependency_name,
    endpoint_name,
    request_model,
    expected_detail,
):
    monkeypatch.setattr(
        main,
        dependency_name,
        AsyncMock(side_effect=RuntimeError("rag unavailable")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await getattr(main, endpoint_name)(request_model)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == expected_detail
