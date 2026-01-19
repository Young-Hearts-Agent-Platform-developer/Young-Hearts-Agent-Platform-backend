
from typing import List, Optional, Any
from sqlalchemy.orm import Session
from app.models.consultation import ConsultationSession, ConsultationMessage
from app.schemas.consultation import ConsultationSessionCreate, ConsultationMessageCreate
from app.models.user import User
from app.db.session import get_db
from sqlalchemy import desc
from fastapi import HTTPException
from app.services.auth import is_admin
from app.rag.service import generate_topic

class ConsultationService:
    def __init__(self, db: Session):
        self.db = db

    def get_session(self, session_id: int) -> Optional[ConsultationSession]:
        """
        根据 session_id 查询 ConsultationSession，不做权限校验，仅供内部使用。
        """
        return self.db.query(ConsultationSession).filter(ConsultationSession.id == session_id).first()

    def create_session(self, user_id: int, topic: str) -> ConsultationSession:
        session = ConsultationSession(user_id=user_id, topic=topic)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def list_sessions_recent(self, user_id: int, roles: List[str]) -> List[ConsultationSession]:
        query = self.db.query(ConsultationSession)
        if not is_admin(roles):
            query = query.filter(ConsultationSession.user_id == user_id)
        query = query.order_by(desc(ConsultationSession.created_at))
        return query.limit(20).all()

    def get_session_detail(self, session_id: int, user_id: int, roles: List[str]) -> ConsultationSession:
        session = self.db.query(ConsultationSession).filter(ConsultationSession.id == session_id).first()
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if not is_admin(roles) and getattr(session, "user_id", None) != user_id:
            raise HTTPException(status_code=403, detail="Permission denied")
        return session

    def save_message(self, session_id: int, role: str, content: str, sources: Optional[Any] = None) -> ConsultationMessage:
        message = ConsultationMessage(session_id=session_id, role=role, content=content, sources=sources)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def save_ai_message_and_generate_topic(self, session_id: int, ai_content: str, user_content: Optional[str] = None, sources: Optional[Any] = None) -> ConsultationMessage:
        """
        保存 AI 消息，并在首次 AI 回复后自动生成 topic
        :param session_id: 会话ID
        :param ai_content: AI 回复内容
        :param user_content: 用户首次提问内容（仅首次AI回复时需传入）
        :param sources: RAG 源
        :return: ConsultationMessage
        """
        session = self.db.query(ConsultationSession).filter(ConsultationSession.id == session_id).first()
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        # 获取当前 topic 值，避免直接用 Column 对象
        current_topic = getattr(session, 'topic', None)
        if isinstance(current_topic, str):
            topic_value = current_topic
        else:
            topic_value = None
        # 判断是否首次生成 topic
        if (topic_value is None) or (topic_value == "新对话"):
            # 需有用户首次提问内容
            if not user_content:
                # 查找该 session 的第一条 user 消息
                first_user_msg = self.db.query(ConsultationMessage).filter(
                    ConsultationMessage.session_id == session_id,
                    ConsultationMessage.role == "user"
                ).order_by(ConsultationMessage.created_at.asc()).first()
                if first_user_msg:
                    msg_content = getattr(first_user_msg, 'content', None)
                    user_content = msg_content if isinstance(msg_content, str) else None
                else:
                    user_content = ""
            # 生成 topic
            safe_user_content = user_content if user_content is not None else ""
            safe_ai_content = ai_content if ai_content is not None else ""
            topic = generate_topic(safe_user_content, safe_ai_content)
            # 通过 setattr 赋值，避免直接赋值 Column
            setattr(session, 'topic', topic)
            self.db.commit()
        # 保存 AI 消息
        message = ConsultationMessage(session_id=session_id, role="ai", content=ai_content, sources=sources)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def list_messages_all(self, session_id: int, user_id: int, roles: List[str]) -> List[ConsultationMessage]:
        session = self.get_session_detail(session_id, user_id, roles)
        query = self.db.query(ConsultationMessage).filter(ConsultationMessage.session_id == session_id)
        query = query.order_by(desc(ConsultationMessage.created_at))
        return query.all()

    def delete_session(self, session_id: int, user_id: int, roles: List[str]) -> None:
        session = self.db.query(ConsultationSession).filter(ConsultationSession.id == session_id).first()
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if not is_admin(roles) and getattr(session, "user_id", None) != user_id:
            raise HTTPException(status_code=403, detail="Permission denied")
        self.db.delete(session)
        self.db.commit()
