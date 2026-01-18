
from typing import List, Optional, Any
from sqlalchemy.orm import Session
from app.models.consultation import ConsultationSession, ConsultationMessage
from app.schemas.consultation import ConsultationSessionCreate, ConsultationMessageCreate
from app.models.user import User
from app.db.session import get_db
from sqlalchemy import desc
from fastapi import HTTPException
from app.services.auth import is_admin



class ConsultationService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, user_id: int, topic: str) -> ConsultationSession:
        session = ConsultationSession(user_id=user_id, topic=topic)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def list_sessions(self, user_id: int, roles: List[str], page: int = 1, size: int = 20) -> List[ConsultationSession]:
        query = self.db.query(ConsultationSession)
        if not is_admin(roles):
            query = query.filter(ConsultationSession.user_id == user_id)
        query = query.order_by(desc(ConsultationSession.created_at))
        return query.offset((page - 1) * size).limit(size).all()

    def get_session_detail(self, session_id: int, user_id: int, roles: List[str]) -> ConsultationSession:
        session = self.db.query(ConsultationSession).filter(ConsultationSession.id == session_id).first()
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        # session.user_id 是 int，直接比较
        # session.user_id 需确保为实例属性
        if not is_admin(roles) and getattr(session, "user_id", None) != user_id:
            raise HTTPException(status_code=403, detail="Permission denied")
        return session

    def save_message(self, session_id: int, role: str, content: str, sources: Optional[Any] = None) -> ConsultationMessage:
        message = ConsultationMessage(session_id=session_id, role=role, content=content, sources=sources)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def list_messages(self, session_id: int, user_id: int, roles: List[str], page: int = 1, size: int = 20) -> List[ConsultationMessage]:
        session = self.get_session_detail(session_id, user_id, roles)
        query = self.db.query(ConsultationMessage).filter(ConsultationMessage.session_id == session_id)
        query = query.order_by(ConsultationMessage.created_at)
        return query.offset((page - 1) * size).limit(size).all()

    def delete_session(self, session_id: int, user_id: int, roles: List[str]) -> None:
        session = self.db.query(ConsultationSession).filter(ConsultationSession.id == session_id).first()
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if not is_admin(roles) and getattr(session, "user_id", None) != user_id:
            raise HTTPException(status_code=403, detail="Permission denied")
        self.db.delete(session)
        self.db.commit()
