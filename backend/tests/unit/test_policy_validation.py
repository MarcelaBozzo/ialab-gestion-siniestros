from datetime import date, datetime, timezone

import pytest

from app.policy_validation import (
    is_policy_effective_on_loss_date,
    validate_policy_active_on_loss_date,
    validate_policy_against_claim,
    validate_policy_exists,
    validate_policy_number_match,
    validate_policy_vehicle_match,
)
from app.schemas import (
    ClaimData,
    ClaimsOccurrence,
    Policy,
    PolicySearchResult,
    VehInfo,
)


def make_policy(**updates) -> Policy:
    values = {
        "policy_number": "POL-123456",
        "policy_status_cd": "ACTIVE",
        "effective_date": date(2026, 1, 1),
        "expiration_date": date(2026, 12, 31),
        "insured_vehicle": VehInfo(vehicle_plate="ABCD12"),
    }
    values.update(updates)
    return Policy(**values)


@pytest.mark.parametrize(
    ("search_result", "expected"),
    [
        (PolicySearchResult(policy_found=True, policy_number="POL-1"), True),
        (PolicySearchResult(policy_found=False), False),
    ],
)
def test_validate_policy_exists(search_result, expected):
    assert validate_policy_exists(search_result) is expected


@pytest.mark.parametrize(
    ("claim_number", "expected"),
    [
        (" pol-123456 ", True),
        ("POL-999999", False),
        (None, None),
    ],
)
def test_validate_policy_number_match(claim_number, expected):
    claim = ClaimData(
        claim_number="CLM-1",
        policy_number=claim_number,
    )

    assert validate_policy_number_match(claim, make_policy()) is expected


@pytest.mark.parametrize(
    ("claim_vehicle", "policy_vehicle", "expected"),
    [
        (
            VehInfo(vehicle_plate="AB-CD 12"),
            VehInfo(vehicle_plate="ABCD12"),
            True,
        ),
        (
            VehInfo(vehicle_plate="WXYZ99"),
            VehInfo(vehicle_plate="ABCD12"),
            False,
        ),
        (None, VehInfo(vehicle_plate="ABCD12"), None),
        (VehInfo(vehicle_plate="ABCD12"), None, None),
        (VehInfo(), VehInfo(vehicle_plate="ABCD12"), None),
    ],
)
def test_validate_policy_vehicle_match(
    claim_vehicle,
    policy_vehicle,
    expected,
):
    claim = ClaimData(claim_number="CLM-1", veh_info=claim_vehicle)
    policy = make_policy(insured_vehicle=policy_vehicle)

    assert validate_policy_vehicle_match(claim, policy) is expected


@pytest.mark.parametrize(
    ("loss_date", "expected"),
    [
        (date(2026, 1, 1), True),
        (date(2026, 12, 31), True),
        (date(2025, 12, 31), False),
        (date(2027, 1, 1), False),
        (None, None),
    ],
)
def test_validate_policy_active_on_loss_date(loss_date, expected):
    claim = ClaimData(
        claim_number="CLM-1",
        claims_occurrence=ClaimsOccurrence(loss_dt=loss_date),
    )

    assert (
        validate_policy_active_on_loss_date(claim, make_policy())
        is expected
    )


def test_effective_date_helper_accepts_datetime():
    loss_dt = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)

    assert is_policy_effective_on_loss_date(make_policy(), loss_dt)


def test_validate_policy_against_claim_aggregates_consistency_only():
    claim = ClaimData(
        claim_number="CLM-1",
        policy_number="POL-123456",
        veh_info=VehInfo(vehicle_plate="ABCD12"),
        claims_occurrence=ClaimsOccurrence(loss_dt=date(2026, 6, 1)),
    )

    result = validate_policy_against_claim(claim, make_policy())

    assert result.model_dump() == {
        "policy_number_matches": True,
        "vehicle_matches": True,
        "policy_active_on_loss_dt": True,
    }
