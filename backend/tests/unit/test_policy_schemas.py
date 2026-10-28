from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas import (
    Coverage,
    Policy,
    PolicySearchResult,
    PolicyValidationResult,
    VehInfo,
)


def test_policy_keeps_previous_contract_compatible():
    policy = Policy(
        policy_number="POL-123456",
        policy_status_cd="ACTIVE",
        effective_date=date(2026, 1, 1),
        expiration_date=date(2026, 12, 31),
    )

    assert policy.product_code is None
    assert policy.insured_vehicle is None
    assert policy.coverages == []
    assert policy.source_system == "policy_core"
    assert policy.retrieved_at is None


def test_policy_accepts_poc_12_domain_fields():
    retrieved_at = datetime(2026, 10, 28, tzinfo=timezone.utc)
    policy = Policy(
        policy_number="POL-123456",
        policy_status_cd="ACTIVE",
        effective_date=date(2026, 1, 1),
        expiration_date=date(2026, 12, 31),
        product_code="AUTO_STANDARD",
        product_name="Auto Standard",
        insured_customer_id="CUS-123",
        insured_vehicle=VehInfo(vehicle_plate="ABCD12"),
        coverages=[
            Coverage(
                coverage_cd="COLLISION",
                deductible_amount=Decimal("150000"),
            )
        ],
        retrieved_at=retrieved_at,
    )

    assert isinstance(policy.insured_vehicle, VehInfo)
    assert policy.product_name == "Auto Standard"
    assert policy.insured_customer_id == "CUS-123"
    assert policy.coverages[0].deductible_amount == Decimal("150000")
    assert policy.retrieved_at == retrieved_at


@pytest.mark.parametrize(
    ("policy_found", "policy_number"),
    [(True, "POL-123456"), (False, None)],
)
def test_policy_search_result_accepts_consistent_values(
    policy_found,
    policy_number,
):
    result = PolicySearchResult(
        policy_found=policy_found,
        policy_number=policy_number,
    )

    assert result.policy_found is policy_found
    assert result.policy_number == policy_number


@pytest.mark.parametrize(
    ("policy_found", "policy_number"),
    [(True, None), (False, "POL-123456")],
)
def test_policy_search_result_rejects_inconsistent_values(
    policy_found,
    policy_number,
):
    with pytest.raises(ValidationError):
        PolicySearchResult(
            policy_found=policy_found,
            policy_number=policy_number,
        )


def test_policy_validation_result_defaults_to_unknown():
    result = PolicyValidationResult()

    assert result.policy_number_matches is None
    assert result.vehicle_matches is None
    assert result.policy_active_on_loss_dt is None
