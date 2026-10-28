from app.conversation_context import build_conversation_context
from app.conversation_memory import utc_now
from app.schemas import ConversationMessage, ConversationSession


def test_context_contains_summary_and_recent_messages():
    session = ConversationSession(
        session_id="11111111-1111-1111-1111-111111111111",
        created_at=utc_now(),
        updated_at=utc_now(),
        summary="El analista está revisando el accidente.",
        messages=[
            ConversationMessage(
                role="user",
                content="¿Dónde ocurrió?",
                created_at=utc_now(),
            ),
        ],
    )
    context = build_conversation_context(session)
    assert "Conversation summary" in context
    assert "¿Dónde ocurrió?" in context
