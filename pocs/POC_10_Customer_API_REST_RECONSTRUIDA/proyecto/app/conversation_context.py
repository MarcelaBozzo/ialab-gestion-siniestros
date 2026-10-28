from app.config import CONVERSATION_RECENT_MESSAGES
from app.conversation_memory import get_recent_messages
from app.schemas import ConversationSession


def build_conversation_context(session: ConversationSession) -> str:
    parts: list[str] = []

    if session.summary:
        parts.append(f"Conversation summary:\n{session.summary}")

    recent = get_recent_messages(session, CONVERSATION_RECENT_MESSAGES)
    if recent:
        lines = [
            f"{message.role}: {message.content}"
            for message in recent
        ]
        parts.append("Recent conversation:\n" + "\n".join(lines))

    return "\n\n".join(parts)
