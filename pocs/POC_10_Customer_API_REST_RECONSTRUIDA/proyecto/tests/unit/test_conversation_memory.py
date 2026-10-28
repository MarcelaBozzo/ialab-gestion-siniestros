import pytest

from app import conversation_memory
from app.conversation_memory import get_recent_messages, utc_now
from app.schemas import ConversationMessage, ConversationSession


def test_create_session(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_memory, "CONVERSATION_STORAGE_PATH", tmp_path)
    session = conversation_memory.create_session(claim_number="CLM-000123")
    assert session.session_id
    assert session.claim_number == "CLM-000123"
    assert session.messages == []
    path = conversation_memory.get_session_path(session.session_id)
    assert path.is_file()


def test_session_can_be_loaded(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_memory, "CONVERSATION_STORAGE_PATH", tmp_path)
    created = conversation_memory.create_session(claim_number="CLM-000123")
    loaded = conversation_memory.get_session(created.session_id)
    assert loaded is not None
    assert loaded.session_id == created.session_id


def test_append_message(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_memory, "CONVERSATION_STORAGE_PATH", tmp_path)
    session = conversation_memory.create_session()
    conversation_memory.append_message(
        session_id=session.session_id,
        role="user",
        content="Hola",
    )
    loaded = conversation_memory.get_session(session.session_id)
    assert loaded is not None
    assert len(loaded.messages) == 1
    assert loaded.messages[0].content == "Hola"


def test_sessions_are_isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_memory, "CONVERSATION_STORAGE_PATH", tmp_path)
    session_a = conversation_memory.create_session()
    session_b = conversation_memory.create_session()
    conversation_memory.append_message(
        session_id=session_a.session_id,
        role="user",
        content="Mensaje A",
    )
    loaded_b = conversation_memory.get_session(session_b.session_id)
    assert loaded_b is not None
    assert loaded_b.messages == []


def test_get_recent_messages():
    session = ConversationSession(
        session_id="11111111-1111-1111-1111-111111111111",
        created_at=utc_now(),
        updated_at=utc_now(),
        messages=[
            ConversationMessage(
                role="user",
                content=f"Message {index}",
                created_at=utc_now(),
            )
            for index in range(10)
        ],
    )
    recent = get_recent_messages(session, limit=3)
    assert len(recent) == 3
    assert recent[0].content == "Message 7"


@pytest.mark.asyncio
async def test_compact_session_summarizes_old_messages(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_memory, "CONVERSATION_STORAGE_PATH", tmp_path)
    monkeypatch.setattr(conversation_memory, "CONVERSATION_SUMMARY_TRIGGER", 4)
    monkeypatch.setattr(conversation_memory, "CONVERSATION_RECENT_MESSAGES", 2)

    async def fake_summarize(messages, existing_summary=None):
        assert len(messages) == 2
        assert existing_summary is None
        return "Se conversó sobre los mensajes iniciales."

    monkeypatch.setattr(conversation_memory, "summarize_conversation", fake_summarize)
    session = conversation_memory.create_session()
    for index in range(4):
        conversation_memory.append_message(
            session_id=session.session_id,
            role="user",
            content=f"Message {index}",
        )

    current = conversation_memory.get_session(session.session_id)
    assert current is not None
    compacted = await conversation_memory.compact_session_if_needed(current)
    assert compacted.summary == "Se conversó sobre los mensajes iniciales."
    assert [message.content for message in compacted.messages] == [
        "Message 2",
        "Message 3",
    ]
    persisted = conversation_memory.get_session(session.session_id)
    assert persisted is not None
    assert persisted.summary == compacted.summary
    assert len(persisted.messages) == 2
