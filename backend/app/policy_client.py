from datetime import datetime, timezone
from urllib.parse import quote

import httpx
from pydantic import ValidationError

from app.config import (
    POLICY_CORE_BASE_URL,
    POLICY_CORE_TIMEOUT_SECONDS,
)
from app.schemas import Policy, PolicySearchResult


class PolicyApiError(RuntimeError):
    pass


class PolicyApiUnavailable(PolicyApiError):
    pass


class PolicyNotFound(PolicyApiError):
    pass


def normalize_policy_number(policy_number: str) -> str:
    normalized = policy_number.strip().upper()

    if not normalized:
        raise ValueError("policy_number cannot be empty")

    return normalized


def normalize_vehicle_plate(vehicle_plate: str) -> str:
    normalized = (
        vehicle_plate.replace("-", "").replace(" ", "").strip().upper()
    )

    if not normalized:
        raise ValueError("vehicle_plate cannot be empty")

    return normalized


async def get_policy_from_api(
    policy_number: str,
    transport: httpx.AsyncBaseTransport | None = None,
) -> Policy:
    normalized = normalize_policy_number(policy_number)
    url = (
        f"{POLICY_CORE_BASE_URL}/policies/"
        f"{quote(normalized, safe='')}"
    )

    try:
        async with httpx.AsyncClient(
            timeout=POLICY_CORE_TIMEOUT_SECONDS,
            transport=transport,
        ) as client:
            response = await client.get(url)
    except httpx.RequestError as exc:
        raise PolicyApiUnavailable("Policy API unavailable") from exc

    if response.status_code == 404:
        raise PolicyNotFound("Policy not found")

    if response.status_code >= 500:
        raise PolicyApiUnavailable(
            f"Policy API unavailable: HTTP {response.status_code}"
        )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise PolicyApiError(
            f"Policy API returned HTTP {response.status_code}"
        ) from exc

    try:
        policy = Policy.model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise PolicyApiError(
            "Policy API returned an invalid policy response"
        ) from exc

    return policy.model_copy(
        update={
            "source_system": "policy_core",
            "retrieved_at": datetime.now(timezone.utc),
        }
    )


async def find_policy_by_vehicle_from_api(
    vehicle_plate: str,
    transport: httpx.AsyncBaseTransport | None = None,
) -> PolicySearchResult:
    normalized = normalize_vehicle_plate(vehicle_plate)
    url = (
        f"{POLICY_CORE_BASE_URL}/policies/by-vehicle/"
        f"{quote(normalized, safe='')}"
    )

    try:
        async with httpx.AsyncClient(
            timeout=POLICY_CORE_TIMEOUT_SECONDS,
            transport=transport,
        ) as client:
            response = await client.get(url)
    except httpx.RequestError as exc:
        raise PolicyApiUnavailable("Policy API unavailable") from exc

    if response.status_code == 404:
        return PolicySearchResult(
            policy_found=False,
            policy_number=None,
        )

    if response.status_code >= 500:
        raise PolicyApiUnavailable(
            f"Policy API unavailable: HTTP {response.status_code}"
        )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise PolicyApiError(
            f"Policy API returned HTTP {response.status_code}"
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise PolicyApiError("Policy API returned invalid JSON") from exc

    if not isinstance(data, dict):
        raise PolicyApiError("Policy API response must be an object")

    policy_number = data.get("policy_number")

    if not policy_number:
        raise PolicyApiError(
            "Policy API response does not contain policy_number"
        )

    if not isinstance(policy_number, str):
        raise PolicyApiError(
            "Policy API policy_number must be a string"
        )

    return PolicySearchResult(
        policy_found=True,
        policy_number=normalize_policy_number(policy_number),
    )
