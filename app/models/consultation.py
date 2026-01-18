from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.models import Base

class ConsultationSession(Base):
    __tablename__ = "consultation_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_archived = Column(Boolean, default=False)

    messages = relationship("ConsultationMessage", back_populates="session")

class ConsultationMessage(Base):
    __tablename__ = "consultation_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("consultation_sessions.id"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # 枚举，user/ai
    content = Column(Text, nullable=False)  # Markdown 格式内容
    sources = Column(Text, nullable=True)  # (RAG 引用来源: [{title, id, score}])
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("ConsultationSession", back_populates="messages")
