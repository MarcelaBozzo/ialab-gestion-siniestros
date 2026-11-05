import asyncio
from uuid import uuid4

import httpx
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct, Value
from pydantic import ValidationError

from a2a.client import A2ACardResolver, Client, ClientConfig, create_client
from a2a.client.errors import A2AClientError
from a2a.types import (
    Message,
    Part,
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    StreamResponse,
    TaskState,
)
from a2a.utils import TransportProtocol

from app.a2a.errors import (
    A2AAgentUnavailable,
    A2ACapabilityNotFound,
    A2AInvalidResponse,
    A2ARemoteTaskFailed,
)
from app.config import (
    POLICY_AGENT_A2A_CONNECT_TIMEOUT_SECONDS,
    POLICY_AGENT_A2A_READ_TIMEOUT_SECONDS,
    POLICY_AGENT_A2A_URL,
)
from app.schemas import CoverageAnalysis, CoverageAnalysisRequest


TERMINAL_TASK_STATES = frozenset(
    {
        TaskState.TASK_STATE_COMPLETED,
        TaskState.TASK_STATE_FAILED,
        TaskState.TASK_STATE_CANCELED,
        TaskState.TASK_STATE_REJECTED,
    }
)


class PolicyA2AClient:
    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None
        self._client: Client | None = None

    async def start(self) -> None:
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(
                POLICY_AGENT_A2A_READ_TIMEOUT_SECONDS,
                connect=POLICY_AGENT_A2A_CONNECT_TIMEOUT_SECONDS,
            )
        )
        try:
            resolver = A2ACardResolver(
                httpx_client=self._http,
                base_url=POLICY_AGENT_A2A_URL,
            )
            card = await resolver.get_agent_card()
            if not any(
                skill.id == "analyze_coverage"
                for skill in card.skills
            ):
                raise A2ACapabilityNotFound(
                    "Policy Agent does not publish analyze_coverage"
                )

            config = ClientConfig(
                httpx_client=self._http,
                supported_protocol_bindings=[TransportProtocol.JSONRPC],
                streaming=False,
            )
            self._client = await create_client(
                card,
                client_config=config,
            )
        except A2ACapabilityNotFound:
            await self.close()
            raise
        except (httpx.HTTPError, TimeoutError, A2AClientError) as exc:
            await self.close()
            raise A2AAgentUnavailable(
                "Policy Agent discovery failed"
            ) from exc

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    async def analyze_coverage(
        self,
        request: CoverageAnalysisRequest,
    ) -> CoverageAnalysis:
        if self._client is None:
            raise A2AAgentUnavailable("Policy Agent client is not started")

        request_data = Struct()
        json_format.ParseDict(
            request.model_dump(mode="json"),
            request_data,
        )
        message = Message(
            role=Role.ROLE_USER,
            message_id=str(uuid4()),
            parts=[Part(data=Value(struct_value=request_data))],
        )
        a2a_request = SendMessageRequest(
            message=message,
            configuration=SendMessageConfiguration(
                return_immediately=False,
                accepted_output_modes=["application/json"],
            ),
        )

        try:
            events = await asyncio.wait_for(
                self._collect_events(a2a_request),
                timeout=POLICY_AGENT_A2A_READ_TIMEOUT_SECONDS,
            )
        except (httpx.HTTPError, TimeoutError, A2AClientError) as exc:
            raise A2AAgentUnavailable(
                "Policy Agent request failed"
            ) from exc

        if len(events) != 1 or not events[0].HasField("task"):
            raise A2AInvalidResponse(
                "Policy Agent did not return a task result"
            )

        task = events[0].task
        state = task.status.state
        if state not in TERMINAL_TASK_STATES:
            raise A2AInvalidResponse(
                "Policy Agent returned a non-terminal task"
            )
        if state != TaskState.TASK_STATE_COMPLETED:
            raise A2ARemoteTaskFailed(
                "Policy Agent coverage task failed"
            )

        for artifact in task.artifacts:
            if artifact.name != "coverage_analysis":
                continue
            for part in artifact.parts:
                if not part.HasField("data"):
                    continue
                payload = json_format.MessageToDict(part.data)
                try:
                    return CoverageAnalysis.model_validate(payload)
                except ValidationError as exc:
                    raise A2AInvalidResponse(
                        "Policy Agent returned an invalid CoverageAnalysis"
                    ) from exc

        raise A2AInvalidResponse(
            "Policy Agent task has no coverage_analysis artifact"
        )

    async def _collect_events(
        self,
        request: SendMessageRequest,
    ) -> list[StreamResponse]:
        assert self._client is not None
        return [
            event
            async for event in self._client.send_message(request)
        ]


policy_a2a_client = PolicyA2AClient()
