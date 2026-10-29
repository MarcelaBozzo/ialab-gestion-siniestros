import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.mcp.errors import (
    McpInvalidResponse,
    McpPolicyApiError,
    McpPolicyApiUnavailable,
    McpPolicyNotFound,
    McpToolExecutionError,
    McpToolNotFound,
    McpUnavailable,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVER_ENV = {
    **os.environ,
    "PYTHONPATH": os.pathsep.join(
        path
        for path in (
            str(PROJECT_ROOT),
            os.environ.get("PYTHONPATH", ""),
        )
        if path
    ),
}
SERVER_PARAMETERS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "app.mcp.policy_server"],
    env=SERVER_ENV,
)


async def call_policy_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    tool_found = False
    result = None

    try:
        async with stdio_client(SERVER_PARAMETERS) as (
            read_stream,
            write_stream,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                listed_tools = await session.list_tools()
                tool_names = {tool.name for tool in listed_tools.tools}
                tool_found = tool_name in tool_names
                if tool_found:
                    result = await session.call_tool(tool_name, arguments)
    except Exception as exc:
        raise McpUnavailable("Could not connect to policy-mcp") from exc

    if not tool_found:
        raise McpToolNotFound(tool_name)

    if result is None:
        raise McpInvalidResponse(
            f"Tool {tool_name!r} did not return a result"
        )

    if result.is_error:
        error_text = " ".join(
            block.text
            for block in result.content
            if hasattr(block, "text")
        )
        if "POLICY_NOT_FOUND" in error_text:
            raise McpPolicyNotFound()
        if "POLICY_API_UNAVAILABLE" in error_text:
            raise McpPolicyApiUnavailable()
        if "POLICY_API_ERROR" in error_text:
            raise McpPolicyApiError()
        raise McpToolExecutionError(
            f"Policy MCP tool {tool_name} failed"
        )

    payload = result.structured_content
    if not isinstance(payload, dict):
        raise McpInvalidResponse(
            f"Tool {tool_name!r} did not return an object"
        )
    return payload


async def list_policy_mcp_tools() -> list[str]:
    try:
        async with stdio_client(SERVER_PARAMETERS) as (
            read_stream,
            write_stream,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                return [tool.name for tool in result.tools]
    except Exception as exc:
        raise McpUnavailable("Could not connect to policy-mcp") from exc
