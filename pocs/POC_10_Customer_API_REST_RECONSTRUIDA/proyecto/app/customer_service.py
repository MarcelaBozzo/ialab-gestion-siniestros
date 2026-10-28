from typing import Literal
from app.customer_client import (
    CustomerApiError, CustomerNotFound, get_customer_profile, normalize_national_id, verify_customer,
)
from app.schemas import CustomerFieldValue, CustomerVerification

async def verify_claimant_customer(national_id: str) -> CustomerVerification:
    return await verify_customer(national_id)

async def get_claimant_customer_profile(
    national_id: str,
    requested_field: Literal["email", "phone_number", "address"],
) -> CustomerFieldValue:
    verification = await verify_customer(national_id)
    if not verification.customer_found or not verification.customer_id:
        raise CustomerNotFound("Claimant is not a customer")
    profile = await get_customer_profile(verification.customer_id, requested_field)
    if normalize_national_id(profile.national_id) != normalize_national_id(national_id):
        raise CustomerApiError("Customer profile does not match the claimant")
    return CustomerFieldValue(requested_field=requested_field, value=getattr(profile, requested_field))
