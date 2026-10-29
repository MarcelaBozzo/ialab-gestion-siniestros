from datetime import date
from unittest.mock import AsyncMock

import pytest

from app import tools
from app.agent import agent
from app.schemas import Policy, PolicySearchResult


@pytest.mark.asyncio
async def test_find_policy_tool_delegates_to_application_service(monkeypatch):
    expected = PolicySearchResult(
        policy_found=True,
        policy_number="POL-123456",
    )
    service = AsyncMock(return_value=expected)
    monkeypatch.setattr(tools, "find_claim_policy", service)

    result = await tools.find_policy_tool("ABCD12")

    assert result is expected
    service.assert_awaited_once_with("ABCD12")


@pytest.mark.asyncio
async def test_get_policy_tool_delegates_to_application_service(monkeypatch):
    expected = Policy(
        policy_number="POL-123456",
        policy_status_cd="ACTIVE",
        effective_date=date(2026, 1, 1),
        expiration_date=date(2026, 12, 31),
    )
    service = AsyncMock(return_value=expected)
    monkeypatch.setattr(tools, "get_claim_policy", service)

    result = await tools.get_policy_tool("POL-123456")

    assert result is expected
    service.assert_awaited_once_with("POL-123456")


def test_agent_preserves_existing_tools_and_registers_policy_tools():
    tool_names = set(agent._function_toolset.tools)

    assert {
        "calculate_deductible",
        "calculate_reserve",
        "get_missing_claim_information",
        "verify_customer_tool",
        "get_customer_profile_tool",
        "find_policy_tool",
        "get_policy_tool",
    }.issubset(tool_names)
