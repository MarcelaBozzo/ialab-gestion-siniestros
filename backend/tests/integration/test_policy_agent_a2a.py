from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct, Value

from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.types import (
    Message,
    Part,
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    TaskState,
)
from a2a.utils import TransportProtocol

from app.a2a import policy_server
from app.schemas import (
    ClaimsOccurrence,
    CorporateSourceType,
    CoverageAnalysis,
    CoverageAnalysisRequest,
    CoverageAssessment,
    CoverageEvidence,
    VehInfo,
)


def make_request(
    claim_number: str = "CLM-000123",
) -> CoverageAnalysisRequest:
    return CoverageAnalysisRequest(
        claim_number=claim_number,
        policy_number="POL-123456",
        claims_occurrence=ClaimsOccurrence(
            loss_dt="2026-07-02",
            loss_desc="Colisión con otro vehículo.",
        ),
        veh_info=VehInfo(vehicle_plate="ABCD12"),
    )


def analysis_for(request: CoverageAnalysisRequest) -> CoverageAnalysis:
    return CoverageAnalysis(
        claim_number=request.claim_number,
        policy_number=request.policy_number,
        assessment=CoverageAssessment.POTENTIALLY_COVERED,
        rationale="Los hechos son compatibles con la cláusula citada.",
        applicable_coverages=["COLLISION"],
        evidence=[
            CoverageEvidence(
                source_document="AUTO_STANDARD_2026",
                source_type=CorporateSourceType.POLICY_CONDITIONS,
                clause_id="STD-COV-01",
                page=2,
                excerpt="Daños materiales causados por colisión.",
            )
        ],
        confidence=0.8,
    )


def structured_part(payload: dict) -> Part:
    data = Struct()
    json_format.ParseDict(payload, data)
    return Part(data=Value(struct_value=data))


async def create_in_memory_client(http_client):
    resolver = A2ACardResolver(
        httpx_client=http_client,
        base_url="http://testserver",
    )
    card = await resolver.get_agent_card()
    card.supported_interfaces[0].url = "http://testserver/a2a/jsonrpc"
    client = await create_client(
        card,
        client_config=ClientConfig(
            httpx_client=http_client,
            supported_protocol_bindings=[TransportProtocol.JSONRPC],
            streaming=False,
        ),
    )
    return card, client


async def send_request(client, part: Part):
    request = SendMessageRequest(
        message=Message(
            role=Role.ROLE_USER,
            message_id=str(uuid4()),
            parts=[part],
        ),
        configuration=SendMessageConfiguration(
            return_immediately=False,
            accepted_output_modes=["application/json"],
        ),
    )
    return [event async for event in client.send_message(request)]


@pytest.mark.asyncio
async def test_discovery_and_structured_request_response_preserve_provenance(
    monkeypatch,
):
    request = make_request()
    expected = analysis_for(request)
    service = AsyncMock(return_value=expected)
    monkeypatch.setattr(policy_server, "analyze_policy_coverage", service)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=policy_server.app),
        base_url="http://testserver",
    ) as http_client:
        card, client = await create_in_memory_client(http_client)
        try:
            events = await send_request(
                client,
                structured_part(request.model_dump(mode="json")),
            )
        finally:
            await client.close()

    assert [skill.id for skill in card.skills] == ["analyze_coverage"]
    assert len(events) == 1
    task = events[0].task
    assert task.status.state == TaskState.TASK_STATE_COMPLETED
    service.assert_awaited_once()
    service_request = service.await_args.args[0]
    assert isinstance(service_request, CoverageAnalysisRequest)
    assert "session_id" not in service_request.model_dump()
    assert "messages" not in service_request.model_dump()

    artifact = next(
        item for item in task.artifacts
        if item.name == "coverage_analysis"
    )
    payload = json_format.MessageToDict(artifact.parts[0].data)
    result = CoverageAnalysis.model_validate(payload)
    assert result == expected
    assert result.evidence[0].source_document == "AUTO_STANDARD_2026"
    assert result.evidence[0].page == 2


@pytest.mark.asyncio
async def test_invalid_structured_request_finishes_as_failed_task(monkeypatch):
    service = AsyncMock()
    monkeypatch.setattr(policy_server, "analyze_policy_coverage", service)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=policy_server.app),
        base_url="http://testserver",
    ) as http_client:
        _, client = await create_in_memory_client(http_client)
        try:
            events = await send_request(
                client,
                structured_part({"claim_number": ""}),
            )
        finally:
            await client.close()

    assert len(events) == 1
    assert events[0].task.status.state == TaskState.TASK_STATE_FAILED
    assert not events[0].task.artifacts
    service.assert_not_awaited()


@pytest.mark.asyncio
async def test_domain_dependency_failure_is_safe_failed_task(monkeypatch):
    service = AsyncMock(side_effect=RuntimeError("Qdrant secret failure"))
    monkeypatch.setattr(policy_server, "analyze_policy_coverage", service)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=policy_server.app),
        base_url="http://testserver",
    ) as http_client:
        _, client = await create_in_memory_client(http_client)
        try:
            events = await send_request(
                client,
                structured_part(make_request().model_dump(mode="json")),
            )
        finally:
            await client.close()

    assert len(events) == 1
    task = events[0].task
    assert task.status.state == TaskState.TASK_STATE_FAILED
    assert not task.artifacts
    assert task.status.message.parts[0].text == (
        "Coverage analysis could not be completed"
    )
    assert "Qdrant secret failure" not in task.status.message.parts[0].text


@pytest.mark.asyncio
async def test_a2a_tasks_do_not_share_conversation_state(monkeypatch):
    service = AsyncMock(side_effect=analysis_for)
    monkeypatch.setattr(policy_server, "analyze_policy_coverage", service)
    requests = [make_request("CLM-A"), make_request("CLM-B")]

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=policy_server.app),
        base_url="http://testserver",
    ) as http_client:
        _, client = await create_in_memory_client(http_client)
        try:
            event_sets = [
                await send_request(
                    client,
                    structured_part(request.model_dump(mode="json")),
                )
                for request in requests
            ]
        finally:
            await client.close()

    tasks = [events[0].task for events in event_sets]
    assert [task.status.state for task in tasks] == [
        TaskState.TASK_STATE_COMPLETED,
        TaskState.TASK_STATE_COMPLETED,
    ]
    assert tasks[0].id != tasks[1].id
    assert tasks[0].context_id != tasks[1].context_id
    assert [
        call.args[0].claim_number for call in service.await_args_list
    ] == ["CLM-A", "CLM-B"]
