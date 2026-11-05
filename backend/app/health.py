import httpx
from a2a.client import A2ACardResolver
from fastapi import APIRouter, HTTPException

from app.config import (
    POLICY_AGENT_A2A_CONNECT_TIMEOUT_SECONDS,
    POLICY_AGENT_A2A_READ_TIMEOUT_SECONDS,
    POLICY_AGENT_A2A_URL,
)
from app.mcp.customer_client import list_customer_mcp_tools
from app.mcp.errors import McpUnavailable
from app.schemas import CustomerMcpHealthResponse, PolicyAgentHealthResponse

router = APIRouter()
EXPECTED_CUSTOMER_TOOLS = {"verify_customer", "get_customer_profile"}

@router.get(
    "/health/customer-mcp",
    response_model=CustomerMcpHealthResponse,
    responses={503: {"description": "Customer MCP unavailable or unhealthy"}},
    tags=["Health"],
)
async def customer_mcp_health() -> CustomerMcpHealthResponse:
    try:
        tool_names = await list_customer_mcp_tools()
    except McpUnavailable as exc:
        raise HTTPException(status_code=503, detail="Customer MCP is unavailable") from exc
    if set(tool_names) != EXPECTED_CUSTOMER_TOOLS:
        raise HTTPException(status_code=503, detail="Customer MCP tool contract is unhealthy")
    return CustomerMcpHealthResponse(status="ok", server="customer-mcp", tools=sorted(tool_names))


@router.get(
    "/health/policy-agent",
    response_model=PolicyAgentHealthResponse,
    tags=["Health"],
    responses={
        503: {"description": "Policy Agent unavailable or missing skill"},
    },
)
async def policy_agent_health() -> PolicyAgentHealthResponse:
    timeout = httpx.Timeout(
        POLICY_AGENT_A2A_READ_TIMEOUT_SECONDS,
        connect=POLICY_AGENT_A2A_CONNECT_TIMEOUT_SECONDS,
    )
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resolver = A2ACardResolver(
                httpx_client=client,
                base_url=POLICY_AGENT_A2A_URL,
            )
            card = await resolver.get_agent_card()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Policy Agent is unavailable",
        ) from exc

    skills = sorted(skill.id for skill in card.skills)
    if "analyze_coverage" not in skills:
        raise HTTPException(
            status_code=503,
            detail="Policy Agent does not publish analyze_coverage",
        )

    return PolicyAgentHealthResponse(
        status="ok",
        agent="policy-agent",
        skills=skills,
    )
