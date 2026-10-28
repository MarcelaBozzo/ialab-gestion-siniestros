from decimal import Decimal
from app.schemas import DeductibleCalculation, ReserveCalculation

def calculate_deductible(loss_amount: Decimal, deductible_percentage: Decimal, minimum_deductible: Decimal) -> DeductibleCalculation:
    percentage_amount = loss_amount * deductible_percentage / Decimal("100")
    calculated_deductible = min(max(percentage_amount, minimum_deductible), loss_amount)
    return DeductibleCalculation(
        loss_amount=loss_amount,
        deductible_percentage=deductible_percentage,
        minimum_deductible=minimum_deductible,
        calculated_deductible=calculated_deductible,
    )

def calculate_reserve(estimated_loss_amount: Decimal, deductible_amount: Decimal) -> ReserveCalculation:
    calculated_reserve = max(estimated_loss_amount - deductible_amount, Decimal("0"))
    return ReserveCalculation(
        estimated_loss_amount=estimated_loss_amount,
        deductible_amount=deductible_amount,
        calculated_reserve=calculated_reserve,
    )

def get_missing_claim_information(loss_dt: str | None = None, loss_desc: str | None = None, policy_number: str | None = None, vehicle_plate: str | None = None) -> list[str]:
    missing = []
    if not loss_dt: missing.append("LossDt")
    if not loss_desc: missing.append("LossDesc")
    if not policy_number: missing.append("PolicyNumber")
    if not vehicle_plate: missing.append("vehicle_plate")
    return missing
