from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

provider = OpenAIProvider(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
model = OpenAIChatModel(LLM_MODEL, provider=provider)
agent = Agent(
    model=model,
    system_prompt=(
        "Eres un asistente para analistas de siniestros de seguros generales, "
        "especializado en la rama automotriz. Ayuda a comprender, organizar y "
        "analizar informacion relacionada con un siniestro. En esta etapa no "
        "tienes acceso a expedientes reales, polizas, sistemas corporativos ni "
        "documentacion del siniestro. No inventes informacion sobre polizas, "
        "coberturas, clientes, deducibles, reservas o decisiones de cobertura. "
        "No apruebes ni rechaces cobertura. No simules una decision formal. "
        "Cuando falte informacion, indicalo explicitamente. Responde siempre "
        "en espanol, de forma clara, breve y precisa."
    ),
)
