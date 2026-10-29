from pydantic import ValidationError

from app.mcp.errors import (
    McpInvalidResponse,
    McpPolicyApiError,
    McpPolicyApiUnavailable,
    McpPolicyNotFound,
)
from app.mcp.policy_client import call_policy_mcp_tool
from app.policy_client import (
    PolicyApiError,
    PolicyApiUnavailable,
    PolicyNotFound,
)
from app.schemas import Policy, PolicySearchResult


async def find_claim_policy(vehicle_plate: str) -> PolicySearchResult:
    try:
        result = await call_policy_mcp_tool(
            tool_name="find_policy",
            arguments={"vehicle_plate": vehicle_plate},
        )
    except McpPolicyApiUnavailable as exc:
        raise PolicyApiUnavailable() from exc
    except McpPolicyApiError as exc:
        raise PolicyApiError() from exc

    try:
        return PolicySearchResult.model_validate(result)
    except ValidationError as exc:
        raise McpInvalidResponse(
            "find_policy returned an invalid response"
        ) from exc


async def get_claim_policy(policy_number: str) -> Policy:
    try:
        result = await call_policy_mcp_tool(
            tool_name="get_policy",
            arguments={"policy_number": policy_number},
        )
    except McpPolicyApiUnavailable as exc:
        raise PolicyApiUnavailable() from exc
    except McpPolicyNotFound as exc:
        raise PolicyNotFound("Policy not found") from exc
    except McpPolicyApiError as exc:
        raise PolicyApiError() from exc

    try:
        return Policy.model_validate(result)
    except ValidationError as exc:
        raise McpInvalidResponse(
            "get_policy returned an invalid response"
        ) from exc
