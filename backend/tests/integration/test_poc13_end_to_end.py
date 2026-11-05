from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.utils import TransportProtocol

from app import coverage_service, policy_agent_service, policy_client
from app import policy_core, policy_service, secure_rag
from app.a2a import policy_server as a2a_policy_server
from app.agents import claims_agent
from app.mcp import policy_server as policy_mcp_server
from app.schemas import (
    ClaimData,
    ClaimsOccurrence,
    ContentClassification,
    ContentGuardrailDecision,
    CorporateKnowledgeChunk,
    CorporateSourceType,
    CoverageAnalysis,
    CoverageAssessment,
    CoverageEvidence,
    VehInfo,
)


@pytest.mark.asyncio
async def test_full_claims_a2a_policy_mcp_and_secure_rag_flow(monkeypatch):
    policy_core_transport = httpx.ASGITransport(app=policy_core.app)

    async def retrieve_from_policy_core(policy_number):
        return await policy_client.get_policy_from_api(
            policy_number,
            transport=policy_core_transport,
        )

    monkeypatch.setattr(
        policy_mcp_server,
        "get_policy_from_api",
        retrieve_from_policy_core,
    )
    mcp_calls = []

    async def call_in_process_policy_mcp(tool_name, arguments):
        mcp_calls.append((tool_name, arguments))
        result = await policy_mcp_server.mcp.call_tool(tool_name, arguments)
        assert result.is_error is False
        return result.structured_content

    monkeypatch.setattr(
        policy_service,
        "call_policy_mcp_tool",
        call_in_process_policy_mcp,
    )

    clause = (
        "STD-COV-01 Daños materiales causados por colisión requieren "
        "evaluación del analista."
    )
    contractual_chunk = CorporateKnowledgeChunk(
        document_id="AUTO_STANDARD_2026",
        document_type=CorporateSourceType.POLICY_CONDITIONS.value,
        product_code="AUTO_STANDARD",
        coverage_cd="COLLISION",
        page=2,
        chunk_index=1,
        content=clause,
    )
    rag_calls = []

    async def retrieve_corporate(
        query,
        product_code=None,
        coverage_cd=None,
        document_type=None,
        limit=5,
    ):
        rag_calls.append((product_code, coverage_cd, document_type))
        if (
            product_code == "AUTO_STANDARD"
            and coverage_cd == "COLLISION"
            and document_type == "POLICY_CONDITIONS"
        ):
            return [contractual_chunk, contractual_chunk]
        return []

    monkeypatch.setattr(
        secure_rag,
        "search_corporate_knowledge",
        retrieve_corporate,
    )
    monkeypatch.setattr(
        secure_rag,
        "classify_content",
        AsyncMock(
            return_value=ContentGuardrailDecision(
                classification=ContentClassification.SAFE,
                reason="controlled fixture",
            )
        ),
    )
    proposed = CoverageAnalysis(
        claim_number="CLM-000123",
        policy_number="POL-123456",
        assessment=CoverageAssessment.POTENTIALLY_COVERED,
        rationale=(
            "Propuesta basada en evidencia contractual; requiere revisión "
            "y aprobación humana."
        ),
        applicable_coverages=["COLLISION"],
        evidence=[
            CoverageEvidence(
                source_document="AUTO_STANDARD_2026",
                source_type=CorporateSourceType.POLICY_CONDITIONS,
                clause_id="STD-COV-01",
                page=2,
                excerpt=clause,
            )
        ],
        confidence=0.8,
    )
    policy_run = AsyncMock(return_value=SimpleNamespace(output=proposed))
    monkeypatch.setattr(policy_agent_service.policy_agent, "run", policy_run)

    received_requests = []
    real_analyze = policy_agent_service.analyze_policy_coverage

    async def recorded_analysis(request):
        received_requests.append(request)
        return await real_analyze(request)

    monkeypatch.setattr(
        a2a_policy_server,
        "analyze_policy_coverage",
        recorded_analysis,
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=a2a_policy_server.app),
        base_url="http://testserver",
    ) as http_client:
        resolver = A2ACardResolver(
            httpx_client=http_client,
            base_url="http://testserver",
        )
        card = await resolver.get_agent_card()
        card.supported_interfaces[0].url = "http://testserver/a2a/jsonrpc"
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
        dependencies = claims_agent.ClaimsAgentDependencies(
            claim_number="CLM-000123",
            claim_data=ClaimData(
                claim_number="CLM-000123",
                policy_number="POL-123456",
                claims_occurrence=ClaimsOccurrence(
                    loss_dt="2026-07-02",
                    loss_desc="Colisión con otro vehículo.",
                ),
                veh_info=VehInfo(vehicle_plate="ABCD12"),
            ),
            relevant_document_evidence=[],
        )
        try:
            result = await claims_agent.analyze_coverage(
                SimpleNamespace(deps=dependencies)
            )
        finally:
            await sdk_client.close()

    assert result.assessment == CoverageAssessment.POTENTIALLY_COVERED
    assert result.policy_validation.model_dump() == {
        "policy_number_matches": True,
        "vehicle_matches": True,
        "policy_active_on_loss_dt": True,
    }
    assert result.evidence[0].source_document == "AUTO_STANDARD_2026"
    assert mcp_calls == [
        ("get_policy", {"policy_number": "POL-123456"})
    ]
    assert ("AUTO_STANDARD", "COLLISION", "POLICY_CONDITIONS") in rag_calls
    assert all(call[0] in {None, "AUTO_STANDARD"} for call in rag_calls)
    assert len(received_requests) == 1
    request_payload = received_requests[0].model_dump()
    assert not (
        {"session_id", "messages", "summary"} & request_payload.keys()
    )
    prompt = policy_run.await_args.args[0]
    assert "contenido no confiable" in prompt
    assert "No apruebes ni rechaces cobertura" in prompt
    prohibited = " ".join(
        [result.rationale, *result.applicable_coverages]
    ).lower()
    assert "pago autorizado" not in prohibited
    assert "siniestro cerrado" not in prohibited
