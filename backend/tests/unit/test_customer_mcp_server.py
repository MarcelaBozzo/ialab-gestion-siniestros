from unittest.mock import AsyncMock

import pytest

from app.mcp import customer_server
from app.schemas import CustomerProfile, CustomerVerification


@pytest.mark.asyncio
async def test_verify_customer_returns_minimal_contract(monkeypatch):
    monkeypatch.setattr(
        customer_server,
        "verify_customer_from_api",
        AsyncMock(
            return_value=CustomerVerification(
                customer_found=True,
                customer_id="CUST-000123",
            )
        ),
    )
    result = await customer_server.verify_customer("123456785")
    assert result == {"customer_found": True, "customer_id": "CUST-000123"}


@pytest.mark.asyncio
async def test_get_customer_profile_returns_only_requested_field(monkeypatch):
    monkeypatch.setattr(
        customer_server,
        "verify_customer_from_api",
        AsyncMock(
            return_value=CustomerVerification(
                customer_found=True,
                customer_id="CUST-000123",
            )
        ),
    )
    monkeypatch.setattr(
        customer_server,
        "get_customer_profile_from_api",
        AsyncMock(
            return_value=CustomerProfile(
                customer_id="CUST-000123",
                national_id="123456785",
                full_name="Alejandro Torres Munoz",
                email="alejandro.torres@example.com",
                phone_number="+56955550123",
                address="Av. Ejemplo 1234, Santiago",
            )
        ),
    )
    result = await customer_server.get_customer_profile("123456785", "email")
    assert result == {"email": "alejandro.torres@example.com"}
    assert "customer_id" not in result
    assert "national_id" not in result
    assert "full_name" not in result
