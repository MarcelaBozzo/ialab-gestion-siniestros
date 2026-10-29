from datetime import date

from fastapi import HTTPException

from app.policy_client import (
    PolicyApiError,
    PolicyApiUnavailable,
    PolicyNotFound,
    get_policy_from_api,
)
from app.schemas import Policy


async def get_policy(policy_number: str) -> Policy:
    try:
        return await get_policy_from_api(policy_number)
    except PolicyNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail="Policy not found",
        ) from exc
    except PolicyApiUnavailable as exc:
        raise HTTPException(
            status_code=502,
            detail="Policy Core is unavailable",
        ) from exc
    except PolicyApiError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Policy Core returned an invalid policy response"
                if "invalid policy response" in str(exc)
                else "Policy Core returned an unexpected error"
            ),
        ) from exc


def is_policy_effective_on_loss_date(
    policy: Policy,
    loss_dt: date,
) -> bool:
    return policy.effective_date <= loss_dt <= policy.expiration_date
