from datetime import datetime, timezone

import pytest

from app import policy_service
from app.mcp.errors import (
    McpInvalidResponse,
    McpPolicyApiError,
    McpPolicyApiUnavailable,
    McpPolicyNotFound,
    McpUnavailable,
)
from app.policy_client import (
    PolicyApiError,
    PolicyApiUnavailable,
    PolicyNotFound,
)


async def set_mcp_result(monkeypatch, result):
    calls = []

    async def fake_call(tool_name, arguments):
        calls.append((tool_name, arguments))
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(policy_service, "call_policy_mcp_tool", fake_call)
    return calls


@pytest.mark.parametrize(
    ("payload", "expected_found", "expected_number"),
    [
        (
            {"policy_found": True, "policy_number": "POL-123456"},
            True,
            "POL-123456",
        ),
        (
            {"policy_found": False, "policy_number": None},
            False,
            None,
        ),
    ],
)
@pytest.mark.asyncio
async def test_find_claim_policy_validates_existence_result(
    monkeypatch,
    payload,
    expected_found,
    expected_number,
):
    calls = await set_mcp_result(monkeypatch, payload)

    result = await policy_service.find_claim_policy("AB-CD 12")

    assert result.policy_found is expected_found
    assert result.policy_number == expected_number
    assert calls == [
        ("find_policy", {"vehicle_plate": "AB-CD 12"})
    ]


@pytest.mark.parametrize(
    ("mcp_error", "domain_error"),
    [
        (McpPolicyApiUnavailable(), PolicyApiUnavailable),
        (McpPolicyApiError(), PolicyApiError),
    ],
)
@pytest.mark.asyncio
async def test_find_claim_policy_translates_domain_errors(
    monkeypatch,
    mcp_error,
    domain_error,
):
    await set_mcp_result(monkeypatch, mcp_error)

    with pytest.raises(domain_error):
        await policy_service.find_claim_policy("ABCD12")


@pytest.mark.asyncio
async def test_find_claim_policy_rejects_invalid_contract(monkeypatch):
    await set_mcp_result(
        monkeypatch,
        {"policy_found": True, "policy_number": None},
    )

    with pytest.raises(McpInvalidResponse):
        await policy_service.find_claim_policy("ABCD12")


@pytest.mark.asyncio
async def test_get_claim_policy_preserves_provenance(monkeypatch):
    retrieved_at = datetime(2026, 10, 29, 12, 0, tzinfo=timezone.utc)
    payload = {
        "policy_number": "POL-123456",
        "policy_status_cd": "ACTIVE",
        "effective_date": "2026-01-01",
        "expiration_date": "2026-12-31",
        "insured_vehicle": {"vehicle_plate": "ABCD12"},
        "source_system": "policy_core",
        "retrieved_at": retrieved_at.isoformat(),
    }
    calls = await set_mcp_result(monkeypatch, payload)

    policy = await policy_service.get_claim_policy("POL-123456")

    assert policy.source_system == "policy_core"
    assert policy.retrieved_at == retrieved_at
    assert calls == [
        ("get_policy", {"policy_number": "POL-123456"})
    ]


@pytest.mark.parametrize(
    ("mcp_error", "domain_error"),
    [
        (McpPolicyNotFound(), PolicyNotFound),
        (McpPolicyApiUnavailable(), PolicyApiUnavailable),
        (McpPolicyApiError(), PolicyApiError),
    ],
)
@pytest.mark.asyncio
async def test_get_claim_policy_translates_domain_errors(
    monkeypatch,
    mcp_error,
    domain_error,
):
    await set_mcp_result(monkeypatch, mcp_error)

    with pytest.raises(domain_error):
        await policy_service.get_claim_policy("POL-123456")


@pytest.mark.asyncio
async def test_get_claim_policy_rejects_invalid_contract(monkeypatch):
    await set_mcp_result(monkeypatch, {"policy_number": "POL-123456"})

    with pytest.raises(McpInvalidResponse):
        await policy_service.get_claim_policy("POL-123456")


@pytest.mark.parametrize(
    "operation,argument",
    [
        (policy_service.find_claim_policy, "ABCD12"),
        (policy_service.get_claim_policy, "POL-123456"),
    ],
)
@pytest.mark.asyncio
async def test_policy_service_preserves_mcp_transport_failure(
    monkeypatch,
    operation,
    argument,
):
    await set_mcp_result(monkeypatch, McpUnavailable("unavailable"))

    with pytest.raises(McpUnavailable):
        await operation(argument)
