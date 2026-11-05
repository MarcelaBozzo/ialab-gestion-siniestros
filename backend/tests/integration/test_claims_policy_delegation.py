from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.utils import TransportProtocol

from app import coverage_service
from app.a2a import policy_server
from app.agents import claims_agent
from app.schemas import (
    ClaimData,
    ClaimsOccurrence,
    CoverageAnalysis,
    CoverageAssessment,
    VehInfo,
)


@pytest.mark.asyncio
async def test_claims_tool_delegates_minimal_contract_to_a2a_client(
    monkeypatch,
):
    expected = CoverageAnalysis(
        claim_number="CLM-000123",
        policy_number="POL-123456",
        assessment=CoverageAssessment.REQUIRES_REVIEW,
        rationale="Propuesta especializada sujeta a revisión humana.",
        confidence=0.6,
    )
    a2a_call = AsyncMock(return_value=expected)
    monkeypatch.setattr(
        coverage_service.policy_a2a_client,
        "analyze_coverage",
        a2a_call,
    )
    dependencies = claims_agent.ClaimsAgentDependencies(
        claim_number="CLM-000123",
        claim_data=ClaimData(
            claim_number="CLM-000123",
            policy_number="POL-123456",
            claims_occurrence=ClaimsOccurrence(
                loss_desc="Colisión frontal.",
            ),
            veh_info=VehInfo(vehicle_plate="ABCD12"),
        ),
        relevant_document_evidence=[],
    )

    result = await claims_agent.analyze_coverage(
        SimpleNamespace(deps=dependencies)
    )

    assert result == expected
    request = a2a_call.await_args.args[0]
    assert request.model_dump(mode="json") == {
        "claim_number": "CLM-000123",
        "policy_number": "POL-123456",
        "claims_occurrence": {
            "loss_dt": None,
            "loss_time": None,
            "loss_cause_cd": None,
            "loss_cause_desc": None,
            "loss_desc": "Colisión frontal.",
            "loss_location_desc": None,
        },
        "veh_info": {
            "veh_identification_number": None,
            "vehicle_plate": "ABCD12",
            "manufacturer": None,
            "model": None,
            "model_year": None,
        },
        "relevant_document_evidence": [],
    }
    assert "session_id" not in request.model_dump()
    assert "summary" not in request.model_dump()
    assert "messages" not in request.model_dump()


@pytest.mark.asyncio
async def test_claims_tool_crosses_a2a_boundary_with_structured_contract(
    monkeypatch,
):
    expected = CoverageAnalysis(
        claim_number="CLM-000123",
        policy_number="POL-123456",
        assessment=CoverageAssessment.REQUIRES_REVIEW,
        rationale="Análisis remoto sujeto a revisión humana.",
        confidence=0.5,
    )
    remote_service = AsyncMock(return_value=expected)
    monkeypatch.setattr(
        policy_server,
        "analyze_policy_coverage",
        remote_service,
    )
    dependencies = claims_agent.ClaimsAgentDependencies(
        claim_number="CLM-000123",
        claim_data=ClaimData(
            claim_number="CLM-000123",
            policy_number="POL-123456",
            claims_occurrence=ClaimsOccurrence(
                loss_desc="Colisión frontal.",
            ),
            veh_info=VehInfo(vehicle_plate="ABCD12"),
        ),
        relevant_document_evidence=[],
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=policy_server.app),
        base_url="http://testserver",
    ) as http_client:
        resolver = A2ACardResolver(
            httpx_client=http_client,
            base_url="http://testserver",
        )
        card = await resolver.get_agent_card()
        card.supported_interfaces[0].url = (
            "http://testserver/a2a/jsonrpc"
        )
        sdk_client = await create_client(
            card,
            client_config=ClientConfig(
                httpx_client=http_client,
                supported_protocol_bindings=[TransportProtocol.JSONRPC],
                streaming=False,
            ),
        )
        monkeypatch.setattr(
            coverage_service.policy_a2a_client,
            "_client",
            sdk_client,
        )
        try:
            result = await claims_agent.analyze_coverage(
                SimpleNamespace(deps=dependencies)
            )
        finally:
            await sdk_client.close()

    assert result == expected
    remote_service.assert_awaited_once()
    remote_request = remote_service.await_args.args[0]
    assert remote_request.claim_number == "CLM-000123"
    assert remote_request.policy_number == "POL-123456"
    assert "session_id" not in remote_request.model_dump()
    assert "messages" not in remote_request.model_dump()
