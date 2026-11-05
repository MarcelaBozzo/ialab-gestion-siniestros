import logging
from typing import Any

from fastapi import FastAPI
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct, Value

from a2a.helpers.proto_helpers import new_task_from_user_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import TaskUpdater
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Part,
    TaskState,
)
from a2a.utils import TransportProtocol

from app.config import POLICY_AGENT_A2A_URL
from app.policy_agent_service import analyze_policy_coverage
from app.schemas import CoverageAnalysisRequest


logger = logging.getLogger(__name__)
POLICY_AGENT_URL = POLICY_AGENT_A2A_URL
JSONRPC_URL = f"{POLICY_AGENT_URL}/a2a/jsonrpc"


def json_part(payload: dict[str, Any]) -> Part:
    data = Struct()
    json_format.ParseDict(payload, data)
    return Part(data=Value(struct_value=data))


class PolicyAgentExecutor(AgentExecutor):
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        if context.message is None or context.task_id is None:
            raise ValueError("A structured A2A message is required")

        task = context.current_task
        if task is None:
            task = new_task_from_user_message(context.message)
            task.id = context.task_id
            task.context_id = context.context_id or task.context_id
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=context.task_id,
            context_id=context.context_id or task.context_id,
        )
        await updater.start_work()

        try:
            data_parts = [
                part
                for part in context.message.parts
                if part.HasField("data")
            ]
            if len(data_parts) != 1:
                raise ValueError("Expected one structured JSON request part")

            payload = json_format.MessageToDict(data_parts[0].data)
            request = CoverageAnalysisRequest.model_validate(payload)
            analysis = await analyze_policy_coverage(request)
            await updater.add_artifact(
                parts=[json_part(analysis.model_dump(mode="json"))],
                name="coverage_analysis",
                last_chunk=True,
            )
            await updater.complete()
        except Exception:
            logger.exception("Policy Agent coverage task failed")
            await updater.update_status(
                TaskState.TASK_STATE_FAILED,
                message=updater.new_agent_message(
                    [Part(text="Coverage analysis could not be completed")]
                ),
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=context.task_id or "",
            context_id=context.context_id or "",
        )
        await updater.cancel()


agent_card = AgentCard(
    name="policy-agent",
    description="Análisis propuesto de cobertura automotriz",
    version="0.1.0",
    capabilities=AgentCapabilities(streaming=False),
    default_input_modes=["application/json"],
    default_output_modes=["application/json"],
    skills=[
        AgentSkill(
            id="analyze_coverage",
            name="Analyze coverage",
            description=(
                "Analiza pólizas automotrices y condicionado para "
                "producir una propuesta de cobertura sustentada en "
                "evidencia. No aprueba ni rechaza cobertura y no "
                "ejecuta pagos."
            ),
            tags=["policy", "coverage"],
            input_modes=["application/json"],
            output_modes=["application/json"],
        )
    ],
    supported_interfaces=[
        AgentInterface(
            url=JSONRPC_URL,
            protocol_binding=TransportProtocol.JSONRPC,
            protocol_version="1.0",
        )
    ],
)

request_handler = DefaultRequestHandler(
    agent_executor=PolicyAgentExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=agent_card,
)

app = FastAPI()
add_a2a_routes_to_fastapi(
    app,
    agent_card_routes=create_agent_card_routes(agent_card=agent_card),
    jsonrpc_routes=create_jsonrpc_routes(
        request_handler=request_handler,
        rpc_url="/a2a/jsonrpc",
    ),
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "agent": "policy-agent"}
