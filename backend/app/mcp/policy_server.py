from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from app.policy_client import (
    PolicyApiError,
    PolicyApiUnavailable,
    PolicyNotFound,
    find_policy_by_vehicle_from_api,
    get_policy_from_api,
)
from app.schemas import Policy, PolicySearchResult


mcp = MCPServer(name="policy-mcp")


@mcp.tool()
async def find_policy(vehicle_plate: str) -> PolicySearchResult:
    """Locate a policy by insured vehicle; this does not determine coverage."""
    try:
        return await find_policy_by_vehicle_from_api(vehicle_plate)
    except PolicyApiUnavailable as exc:
        raise ToolError("POLICY_API_UNAVAILABLE") from exc
    except PolicyApiError as exc:
        raise ToolError("POLICY_API_ERROR") from exc


@mcp.tool()
async def get_policy(policy_number: str) -> Policy:
    """Retrieve structured policy information; this does not determine coverage."""
    try:
        return await get_policy_from_api(policy_number)
    except PolicyNotFound as exc:
        raise ToolError("POLICY_NOT_FOUND") from exc
    except PolicyApiUnavailable as exc:
        raise ToolError("POLICY_API_UNAVAILABLE") from exc
    except PolicyApiError as exc:
        raise ToolError("POLICY_API_ERROR") from exc


if __name__ == "__main__":
    mcp.run(transport="stdio")
