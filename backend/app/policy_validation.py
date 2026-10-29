from datetime import date, datetime

from app.policy_client import (
    normalize_policy_number,
    normalize_vehicle_plate,
)
from app.schemas import (
    ClaimData,
    Policy,
    PolicySearchResult,
    PolicyValidationResult,
)


def validate_policy_exists(search_result: PolicySearchResult) -> bool:
    return search_result.policy_found


def validate_policy_number_match(
    claim_data: ClaimData,
    policy: Policy,
) -> bool | None:
    if not claim_data.policy_number:
        return None

    return normalize_policy_number(
        claim_data.policy_number
    ) == normalize_policy_number(policy.policy_number)


def validate_policy_vehicle_match(
    claim_data: ClaimData,
    policy: Policy,
) -> bool | None:
    claim_vehicle = claim_data.veh_info
    policy_vehicle = policy.insured_vehicle

    if (
        claim_vehicle is None
        or policy_vehicle is None
        or not claim_vehicle.vehicle_plate
        or not policy_vehicle.vehicle_plate
    ):
        return None

    return normalize_vehicle_plate(
        claim_vehicle.vehicle_plate
    ) == normalize_vehicle_plate(policy_vehicle.vehicle_plate)


def is_policy_effective_on_loss_date(
    policy: Policy,
    loss_dt: date | datetime,
) -> bool:
    loss_date = loss_dt.date() if isinstance(loss_dt, datetime) else loss_dt
    return policy.effective_date <= loss_date <= policy.expiration_date


def validate_policy_active_on_loss_date(
    claim_data: ClaimData,
    policy: Policy,
) -> bool | None:
    occurrence = claim_data.claims_occurrence

    if occurrence is None or occurrence.loss_dt is None:
        return None

    return is_policy_effective_on_loss_date(policy, occurrence.loss_dt)


def validate_policy_against_claim(
    claim_data: ClaimData,
    policy: Policy,
) -> PolicyValidationResult:
    return PolicyValidationResult(
        policy_number_matches=validate_policy_number_match(
            claim_data,
            policy,
        ),
        vehicle_matches=validate_policy_vehicle_match(
            claim_data,
            policy,
        ),
        policy_active_on_loss_dt=validate_policy_active_on_loss_date(
            claim_data,
            policy,
        ),
    )
