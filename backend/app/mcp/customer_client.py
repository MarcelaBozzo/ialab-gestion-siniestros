import os
import sys
from pathlib import Path
from typing import Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.mcp.errors import (
    McpCustomerApiError,
    McpCustomerApiUnavailable,
    McpCustomerNotFound,
    McpInvalidResponse,
    McpToolExecutionError,
    McpToolNotFound,
    McpUnavailable,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
python_path = os.environ.get("PYTHONPATH", "")
SERVER_ENV = {
    **os.environ,
    "PYTHONPATH": os.pathsep.join(path for path in (str(PROJECT_ROOT), python_path) if path),
}
SERVER_PARAMETERS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "app.mcp.customer_server"],
    env=SERVER_ENV,
)

async def call_customer_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        async with stdio_client(SERVER_PARAMETERS) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                listed_tools = await session.list_tools()
                tool_names = {tool.name for tool in listed_tools.tools}
                if tool_name not in tool_names:
                    raise McpToolNotFound(tool_name)
                result = await session.call_tool(tool_name, arguments)
                if result.is_error:
                    error_text = " ".join(block.text for block in result.content if hasattr(block, "text"))
                    if "CUSTOMER_API_UNAVAILABLE" in error_text:
                        raise McpCustomerApiUnavailable()
                    if "CUSTOMER_API_ERROR" in error_text:
                        raise McpCustomerApiError()
                    if "CUSTOMER_NOT_FOUND" in error_text:
                        raise McpCustomerNotFound()
                    raise McpToolExecutionError(f"Customer MCP tool {tool_name} failed")
                payload = result.structured_content
                if not isinstance(payload, dict):
                    raise McpInvalidResponse(f"Tool {tool_name!r} did not return an object")
                return payload
    except (McpCustomerApiUnavailable, McpCustomerApiError, McpCustomerNotFound, McpInvalidResponse, McpToolExecutionError, McpToolNotFound):
        raise
    except Exception as exc:
        raise McpUnavailable("Could not connect to customer-mcp") from exc

async def list_customer_mcp_tools() -> list[str]:
    try:
        async with stdio_client(SERVER_PARAMETERS) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                return [tool.name for tool in result.tools]
    except Exception as exc:
        raise McpUnavailable("Could not connect to customer-mcp") from exc
