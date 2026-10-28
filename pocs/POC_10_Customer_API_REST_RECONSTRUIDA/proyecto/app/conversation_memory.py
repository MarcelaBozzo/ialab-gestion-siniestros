import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from app.config import (
    CONVERSATION_RECENT_MESSAGES,
    CONVERSATION_STORAGE_PATH,
    CONVERSATION_SUMMARY_TRIGGER,
)
from app.conversation_summary import summarize_conversation
from app.schemas import ConversationMessage, ConversationSession


class ConversationSessionNotFoundError(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_session_id(session_id: str) -> None:
    try:
        uuid.UUID(session_id)
    except ValueError as exc:
        raise ValueError("Invalid session_id") from exc


def get_session_path(session_id: str) -> Path:
    validate_session_id(session_id)
    return CONVERSATION_STORAGE_PATH / f"{session_id}.json"


def ensure_session_storage() -> None:
    CONVERSATION_STORAGE_PATH.mkdir(parents=True, exist_ok=True)


def create_session(claim_number: str | None = None) -> ConversationSession:
    ensure_session_storage()
    now = utc_now()
    session = ConversationSession(
        session_id=str(uuid.uuid4()),
        claim_number=claim_number,
        created_at=now,
        updated_at=now,
        summary=None,
        messages=[],
    )
    save_session(session)
    return session


def save_session(session: ConversationSession) -> None:
    ensure_session_storage()
    session.updated_at = utc_now()
    path = get_session_path(session.session_id)
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(
        session.model_dump_json(indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(path)


def get_session(session_id: str) -> ConversationSession | None:
    path = get_session_path(session_id)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return ConversationSession.model_validate(data)


def delete_session(session_id: str) -> bool:
    path = get_session_path(session_id)
    if not path.is_file():
        return False
    path.unlink()
    return True


def append_message(
    session_id: str,
    role: Literal["user", "assistant"],
    content: str,
) -> ConversationSession:
    session = get_session(session_id)
    if session is None:
        raise ConversationSessionNotFoundError(
            "Conversation session not found"
        )
    message = ConversationMessage(
        role=role,
        content=content,
        created_at=utc_now(),
    )
    session.messages.append(message)
    save_session(session)
    return session


def get_recent_messages(
    session: ConversationSession,
    limit: int,
) -> list[ConversationMessage]:
    if limit <= 0:
        return []
    return session.messages[-limit:]


async def compact_session_if_needed(
    session: ConversationSession,
) -> ConversationSession:
    if len(session.messages) < CONVERSATION_SUMMARY_TRIGGER:
        return session

    keep = CONVERSATION_RECENT_MESSAGES
    if keep <= 0:
        raise ValueError(
            "CONVERSATION_RECENT_MESSAGES must be greater than zero"
        )

    older_messages = session.messages[:-keep]
    recent_messages = session.messages[-keep:]
    if not older_messages:
        return session

    summary = await summarize_conversation(
        messages=older_messages,
        existing_summary=session.summary,
    )
    session.summary = summary
    session.messages = recent_messages
    save_session(session)
    return session
