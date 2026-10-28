from types import SimpleNamespace

import pytest

from app import conversation_memory, conversation_service
from app.schemas import GuardrailDecision, RequestClassification


async def allow_input(_message):
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
async def test_failed_agent_call_does_not_persist_turn(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_memory, "CONVERSATION_STORAGE_PATH", tmp_path)
    monkeypatch.setattr(conversation_service, "validate_input", allow_input)

    async def failing_run(prompt):
        raise RuntimeError("Agent unavailable")

    monkeypatch.setattr(conversation_service.agent, "run", failing_run)
    session = conversation_memory.create_session()

    with pytest.raises(RuntimeError):
        await conversation_service.process_conversation_turn(
            session_id=session.session_id,
            message="Hola",
        )

    persisted = conversation_memory.get_session(session.session_id)
    assert persisted is not None
    assert persisted.messages == []


@pytest.mark.asyncio
async def test_summary_failure_keeps_response_and_turn(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_memory, "CONVERSATION_STORAGE_PATH", tmp_path)
    monkeypatch.setattr(conversation_memory, "CONVERSATION_SUMMARY_TRIGGER", 2)
    monkeypatch.setattr(conversation_memory, "CONVERSATION_RECENT_MESSAGES", 1)
    monkeypatch.setattr(conversation_service, "validate_input", allow_input)
    monkeypatch.setattr(conversation_service, "validate_output", allow_output)

    async def successful_run(prompt):
        return SimpleNamespace(output="Respuesta conservada")

    async def failing_summary(messages, existing_summary=None):
        raise RuntimeError("Summarizer unavailable")

    monkeypatch.setattr(conversation_service.agent, "run", successful_run)
    monkeypatch.setattr(conversation_memory, "summarize_conversation", failing_summary)

    session = conversation_memory.create_session()
    response = await conversation_service.process_conversation_turn(
        session_id=session.session_id,
        message="Pregunta",
    )

    assert response == "Respuesta conservada"
    persisted = conversation_memory.get_session(session.session_id)
    assert persisted is not None
    assert len(persisted.messages) == 2
    assert persisted.summary is None
