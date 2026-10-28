from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


def build_chat_model() -> OpenAIChatModel:
    provider = OpenAIProvider(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
    )
    return OpenAIChatModel(
        LLM_MODEL,
        provider=provider,
    )


chat_model = build_chat_model()
