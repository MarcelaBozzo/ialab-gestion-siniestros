from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app import conversation_memory, conversation_service
from app.schemas import GuardrailDecision, RequestClassification


async def allow_input(_message, conversation_context=None):
    return GuardrailDecision(
        classification=RequestClassification.IN_SCOPE,
        reason="test",
    )


async def allow_output(_message):
    return GuardrailDecision(
        classification=RequestClassification.IN_SCOPE,
        reason="test",
    )


@pytest.mark.asyncio
async def test_conversation_remembers_previous_turn(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_memory, "CONVERSATION_STORAGE_PATH", tmp_path)
    monkeypatch.setattr(conversation_service, "validate_input", allow_input)
    monkeypatch.setattr(conversation_service, "validate_output", allow_output)
    monkeypatch.setattr(
        conversation_service,
        "load_claim_data_json",
        AsyncMock(return_value=None),
    )

    async def conversational_run(prompt):
        response = (
            "Dijimos que ocurrió en Providencia."
            if "Providencia" in prompt
            else "Entendido."
        )
        return SimpleNamespace(output=response)

    monkeypatch.setattr(
        conversation_service.agent,
        "run",
        conversational_run,
    )
    session = conversation_memory.create_session(claim_number="CLM-000123")

    await conversation_service.process_conversation_turn(
        session_id=session.session_id,
        message="El accidente que estamos comentando ocurrió en Providencia.",
    )
    response = await conversation_service.process_conversation_turn(
        session_id=session.session_id,
        message="¿Dónde dijimos que ocurrió?",
    )

    assert "providencia" in response.casefold()
    loaded = conversation_memory.get_session(session.session_id)
    assert loaded is not None
    assert len(loaded.messages) == 4


@pytest.mark.asyncio
async def test_unknown_session_fails():
    with pytest.raises(ValueError):
        await conversation_service.process_conversation_turn(
            session_id="11111111-1111-1111-1111-111111111111",
            message="Hola",
        )
