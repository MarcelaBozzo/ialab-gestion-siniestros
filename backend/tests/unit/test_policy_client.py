from datetime import datetime, timezone

import httpx
import pytest

from app.policy_client import (
    PolicyApiError,
    PolicyApiUnavailable,
    PolicyNotFound,
    find_policy_by_vehicle_from_api,
    get_policy_from_api,
    normalize_policy_number,
    normalize_vehicle_plate,
)


POLICY_RESPONSE = {
    "policy_number": "POL-123456",
    "policy_status_cd": "ACTIVE",
    "effective_date": "2026-01-01",
    "expiration_date": "2026-12-31",
    "product_code": "AUTO_STANDARD",
    "insured_vehicle": {
        "vehicle_plate": "ABCD12",
        "manufacturer": "Toyota",
        "model": "Corolla",
        "model_year": 2022,
    },
    "coverages": [],
}


def mock_transport(
    status_code: int = 200,
    json_data: object | None = None,
    content: bytes | None = None,
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if content is not None:
            return httpx.Response(
                status_code,
                content=content,
                request=request,
            )
        return httpx.Response(
            status_code,
            json=json_data,
            request=request,
        )

    return httpx.MockTransport(handler)


def test_normalize_policy_number():
    assert normalize_policy_number(" pol-123456 ") == "POL-123456"


def test_normalize_vehicle_plate():
    assert normalize_vehicle_plate("AB-CD 12") == "ABCD12"


@pytest.mark.parametrize(
    ("normalizer", "value"),
    [
        (normalize_policy_number, "   "),
        (normalize_vehicle_plate, " - "),
    ],
)
def test_normalizers_reject_empty_values(normalizer, value):
    with pytest.raises(ValueError):
        normalizer(value)


@pytest.mark.asyncio
async def test_get_policy_adds_policy_core_provenance():
    before = datetime.now(timezone.utc)

    policy = await get_policy_from_api(
        " pol-123456 ",
        transport=mock_transport(json_data=POLICY_RESPONSE),
    )

    after = datetime.now(timezone.utc)
    assert policy.policy_number == "POL-123456"
    assert policy.source_system == "policy_core"
    assert before <= policy.retrieved_at <= after
    assert policy.retrieved_at.utcoffset().total_seconds() == 0


@pytest.mark.asyncio
async def test_get_policy_encodes_normalized_policy_number():
    requested_paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.raw_path)
        return httpx.Response(200, json=POLICY_RESPONSE, request=request)

    await get_policy_from_api(
        " pol/123 ",
        transport=httpx.MockTransport(handler),
    )

    assert requested_paths == [b"/policies/POL%2F123"]


@pytest.mark.asyncio
async def test_get_policy_returns_not_found_on_404():
    with pytest.raises(PolicyNotFound):
        await get_policy_from_api(
            "POL-999999",
            transport=mock_transport(status_code=404),
        )


@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [(409, PolicyApiError), (500, PolicyApiUnavailable)],
)
@pytest.mark.asyncio
async def test_get_policy_maps_http_errors(status_code, error_type):
    with pytest.raises(error_type):
        await get_policy_from_api(
            "POL-123456",
            transport=mock_transport(status_code=status_code),
        )


@pytest.mark.asyncio
async def test_get_policy_maps_connection_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(PolicyApiUnavailable):
        await get_policy_from_api(
            "POL-123456",
            transport=httpx.MockTransport(handler),
        )


@pytest.mark.parametrize(
    "transport",
    [
        mock_transport(content=b"not-json"),
        mock_transport(json_data={"policy_number": "POL-123456"}),
    ],
    ids=["invalid-json", "invalid-policy-schema"],
)
@pytest.mark.asyncio
async def test_get_policy_rejects_invalid_responses(transport):
    with pytest.raises(PolicyApiError):
        await get_policy_from_api("POL-123456", transport=transport)


@pytest.mark.asyncio
async def test_find_policy_returns_policy_number():
    result = await find_policy_by_vehicle_from_api(
        "AB-CD 12",
        transport=mock_transport(
            json_data={"policy_number": " pol-123456 "}
        ),
    )

    assert result.policy_found is True
    assert result.policy_number == "POL-123456"


@pytest.mark.asyncio
async def test_find_policy_returns_not_found_on_404():
    result = await find_policy_by_vehicle_from_api(
        "WXYZ99",
        transport=mock_transport(status_code=404),
    )

    assert result.policy_found is False
    assert result.policy_number is None


@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [(409, PolicyApiError), (500, PolicyApiUnavailable)],
)
@pytest.mark.asyncio
async def test_find_policy_maps_http_errors(status_code, error_type):
    with pytest.raises(error_type):
        await find_policy_by_vehicle_from_api(
            "ABCD12",
            transport=mock_transport(status_code=status_code),
        )


@pytest.mark.asyncio
async def test_find_policy_maps_connection_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(PolicyApiUnavailable):
        await find_policy_by_vehicle_from_api(
            "ABCD12",
            transport=httpx.MockTransport(handler),
        )


@pytest.mark.parametrize(
    "transport",
    [
        mock_transport(content=b"not-json"),
        mock_transport(json_data=[]),
        mock_transport(json_data={}),
        mock_transport(json_data={"policy_number": 123}),
    ],
    ids=[
        "invalid-json",
        "non-object",
        "missing-policy-number",
        "invalid-policy-number",
    ],
)
@pytest.mark.asyncio
async def test_find_policy_rejects_invalid_responses(transport):
    with pytest.raises(PolicyApiError):
        await find_policy_by_vehicle_from_api(
            "ABCD12",
            transport=transport,
        )
