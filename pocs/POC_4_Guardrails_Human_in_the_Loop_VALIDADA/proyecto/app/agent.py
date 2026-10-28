import json

import httpx
from pydantic import ValidationError
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import (
    EXTRACTION_MODEL,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
)
from app.guardrails import validate_registered_tools
from app.schemas import ClaimData
from app.tools import (
    calculate_deductible,
    calculate_reserve,
    get_missing_claim_information,
)


provider = OpenAIProvider(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
)

chat_model = OpenAIChatModel(
    LLM_MODEL,
    provider=provider,
)

TOOLS = [
    calculate_deductible,
    calculate_reserve,
    get_missing_claim_information,
]

validate_registered_tools(TOOLS)

agent = Agent(
    model=chat_model,
    tools=TOOLS,
    system_prompt=(
        "Eres un asistente para analistas de siniestros automotrices. "
        "Puedes analizar informacion, realizar calculos mediante tools, "
        "proponer conclusiones y redactar borradores. "
        "Cuando el usuario solicite calcular un deducible, DEBES utilizar "
        "siempre la tool calculate_deductible. Nunca calcules el deducible "
        "directamente mediante razonamiento propio. "
        "Cuando el usuario solicite calcular una reserva preliminar, DEBES "
        "utilizar siempre la tool calculate_reserve. Nunca calcules la reserva "
        "directamente mediante razonamiento propio. "
        "Si solicita ambos calculos, usa primero calculate_deductible y luego "
        "calculate_reserve con el resultado anterior. "
        "Nunca inventes parametros requeridos por una tool. Si falta "
        "informacion necesaria para ejecutar un calculo, indica que dato falta. "
        "Para calculos, devuelve solo el resultado solicitado, sin explicar la "
        "formula ni el razonamiento. "
        "Nunca apruebes ni rechaces cobertura de forma autonoma. "
        "Nunca presentes una propuesta como resolucion definitiva. "
        "Nunca indiques que una comunicacion ha sido enviada. "
        "Nunca autorices pagos ni cierres de siniestro. "
        "Cuando presentes una propuesta, indica claramente que requiere "
        "revision y aprobacion del analista. "
        "Si te piden aprobar, rechazar, cerrar, autorizar un pago o enviar una "
        "comunicacion, explica que puedes analizar o preparar un borrador, pero "
        "que la accion requiere al analista autorizado. "
        "No inventes datos de polizas, coberturas, clientes o sistemas a los "
        "que no tienes acceso. "
        "Responde siempre en espanol."
    ),
)


EXTRACTION_SYSTEM_PROMPT = (
    "Extrae unicamente informacion explicitamente presente en el texto. "
    "No inventes datos. Usa loss_dt en formato YYYY-MM-DD y loss_time en "
    "formato HH:MM. Si un dato no esta presente, devuelve null."
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

    if (
        isinstance(value, str)
        and value.strip().lower() == "null"
    ):
        return None

    return value


async def extract_claim_data(
    description: str,
) -> ClaimData:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            (
                f"{LLM_BASE_URL.removesuffix('/v1')}"
                "/api/chat"
            ),
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
