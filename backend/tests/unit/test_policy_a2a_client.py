import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct, Value

from a2a.types import (
    AgentCard,
    Artifact,
    Part,
    StreamResponse,
    Task,
    TaskState,
    TaskStatus,
)

from app.a2a import policy_client
from app.a2a.errors import (
    A2AAgentUnavailable,
    A2ACapabilityNotFound,
    A2AInvalidResponse,
    A2ARemoteTaskFailed,
)
from app.schemas import (
    CoverageAnalysis,
    CoverageAnalysisRequest,
    CoverageAssessment,
)


def make_request() -> CoverageAnalysisRequest:
    return CoverageAnalysisRequest(claim_number="CLM-000123")


def make_analysis() -> CoverageAnalysis:
    return CoverageAnalysis(
        claim_number="CLM-000123",
        assessment=CoverageAssessment.INSUFFICIENT_INFORMATION,
        rationale="Falta evidencia contractual.",
        missing_information=["Condicionado aplicable"],
        confidence=0.1,
    )


def data_part(payload: dict) -> Part:
    structured = Struct()
    json_format.ParseDict(payload, structured)
    return Part(data=Value(struct_value=structured))


def task_event(
    state: int,
    *,
    artifacts: list[Artifact] | None = None,
) -> StreamResponse:
    return StreamResponse(
        task=Task(
            id="test-task",
            context_id="test-context",
            status=TaskStatus(state=state),
            artifacts=artifacts or [],
        )
    )


def completed_event(payload: dict | None = None) -> StreamResponse:
    artifacts = []
    if payload is not None:
        artifacts.append(
            Artifact(
                artifact_id="coverage-artifact",
                name="coverage_analysis",
                parts=[data_part(payload)],
            )
        )
    return task_event(TaskState.TASK_STATE_COMPLETED, artifacts=artifacts)


def started_client() -> policy_client.PolicyA2AClient:
    client = policy_client.PolicyA2AClient()
    client._client = SimpleNamespace()
    return client


@pytest.mark.asyncio
async def test_client_requires_discovery_before_call():
    with pytest.raises(A2AAgentUnavailable, match="not started"):
        await policy_client.PolicyA2AClient().analyze_coverage(make_request())


@pytest.mark.asyncio
async def test_client_validates_completed_structured_analysis(monkeypatch):
    client = started_client()
    expected = make_analysis()
    collect = AsyncMock(
        return_value=[completed_event(expected.model_dump(mode="json"))]
    )
    monkeypatch.setattr(client, "_collect_events", collect)

    result = await client.analyze_coverage(make_request())

    assert result == expected
    sent_request = collect.await_args.args[0]
    payload = json_format.MessageToDict(sent_request.message.parts[0].data)
    assert payload == make_request().model_dump(mode="json")
    assert "session_id" not in payload
    assert "messages" not in payload


@pytest.mark.parametrize(
    "state",
    [
        TaskState.TASK_STATE_FAILED,
        TaskState.TASK_STATE_CANCELED,
        TaskState.TASK_STATE_REJECTED,
    ],
)
@pytest.mark.asyncio
async def test_client_maps_unsuccessful_terminal_state(monkeypatch, state):
    client = started_client()
    monkeypatch.setattr(
        client,
        "_collect_events",
        AsyncMock(return_value=[task_event(state)]),
    )

    with pytest.raises(A2ARemoteTaskFailed):
        await client.analyze_coverage(make_request())


@pytest.mark.asyncio
async def test_client_rejects_nonterminal_task(monkeypatch):
    client = started_client()
    monkeypatch.setattr(
        client,
        "_collect_events",
        AsyncMock(
            return_value=[task_event(TaskState.TASK_STATE_WORKING)]
        ),
    )

    with pytest.raises(A2AInvalidResponse, match="non-terminal"):
        await client.analyze_coverage(make_request())


@pytest.mark.asyncio
async def test_client_rejects_completed_task_without_artifact(monkeypatch):
    client = started_client()
    monkeypatch.setattr(
        client,
        "_collect_events",
        AsyncMock(return_value=[completed_event()]),
    )

    with pytest.raises(A2AInvalidResponse, match="no coverage_analysis"):
        await client.analyze_coverage(make_request())


@pytest.mark.asyncio
async def test_client_rejects_invalid_coverage_analysis(monkeypatch):
    client = started_client()
    monkeypatch.setattr(
        client,
        "_collect_events",
        AsyncMock(return_value=[completed_event({"claim_number": "CLM"})]),
    )

    with pytest.raises(A2AInvalidResponse, match="invalid CoverageAnalysis"):
        await client.analyze_coverage(make_request())


@pytest.mark.asyncio
async def test_client_maps_timeout_to_unavailable(monkeypatch):
    client = started_client()
    monkeypatch.setattr(
        policy_client,
        "POLICY_AGENT_A2A_READ_TIMEOUT_SECONDS",
        0.01,
    )

    async def wait_forever(_request):
        await asyncio.sleep(1)

    monkeypatch.setattr(client, "_collect_events", wait_forever)

    with pytest.raises(A2AAgentUnavailable, match="request failed"):
        await client.analyze_coverage(make_request())


@pytest.mark.asyncio
async def test_client_rejects_card_without_required_skill(monkeypatch):
    class MissingSkillResolver:
        def __init__(self, **kwargs):
            pass

        async def get_agent_card(self):
            return AgentCard(
                name="other-agent",
                version="1.0.0",
                skills=[],
            )

    monkeypatch.setattr(policy_client, "A2ACardResolver", MissingSkillResolver)
    client = policy_client.PolicyA2AClient()

    with pytest.raises(A2ACapabilityNotFound):
        await client.start()

    assert client._http is None
    assert client._client is None


@pytest.mark.asyncio
async def test_client_maps_discovery_failure_and_closes_resources(monkeypatch):
    class FailingResolver:
        def __init__(self, **kwargs):
            pass

        async def get_agent_card(self):
            request = httpx.Request("GET", "http://policy-agent")
            raise httpx.ConnectError("unavailable", request=request)

    monkeypatch.setattr(policy_client, "A2ACardResolver", FailingResolver)
    client = policy_client.PolicyA2AClient()

    with pytest.raises(A2AAgentUnavailable, match="discovery failed"):
        await client.start()

    assert client._http is None
    assert client._client is None
