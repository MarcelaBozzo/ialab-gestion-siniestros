from datetime import date
from unittest.mock import AsyncMock

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from app.mcp import policy_server
from app.policy_client import (
    PolicyApiError,
    PolicyApiUnavailable,
    PolicyNotFound,
)
from app.schemas import Policy, PolicySearchResult


@pytest.mark.asyncio
async def test_policy_mcp_exposes_only_read_only_policy_tools():
    tools = await policy_server.mcp.list_tools()

    assert {tool.name for tool in tools} == {"find_policy", "get_policy"}


@pytest.mark.asyncio
async def test_find_policy_returns_structured_search_result(monkeypatch):
    expected = PolicySearchResult(
        policy_found=True,
        policy_number="POL-123456",
    )
    api_call = AsyncMock(return_value=expected)
    monkeypatch.setattr(
        policy_server,
        "find_policy_by_vehicle_from_api",
        api_call,
    )

    result = await policy_server.find_policy("ABCD12")

    assert result is expected
    api_call.assert_awaited_once_with("ABCD12")


@pytest.mark.asyncio
async def test_get_policy_returns_structured_policy(monkeypatch):
    expected = Policy(
        policy_number="POL-123456",
        policy_status_cd="ACTIVE",
        effective_date=date(2026, 1, 1),
        expiration_date=date(2026, 12, 31),
    )
    api_call = AsyncMock(return_value=expected)
    monkeypatch.setattr(policy_server, "get_policy_from_api", api_call)

    result = await policy_server.get_policy("POL-123456")

    assert result is expected
    api_call.assert_awaited_once_with("POL-123456")


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (PolicyApiUnavailable("unavailable"), "POLICY_API_UNAVAILABLE"),
        (PolicyApiError("invalid response"), "POLICY_API_ERROR"),
    ],
)
@pytest.mark.asyncio
async def test_find_policy_translates_rest_errors(
    monkeypatch,
    error,
    expected_code,
):
    monkeypatch.setattr(
        policy_server,
        "find_policy_by_vehicle_from_api",
        AsyncMock(side_effect=error),
    )

    with pytest.raises(ToolError, match=expected_code):
        await policy_server.find_policy("ABCD12")


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (PolicyNotFound("not found"), "POLICY_NOT_FOUND"),
        (PolicyApiUnavailable("unavailable"), "POLICY_API_UNAVAILABLE"),
        (PolicyApiError("invalid response"), "POLICY_API_ERROR"),
    ],
)
@pytest.mark.asyncio
async def test_get_policy_translates_rest_errors(
    monkeypatch,
    error,
    expected_code,
):
    monkeypatch.setattr(
        policy_server,
        "get_policy_from_api",
        AsyncMock(side_effect=error),
    )

    with pytest.raises(ToolError, match=expected_code):
        await policy_server.get_policy("POL-123456")
