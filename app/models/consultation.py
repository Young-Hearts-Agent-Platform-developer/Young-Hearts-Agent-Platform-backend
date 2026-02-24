
from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models import Base


class ConsultationSession(Base):
    __tablename__ = "consultation_sessions"
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(255), nullable=True)  # 会话主题，可为空，首次 AI 回复后自动生成，可更新
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_archived = Column(Boolean, default=False)

    messages = relationship("ConsultationMessage", back_populates="session", lazy="noload", cascade="all, delete-orphan")


class ConsultationMessage(Base):
    __tablename__ = "consultation_messages"
    id = Column(BigInteger, primary_key=True, index=True)
    session_id = Column(BigInteger, ForeignKey("consultation_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # 枚举，user/ai
    content = Column(Text, nullable=False)  # Markdown 格式内容
    sources = Column(Text, nullable=True)  # (RAG 引用来源: [{title, id, score}])
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("ConsultationSession", back_populates="messages")
