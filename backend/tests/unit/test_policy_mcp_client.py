from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from app.mcp import policy_client
from app.mcp.errors import (
    McpInvalidResponse,
    McpPolicyApiError,
    McpPolicyApiUnavailable,
    McpPolicyNotFound,
    McpToolExecutionError,
    McpToolNotFound,
    McpUnavailable,
)


class FakeClientSession:
    def __init__(self, tools=None, result=None, error=None):
        self.tools = tools or ["find_policy", "get_policy"]
        self.result = result
        self.error = error
        self.initialized = False
        self.called_with = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def initialize(self):
        self.initialized = True

    async def list_tools(self):
        if self.error:
            raise self.error
        return SimpleNamespace(
            tools=[SimpleNamespace(name=name) for name in self.tools]
        )

    async def call_tool(self, tool_name, arguments):
        self.called_with = (tool_name, arguments)
        if self.error:
            raise self.error
        return self.result


def configure_fake_transport(monkeypatch, session):
    @asynccontextmanager
    async def fake_stdio_client(parameters):
        assert parameters is policy_client.SERVER_PARAMETERS
        yield object(), object()

    monkeypatch.setattr(policy_client, "stdio_client", fake_stdio_client)
    monkeypatch.setattr(
        policy_client,
        "ClientSession",
        lambda read_stream, write_stream: session,
    )


def tool_result(
    *,
    is_error=False,
    structured_content=None,
    error_text="",
):
    return SimpleNamespace(
        is_error=is_error,
        structured_content=structured_content,
        content=[SimpleNamespace(text=error_text)] if error_text else [],
    )


@pytest.mark.asyncio
async def test_call_policy_tool_discovers_and_returns_object(monkeypatch):
    payload = {"policy_found": True, "policy_number": "POL-123456"}
    session = FakeClientSession(
        result=tool_result(structured_content=payload)
    )
    configure_fake_transport(monkeypatch, session)

    result = await policy_client.call_policy_mcp_tool(
        "find_policy",
        {"vehicle_plate": "ABCD12"},
    )

    assert result == payload
    assert session.initialized is True
    assert session.called_with == (
        "find_policy",
        {"vehicle_plate": "ABCD12"},
    )


@pytest.mark.asyncio
async def test_call_policy_tool_rejects_unknown_tool(monkeypatch):
    session = FakeClientSession(tools=["find_policy"])
    configure_fake_transport(monkeypatch, session)

    with pytest.raises(McpToolNotFound):
        await policy_client.call_policy_mcp_tool(
            "get_policy",
            {"policy_number": "POL-123456"},
        )


@pytest.mark.parametrize(
    ("error_code", "error_type"),
    [
        ("POLICY_NOT_FOUND", McpPolicyNotFound),
        ("POLICY_API_UNAVAILABLE", McpPolicyApiUnavailable),
        ("POLICY_API_ERROR", McpPolicyApiError),
        ("UNKNOWN_ERROR", McpToolExecutionError),
    ],
)
@pytest.mark.asyncio
async def test_call_policy_tool_translates_tool_errors(
    monkeypatch,
    error_code,
    error_type,
):
    session = FakeClientSession(
        result=tool_result(is_error=True, error_text=error_code)
    )
    configure_fake_transport(monkeypatch, session)

    with pytest.raises(error_type):
        await policy_client.call_policy_mcp_tool(
            "get_policy",
            {"policy_number": "POL-123456"},
        )


@pytest.mark.asyncio
async def test_call_policy_tool_rejects_non_object_result(monkeypatch):
    session = FakeClientSession(
        result=tool_result(structured_content=["invalid"])
    )
    configure_fake_transport(monkeypatch, session)

    with pytest.raises(McpInvalidResponse):
        await policy_client.call_policy_mcp_tool(
            "find_policy",
            {"vehicle_plate": "ABCD12"},
        )


@pytest.mark.asyncio
async def test_call_policy_tool_maps_transport_failure(monkeypatch):
    session = FakeClientSession(error=OSError("stdio unavailable"))
    configure_fake_transport(monkeypatch, session)

    with pytest.raises(McpUnavailable):
        await policy_client.call_policy_mcp_tool(
            "find_policy",
            {"vehicle_plate": "ABCD12"},
        )


@pytest.mark.asyncio
async def test_list_policy_tools_returns_discovery_result(monkeypatch):
    session = FakeClientSession()
    configure_fake_transport(monkeypatch, session)

    result = await policy_client.list_policy_mcp_tools()

    assert result == ["find_policy", "get_policy"]


@pytest.mark.asyncio
async def test_list_policy_tools_maps_transport_failure(monkeypatch):
    session = FakeClientSession(error=OSError("stdio unavailable"))
    configure_fake_transport(monkeypatch, session)

    with pytest.raises(McpUnavailable):
        await policy_client.list_policy_mcp_tools()
