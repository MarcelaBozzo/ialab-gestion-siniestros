import json

import httpx
from pydantic import ValidationError
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import EXTRACTION_MODEL, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from app.schemas import ClaimData
from app.tools import calculate_deductible, calculate_reserve, get_missing_claim_information


provider = OpenAIProvider(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
)

chat_model = OpenAIChatModel(
    LLM_MODEL,
    provider=provider,
)

agent = Agent(
    model=chat_model,
    tools=[calculate_deductible, calculate_reserve, get_missing_claim_information],
    system_prompt=(
        "Eres un asistente para analistas de siniestros automotrices. "
        "Para deducible usa siempre calculate_deductible y para reserva usa siempre calculate_reserve. "
        "Nunca inventes parametros requeridos por una tool. Si falta un parametro, indica cual falta. "
        "No determines cobertura, no apruebes ni rechaces siniestros. Responde siempre en espanol."
    ),
)


EXTRACTION_SYSTEM_PROMPT = (
    "Extrae únicamente información explícitamente presente "
    "en el texto. No inventes datos. "
    "Usa loss_dt en formato YYYY-MM-DD y "
    "loss_time en formato HH:MM. "
    "Si un dato no está presente, devuelve null."
)


EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "policy_number": {
            "type": ["string", "null"],
        },
        "claims_occurrence": {
            "type": "object",
            "properties": {
                "loss_dt": {
                    "type": ["string", "null"],
                },
                "loss_time": {
                    "type": ["string", "null"],
                },
                "loss_desc": {
                    "type": ["string", "null"],
                },
                "loss_location_desc": {
                    "type": ["string", "null"],
                },
            },
            "required": [
                "loss_dt",
                "loss_time",
                "loss_desc",
                "loss_location_desc",
            ],
        },
        "veh_info": {
            "type": "object",
            "properties": {
                "vehicle_plate": {
                    "type": ["string", "null"],
                },
                "manufacturer": {
                    "type": ["string", "null"],
                },
                "model": {
                    "type": ["string", "null"],
                },
            },
            "required": [
                "vehicle_plate",
                "manufacturer",
                "model",
            ],
        },
    },
    "required": [
        "policy_number",
        "claims_occurrence",
        "veh_info",
    ],
}


def _normalize_null_strings(value):
    if isinstance(value, dict):
        return {
            key: _normalize_null_strings(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _normalize_null_strings(item)
            for item in value
        ]

    if isinstance(value, str) and value.strip().lower() == "null":
        return None

    return value


async def extract_claim_data(description: str) -> ClaimData:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{LLM_BASE_URL.removesuffix('/v1')}/api/chat",
            json={
                "model": EXTRACTION_MODEL,
                "stream": False,
                "messages": [
                    {
                        "role": "system",
                        "content": EXTRACTION_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": description,
                    },
                ],
                "format": EXTRACTION_SCHEMA,
                "options": {
                    "temperature": 0,
                },
            },
        )
        response.raise_for_status()

    try:
        content = response.json()["message"]["content"]
        data = json.loads(content)
        normalized_data = _normalize_null_strings(data)
        return ClaimData.model_validate(normalized_data)
    except (
        KeyError,
        TypeError,
        json.JSONDecodeError,
        ValidationError,
    ) as exc:
        raise ValueError(
            "The extraction model returned invalid structured data"
        ) from exc
