import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.policy_client import normalize_vehicle_plate
from app.schemas import Policy


app = FastAPI(title="Policy Core Mock")

policies_path = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "policies"
    / "policies.json"
)

with policies_path.open(encoding="utf-8") as file:
    policies = {
        policy["policy_number"]: Policy.model_validate(policy)
        for policy in json.load(file)
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/policies/by-vehicle/{vehicle_plate}")
async def find_policy_by_vehicle(vehicle_plate: str) -> dict[str, str]:
    normalized_plate = normalize_vehicle_plate(vehicle_plate)
    matches = [
        policy
        for policy in policies.values()
        if policy.insured_vehicle is not None
        and policy.insured_vehicle.vehicle_plate is not None
        and normalize_vehicle_plate(policy.insured_vehicle.vehicle_plate)
        == normalized_plate
    ]

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="Policy not found",
        )

    if len(matches) > 1:
        raise HTTPException(
            status_code=409,
            detail="Policy lookup is ambiguous",
        )

    return {"policy_number": matches[0].policy_number}


@app.get(
    "/policies/{policy_number}",
    response_model=Policy,
)
async def get_policy(policy_number: str) -> Policy:
    policy = policies.get(policy_number)
    if policy is None:
        raise HTTPException(
            status_code=404,
            detail="Policy not found",
        )

    return policy
