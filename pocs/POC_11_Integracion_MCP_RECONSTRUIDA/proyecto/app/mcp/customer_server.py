from typing import Literal
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from app.customer_client import (
    CustomerApiError,
    CustomerApiUnavailable,
    CustomerNotFound,
    get_customer_profile as get_customer_profile_from_api,
    normalize_national_id,
    verify_customer as verify_customer_from_api,
)

mcp = MCPServer("customer-mcp")

@mcp.tool()
async def verify_customer(national_id: str) -> dict:
    """Comprueba si una persona existe como cliente. Devuelve solo existencia y customer_id."""
    try:
        result = await verify_customer_from_api(national_id)
    except CustomerApiUnavailable as exc:
        raise ToolError("CUSTOMER_API_UNAVAILABLE") from exc
    except CustomerApiError as exc:
        raise ToolError("CUSTOMER_API_ERROR") from exc
    return result.model_dump(mode="json")

@mcp.tool()
async def get_customer_profile(
    national_id: str,
    requested_field: Literal["email", "phone_number", "address"],
) -> dict:
    """Verifica al declarante y devuelve solo el campo personal solicitado."""
    try:
        verification = await verify_customer_from_api(national_id)
        if not verification.customer_found or not verification.customer_id:
            raise ToolError("CUSTOMER_NOT_FOUND")
        result = await get_customer_profile_from_api(verification.customer_id, requested_field)
        if normalize_national_id(result.national_id) != normalize_national_id(national_id):
            raise ToolError("CUSTOMER_API_ERROR")
    except CustomerApiUnavailable as exc:
        raise ToolError("CUSTOMER_API_UNAVAILABLE") from exc
    except CustomerNotFound as exc:
        raise ToolError("CUSTOMER_NOT_FOUND") from exc
    except CustomerApiError as exc:
        raise ToolError("CUSTOMER_API_ERROR") from exc
    return {requested_field: getattr(result, requested_field)}

if __name__ == "__main__":
    mcp.run()
