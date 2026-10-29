import httpx
import pytest

from app import policy_core
from app.schemas import Policy


@pytest.fixture
def policy_core_transport():
    return httpx.ASGITransport(app=policy_core.app)


@pytest.mark.asyncio
async def test_policy_core_health(policy_core_transport):
    async with httpx.AsyncClient(
        transport=policy_core_transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_existing_policy_endpoint_is_preserved(policy_core_transport):
    async with httpx.AsyncClient(
        transport=policy_core_transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/policies/POL-123456")

    assert response.status_code == 200
    assert response.json()["policy_number"] == "POL-123456"


@pytest.mark.asyncio
async def test_policy_core_finds_policy_by_normalized_vehicle_plate(
    policy_core_transport,
):
    async with httpx.AsyncClient(
        transport=policy_core_transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/policies/by-vehicle/AB-CD%2012")

    assert response.status_code == 200
    assert response.json() == {"policy_number": "POL-123456"}


@pytest.mark.asyncio
async def test_policy_core_returns_not_found_for_unknown_vehicle(
    policy_core_transport,
):
    async with httpx.AsyncClient(
        transport=policy_core_transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/policies/by-vehicle/WXYZ99")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_policy_core_rejects_ambiguous_vehicle_lookup(
    policy_core_transport,
    monkeypatch,
):
    duplicate = policy_core.policies["POL-123456"].model_copy(
        update={"policy_number": "POL-654321"}
    )
    monkeypatch.setattr(
        policy_core,
        "policies",
        {**policy_core.policies, duplicate.policy_number: duplicate},
    )

    async with httpx.AsyncClient(
        transport=policy_core_transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/policies/by-vehicle/ABCD12")

    assert response.status_code == 409
    assert response.json() == {"detail": "Policy lookup is ambiguous"}
