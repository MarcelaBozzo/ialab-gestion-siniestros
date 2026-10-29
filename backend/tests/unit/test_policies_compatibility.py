from datetime import date

import pytest
from fastapi import HTTPException

from app import policies
from app.policy_client import (
    PolicyApiError,
    PolicyApiUnavailable,
    PolicyNotFound,
)
from app.schemas import Policy


@pytest.mark.asyncio
async def test_compatibility_facade_delegates_to_canonical_client(monkeypatch):
    expected = Policy(
        policy_number="POL-123456",
        policy_status_cd="ACTIVE",
        effective_date=date(2026, 1, 1),
        expiration_date=date(2026, 12, 31),
    )

    async def fake_get_policy(policy_number):
        assert policy_number == "POL-123456"
        return expected

    monkeypatch.setattr(policies, "get_policy_from_api", fake_get_policy)

    assert await policies.get_policy("POL-123456") is expected


@pytest.mark.parametrize(
    ("error", "status_code", "detail"),
    [
        (PolicyNotFound("Policy not found"), 404, "Policy not found"),
        (
            PolicyApiUnavailable("Policy API unavailable"),
            502,
            "Policy Core is unavailable",
        ),
        (
            PolicyApiError("Policy API returned HTTP 409"),
            502,
            "Policy Core returned an unexpected error",
        ),
        (
            PolicyApiError("Policy API returned an invalid policy response"),
            502,
            "Policy Core returned an invalid policy response",
        ),
    ],
)
@pytest.mark.asyncio
async def test_compatibility_facade_preserves_http_errors(
    monkeypatch,
    error,
    status_code,
    detail,
):
    async def fake_get_policy(policy_number):
        raise error

    monkeypatch.setattr(policies, "get_policy_from_api", fake_get_policy)

    with pytest.raises(HTTPException) as exc_info:
        await policies.get_policy("POL-123456")

    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


def test_loss_date_compatibility_helper_is_preserved():
    policy = Policy(
        policy_number="POL-123456",
        policy_status_cd="ACTIVE",
        effective_date=date(2026, 1, 1),
        expiration_date=date(2026, 12, 31),
    )

    assert policies.is_policy_effective_on_loss_date(
        policy,
        date(2026, 6, 15),
    )
