from datetime import date

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

from app.config import POLICY_CORE_BASE_URL
from app.schemas import Policy


async def get_policy(policy_number: str) -> Policy:
    url = f"{POLICY_CORE_BASE_URL.rstrip('/')}/policies/{policy_number}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)

        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Policy not found",
            )

        response.raise_for_status()
        return Policy.model_validate(response.json())

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail="Policy Core returned an unexpected error",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Policy Core is unavailable",
        ) from exc
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Policy Core returned an invalid policy response",
        ) from exc


def is_policy_effective_on_loss_date(
    policy: Policy,
    loss_dt: date,
) -> bool:
    return policy.effective_date <= loss_dt <= policy.expiration_date
