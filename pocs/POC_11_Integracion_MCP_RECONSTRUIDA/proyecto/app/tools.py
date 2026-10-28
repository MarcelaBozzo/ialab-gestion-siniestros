from decimal import Decimal
from typing import Literal

from app.schemas import (
    DeductibleCalculation,
    ReserveCalculation,
)


def calculate_deductible(
    loss_amount: Decimal,
    deductible_percentage: Decimal,
    minimum_deductible: Decimal,
) -> DeductibleCalculation:
    percentage_amount = (
        loss_amount
        * deductible_percentage
        / Decimal("100")
    )

    calculated_deductible = max(
        percentage_amount,
        minimum_deductible,
    )

    calculated_deductible = min(
        calculated_deductible,
        loss_amount,
    )

    return DeductibleCalculation(
        loss_amount=loss_amount,
        deductible_percentage=deductible_percentage,
        minimum_deductible=minimum_deductible,
        calculated_deductible=calculated_deductible,
    )


def calculate_reserve(
    estimated_loss_amount: Decimal,
    deductible_amount: Decimal,
) -> ReserveCalculation:
    calculated_reserve = max(
        estimated_loss_amount - deductible_amount,
        Decimal("0"),
    )

    return ReserveCalculation(
        estimated_loss_amount=estimated_loss_amount,
        deductible_amount=deductible_amount,
        calculated_reserve=calculated_reserve,
    )


def get_missing_claim_information(
    loss_dt: str | None = None,
    loss_desc: str | None = None,
    policy_number: str | None = None,
    vehicle_plate: str | None = None,
) -> list[str]:
    missing: list[str] = []

    if not loss_dt:
        missing.append("LossDt")
    if not loss_desc:
        missing.append("LossDesc")
    if not policy_number:
        missing.append("PolicyNumber")
    if not vehicle_plate:
        missing.append("vehicle_plate")

    return missing


async def verify_customer_tool(national_id: str):
    """Verifica si el declarante es cliente. No recupera PII adicional."""
    from app.customer_service import verify_claimant_customer
    return await verify_claimant_customer(national_id)


async def get_customer_profile_tool(
    national_id: str,
    requested_field: Literal["email", "phone_number", "address"],
):
    """Devuelve solo el dato personal solicitado del declarante."""
    from app.customer_service import get_claimant_customer_profile
    return await get_claimant_customer_profile(national_id, requested_field)
