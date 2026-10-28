from typing import Literal
from pydantic import ValidationError
from app.config import CUSTOMER_INTEGRATION_PROVIDER
from app.customer_client import (
    CustomerApiError,
    CustomerApiUnavailable,
    CustomerNotFound,
    get_customer_profile as get_customer_profile_from_api,
    normalize_national_id,
    verify_customer as verify_customer_from_api,
)
from app.mcp.customer_client import call_customer_mcp_tool
from app.mcp.errors import (
    McpCustomerApiError,
    McpCustomerApiUnavailable,
    McpCustomerNotFound,
    McpInvalidResponse,
)
from app.schemas import CustomerFieldValue, CustomerVerification

async def verify_claimant_customer(national_id: str) -> CustomerVerification:
    if CUSTOMER_INTEGRATION_PROVIDER == "rest":
        return await verify_customer_from_api(national_id)
    try:
        result = await call_customer_mcp_tool("verify_customer", {"national_id": national_id})
    except McpCustomerApiUnavailable as exc:
        raise CustomerApiUnavailable() from exc
    except McpCustomerApiError as exc:
        raise CustomerApiError() from exc
    try:
        return CustomerVerification.model_validate(result)
    except ValidationError as exc:
        raise McpInvalidResponse("verify_customer returned an invalid response") from exc

async def get_claimant_customer_profile(
    national_id: str,
    requested_field: Literal["email", "phone_number", "address"],
) -> CustomerFieldValue:
    if CUSTOMER_INTEGRATION_PROVIDER == "rest":
        verification = await verify_customer_from_api(national_id)
        if not verification.customer_found or not verification.customer_id:
            raise CustomerNotFound("Claimant is not a customer")
        profile = await get_customer_profile_from_api(verification.customer_id, requested_field)
        if normalize_national_id(profile.national_id) != normalize_national_id(national_id):
            raise CustomerApiError("Customer profile does not match the claimant")
        return CustomerFieldValue(requested_field=requested_field, value=getattr(profile, requested_field))
    try:
        result = await call_customer_mcp_tool(
            "get_customer_profile",
            {"national_id": national_id, "requested_field": requested_field},
        )
    except McpCustomerApiUnavailable as exc:
        raise CustomerApiUnavailable() from exc
    except McpCustomerNotFound as exc:
        raise CustomerNotFound() from exc
    except McpCustomerApiError as exc:
        raise CustomerApiError() from exc
    if not isinstance(result, dict) or set(result) != {requested_field}:
        raise McpInvalidResponse("get_customer_profile returned an invalid response")
    try:
        return CustomerFieldValue(requested_field=requested_field, value=result[requested_field])
    except ValidationError as exc:
        raise McpInvalidResponse("get_customer_profile returned an invalid response") from exc
