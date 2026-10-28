from urllib.parse import quote
import httpx
from pydantic import ValidationError
from app.config import CUSTOMER_API_BASE_URL, CUSTOMER_API_TIMEOUT_SECONDS
from app.schemas import CustomerProfile, CustomerVerification

class CustomerApiError(RuntimeError):
    pass

class CustomerApiUnavailable(CustomerApiError):
    pass

class CustomerNotFound(CustomerApiError):
    pass

def normalize_national_id(national_id: str) -> str:
    normalized = national_id.replace(".", "").replace("-", "").strip().upper()
    if not normalized:
        raise ValueError("national_id cannot be empty")
    return normalized

def _create_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=CUSTOMER_API_TIMEOUT_SECONDS)

def _raise_for_customer_response(response: httpx.Response) -> None:
    if response.status_code >= 500:
        raise CustomerApiUnavailable(f"Customer API returned HTTP {response.status_code}")
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise CustomerApiError(f"Customer API returned HTTP {response.status_code}") from exc

async def verify_customer(national_id: str) -> CustomerVerification:
    normalized = normalize_national_id(national_id)
    url = f"{CUSTOMER_API_BASE_URL}/customers/by-national-id/{quote(normalized, safe='')}"
    try:
        async with _create_http_client() as client:
            response = await client.get(url)
    except httpx.RequestError as exc:
        raise CustomerApiUnavailable("Customer API unavailable") from exc
    if response.status_code == 404:
        return CustomerVerification(customer_found=False, customer_id=None)
    _raise_for_customer_response(response)
    try:
        data = response.json()
    except ValueError as exc:
        raise CustomerApiError("Customer API returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise CustomerApiError("Customer API response must be a JSON object")
    customer_id = data.get("customer_id")
    if not isinstance(customer_id, str) or not customer_id.strip():
        raise CustomerApiError("Customer API response does not contain customer_id")
    return CustomerVerification(customer_found=True, customer_id=customer_id)

async def get_customer_profile(customer_id: str, requested_field: str) -> CustomerProfile:
    if not customer_id or not customer_id.strip():
        raise ValueError("customer_id cannot be empty")
    if requested_field not in {"email", "phone_number", "address"}:
        raise ValueError("Unsupported customer profile field")
    url = f"{CUSTOMER_API_BASE_URL}/customers/{quote(customer_id, safe='')}"
    try:
        async with _create_http_client() as client:
            response = await client.get(url, params={"fields": requested_field})
    except httpx.RequestError as exc:
        raise CustomerApiUnavailable("Customer API unavailable") from exc
    if response.status_code == 404:
        raise CustomerNotFound("Customer not found")
    _raise_for_customer_response(response)
    try:
        return CustomerProfile.model_validate(response.json())
    except ValidationError as exc:
        raise CustomerApiError("Customer API returned an invalid customer profile") from exc
    except ValueError as exc:
        raise CustomerApiError("Customer API returned invalid JSON") from exc

async def check_customer_api_health() -> bool:
    try:
        async with _create_http_client() as client:
            response = await client.get(f"{CUSTOMER_API_BASE_URL}/health")
    except httpx.RequestError:
        return False
    return response.is_success
