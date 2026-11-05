from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app import conversation_memory, conversation_service
from app.a2a.errors import A2AAgentUnavailable
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
async def test_failed_agent_call_does_not_persist_turn(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_memory, "CONVERSATION_STORAGE_PATH", tmp_path)
    monkeypatch.setattr(conversation_service, "validate_input", allow_input)

    async def failing_run(prompt, deps=None):
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

    async def successful_run(prompt, deps=None):
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


@pytest.mark.asyncio
async def test_a2a_unavailable_returns_controlled_response_and_keeps_turn(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(conversation_memory, "CONVERSATION_STORAGE_PATH", tmp_path)
    monkeypatch.setattr(conversation_service, "validate_input", allow_input)
    monkeypatch.setattr(
        conversation_service.agent,
        "run",
        AsyncMock(side_effect=A2AAgentUnavailable("offline")),
    )
    session = conversation_memory.create_session(claim_number="CLM-000123")

    response = await conversation_service.process_conversation_turn(
        session_id=session.session_id,
        message="Analiza la cobertura",
    )

    assert response == conversation_service.A2A_UNAVAILABLE_RESPONSE
    persisted = conversation_memory.get_session(session.session_id)
    assert persisted is not None
    assert [message.role for message in persisted.messages] == [
        "user",
        "assistant",
    ]
