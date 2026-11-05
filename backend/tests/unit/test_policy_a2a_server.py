import httpx
import pytest

from a2a.utils import TransportProtocol

from app.a2a.policy_server import agent_card, app


def test_agent_card_publishes_only_structured_coverage_analysis():
    assert agent_card.name == "policy-agent"
    assert agent_card.capabilities.streaming is False
    assert agent_card.default_input_modes == ["application/json"]
    assert agent_card.default_output_modes == ["application/json"]
    assert len(agent_card.supported_interfaces) == 1
    interface = agent_card.supported_interfaces[0]
    assert interface.protocol_binding == TransportProtocol.JSONRPC
    assert interface.protocol_version == "1.0"
    assert interface.url.endswith("/a2a/jsonrpc")

    assert [skill.id for skill in agent_card.skills] == [
        "analyze_coverage"
    ]
    skill = agent_card.skills[0]
    assert skill.input_modes == ["application/json"]
    assert skill.output_modes == ["application/json"]
    assert "No aprueba ni rechaza cobertura" in skill.description
    assert "no ejecuta pagos" in skill.description


@pytest.mark.asyncio
async def test_policy_agent_server_exposes_health_and_agent_card():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        health = await client.get("/health")
        card = await client.get("/.well-known/agent-card.json")

    assert health.status_code == 200
    assert health.json() == {"status": "ok", "agent": "policy-agent"}
    assert card.status_code == 200
    assert card.json()["name"] == "policy-agent"
    assert card.json()["skills"][0]["id"] == "analyze_coverage"
