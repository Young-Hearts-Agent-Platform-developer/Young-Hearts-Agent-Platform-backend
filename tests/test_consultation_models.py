import pytest
from app.models.consultation import ConsultationSession, ConsultationMessage
from datetime import datetime


def test_consultation_session_fields():
    session = ConsultationSession(
        id=1,
        user_id=2,
        topic="test topic",
        created_at=datetime.utcnow(),
        is_archived=False
    )
    assert getattr(session, "id") == 1
    assert getattr(session, "user_id") == 2
    assert getattr(session, "topic") == "test topic"
    assert getattr(session, "is_archived") is False


def test_consultation_message_fields():
    msg = ConsultationMessage(
        id=1,
        session_id=1,
        role="user",
        content="hello",
        sources=None,
        created_at=datetime.utcnow()
    )
    assert getattr(msg, "id") == 1
    assert getattr(msg, "session_id") == 1
    assert getattr(msg, "role") == "user"
    assert getattr(msg, "content") == "hello"
