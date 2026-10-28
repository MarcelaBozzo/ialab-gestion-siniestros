from fastapi import APIRouter, HTTPException
from app.mcp.customer_client import list_customer_mcp_tools
from app.mcp.errors import McpUnavailable
from app.schemas import CustomerMcpHealthResponse

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
