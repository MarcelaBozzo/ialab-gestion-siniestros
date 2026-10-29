from unittest.mock import AsyncMock

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from app.mcp import policy_client, policy_server
from app.mcp.errors import McpPolicyApiUnavailable, McpToolNotFound
from app.mcp.policy_client import (
    call_policy_mcp_tool,
    list_policy_mcp_tools,
)
from app.policy_client import PolicyNotFound
from app.schemas import PolicySearchResult


@pytest.mark.asyncio
async def test_policy_mcp_serializes_pydantic_result_as_structured_content(
    monkeypatch,
):
    monkeypatch.setattr(
        policy_server,
        "find_policy_by_vehicle_from_api",
        AsyncMock(
            return_value=PolicySearchResult(
                policy_found=True,
                policy_number="POL-123456",
            )
        ),
    )

    result = await policy_server.mcp.call_tool(
        "find_policy",
        {"vehicle_plate": "ABCD12"},
    )

    assert result.is_error is False
    assert result.structured_content == {
        "policy_found": True,
        "policy_number": "POL-123456",
    }


@pytest.mark.asyncio
async def test_policy_mcp_surfaces_coded_tool_error(monkeypatch):
    monkeypatch.setattr(
        policy_server,
        "get_policy_from_api",
        AsyncMock(side_effect=PolicyNotFound("not found")),
    )

    with pytest.raises(ToolError, match="POLICY_NOT_FOUND"):
        await policy_server.mcp.call_tool(
            "get_policy",
            {"policy_number": "POL-999999"},
        )


@pytest.mark.asyncio
async def test_policy_mcp_stdio_discovery_exposes_only_policy_tools():
    tools = await list_policy_mcp_tools()

    assert set(tools) == {"find_policy", "get_policy"}


@pytest.mark.asyncio
async def test_policy_mcp_stdio_rejects_unknown_tool_before_invocation():
    with pytest.raises(McpToolNotFound):
        await call_policy_mcp_tool("unknown_policy_tool", {})


@pytest.mark.asyncio
async def test_policy_mcp_stdio_preserves_policy_core_unavailable(monkeypatch):
    monkeypatch.setitem(
        policy_client.SERVER_PARAMETERS.env,
        "POLICY_CORE_BASE_URL",
        "http://127.0.0.1:1",
    )

    with pytest.raises(McpPolicyApiUnavailable):
        await call_policy_mcp_tool(
            "get_policy",
            {"policy_number": "POL-123456"},
        )
