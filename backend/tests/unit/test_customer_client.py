import httpx
import pytest

from app import customer_client
from app.customer_client import CustomerApiUnavailable, normalize_national_id, verify_customer


def test_normalize_national_id():
    assert normalize_national_id("12.345.678-5") == "123456785"


def test_normalize_empty_national_id():
    with pytest.raises(ValueError):
        normalize_national_id("   ")


@pytest.mark.asyncio
async def test_verify_customer_found(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/customers/by-national-id/123456785")
        return httpx.Response(200, json={"customer_id": "CUST-000123"})

    monkeypatch.setattr(
        customer_client,
        "_create_http_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=1),
    )
    result = await verify_customer("12.345.678-5")
    assert result.customer_found is True
    assert result.customer_id == "CUST-000123"


@pytest.mark.asyncio
async def test_verify_customer_not_found(monkeypatch):
    monkeypatch.setattr(
        customer_client,
        "_create_http_client",
        lambda: httpx.AsyncClient(
            transport=httpx.MockTransport(lambda request: httpx.Response(404)),
            timeout=1,
        ),
    )
    result = await verify_customer("999999999")
    assert result.customer_found is False
    assert result.customer_id is None


@pytest.mark.asyncio
async def test_customer_api_500_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        customer_client,
        "_create_http_client",
        lambda: httpx.AsyncClient(
            transport=httpx.MockTransport(lambda request: httpx.Response(500)),
            timeout=1,
        ),
    )
    with pytest.raises(CustomerApiUnavailable):
        await verify_customer("123456785")
