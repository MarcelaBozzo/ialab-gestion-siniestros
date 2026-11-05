from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app import health, main
from app.a2a.errors import A2AAgentUnavailable


@pytest.mark.asyncio
async def test_claims_api_lifespan_starts_and_closes_a2a_client(monkeypatch):
    start = AsyncMock()
    close = AsyncMock()
    monkeypatch.setattr(main.policy_a2a_client, "start", start)
    monkeypatch.setattr(main.policy_a2a_client, "close", close)

    async with main.lifespan(main.app):
        start.assert_awaited_once()
        close.assert_not_awaited()

    close.assert_awaited_once()


@pytest.mark.asyncio
async def test_claims_api_remains_available_when_a2a_discovery_fails(
    monkeypatch,
):
    start = AsyncMock(side_effect=A2AAgentUnavailable("offline"))
    close = AsyncMock()
    monkeypatch.setattr(main.policy_a2a_client, "start", start)
    monkeypatch.setattr(main.policy_a2a_client, "close", close)

    async with main.lifespan(main.app):
        pass

    start.assert_awaited_once()
    close.assert_awaited_once()


@pytest.mark.asyncio
async def test_policy_agent_health_discovers_required_skill(monkeypatch):
    resolver = SimpleNamespace(
        get_agent_card=AsyncMock(
            return_value=SimpleNamespace(
                skills=[SimpleNamespace(id="analyze_coverage")]
            )
        )
    )
    monkeypatch.setattr(health, "A2ACardResolver", lambda **_: resolver)

    result = await health.policy_agent_health()

    assert result.status == "ok"
    assert result.agent == "policy-agent"
    assert result.skills == ["analyze_coverage"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("card", "detail"),
    [
        (None, "Policy Agent is unavailable"),
        (
            SimpleNamespace(skills=[SimpleNamespace(id="other")]),
            "Policy Agent does not publish analyze_coverage",
        ),
    ],
)
async def test_policy_agent_health_reports_unavailable_or_unhealthy(
    monkeypatch,
    card,
    detail,
):
    get_card = (
        AsyncMock(side_effect=RuntimeError("offline"))
        if card is None
        else AsyncMock(return_value=card)
    )
    resolver = SimpleNamespace(get_agent_card=get_card)
    monkeypatch.setattr(health, "A2ACardResolver", lambda **_: resolver)

    with pytest.raises(HTTPException) as exc_info:
        await health.policy_agent_health()

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == detail


def test_openapi_publishes_poc13_health_and_contracts():
    main.app.openapi_schema = None

    schema = main.custom_openapi()

    assert "/health/policy-agent" in schema["paths"]
    published = schema["components"]["schemas"]
    assert {
        "CoverageAnalysisRequest",
        "CoverageAnalysis",
        "CoverageEvidence",
        "CoverageAssessment",
        "PolicyValidationResult",
        "CorporateSourceType",
        "PolicyAgentHealthResponse",
    } <= published.keys()
