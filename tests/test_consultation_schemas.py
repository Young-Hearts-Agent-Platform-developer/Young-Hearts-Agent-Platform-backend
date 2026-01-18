from app.schemas.consultation import (
    ConsultationSession,
    ConsultationSessionCreate,
    ConsultationMessage,
    ConsultationMessageCreate,
)
from datetime import datetime

def test_consultation_session_schema():
    data = {
        "id": 1,
        "user_id": 2,
        "topic": "test topic",
        "created_at": datetime.utcnow(),
        "is_archived": False,
        "messages": [],
    }
    session = ConsultationSession(**data)
    assert session.id == 1
    assert session.user_id == 2
    assert session.topic == "test topic"
    assert session.is_archived is False
    assert session.messages == []

def test_consultation_message_schema():
    data = {
        "id": 1,
        "session_id": 1,
        "role": "user",
        "content": "hello",
        "sources": None,
        "created_at": datetime.utcnow(),
    }
    msg = ConsultationMessage(**data)
    assert msg.id == 1
    assert msg.session_id == 1
    assert msg.role == "user"
    assert msg.content == "hello"
