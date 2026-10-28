from unittest.mock import AsyncMock

import pytest

from app import customer_service
from app.mcp.errors import McpInvalidResponse


@pytest.mark.asyncio
async def test_customer_service_sends_only_explicit_mcp_arguments(monkeypatch):
    calls = []

    async def fake_call(tool_name, arguments):
        calls.append((tool_name, dict(arguments)))
        if tool_name == "verify_customer":
            return {"customer_found": True, "customer_id": "CUST-000123"}
        return {"email": "alejandro.torres@example.com"}

    monkeypatch.setattr(customer_service, "CUSTOMER_INTEGRATION_PROVIDER", "mcp")
    monkeypatch.setattr(customer_service, "call_customer_mcp_tool", fake_call)

    await customer_service.verify_claimant_customer("123456785")
    result = await customer_service.get_claimant_customer_profile("123456785", "email")

    assert result.requested_field == "email"
    assert result.value == "alejandro.torres@example.com"
    assert calls == [
        ("verify_customer", {"national_id": "123456785"}),
        (
            "get_customer_profile",
            {"national_id": "123456785", "requested_field": "email"},
        ),
    ]
    assert all("session_id" not in args for _, args in calls)
    assert all("customer_id" not in args for _, args in calls)


@pytest.mark.asyncio
async def test_customer_service_rejects_invalid_mcp_profile(monkeypatch):
    monkeypatch.setattr(customer_service, "CUSTOMER_INTEGRATION_PROVIDER", "mcp")
    monkeypatch.setattr(
        customer_service,
        "call_customer_mcp_tool",
        AsyncMock(return_value={"unexpected": "payload"}),
    )
    with pytest.raises(McpInvalidResponse):
        await customer_service.get_claimant_customer_profile("123456785", "email")
