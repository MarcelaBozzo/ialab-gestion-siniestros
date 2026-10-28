import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

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
