import json
from pathlib import Path

DEMO_CONTEXT_PATH = Path(__file__).resolve().parents[1] / "data" / "demo_claim_context.json"

def get_demo_claim_context(claim_number: str | None) -> dict:
    if not claim_number or not DEMO_CONTEXT_PATH.is_file():
        return {}
    data = json.loads(DEMO_CONTEXT_PATH.read_text(encoding="utf-8"))
    value = data.get(claim_number, {})
    return value if isinstance(value, dict) else {}
