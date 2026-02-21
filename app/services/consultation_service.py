
from typing import List, Optional, Any
from sqlalchemy.orm import Session
from app.models.consultation import ConsultationSession, ConsultationMessage
from sqlalchemy import desc
from fastapi import HTTPException
from app.services.auth import is_admin
from app.services.rag.service import generate_topic


class ConsultationService:
    def __init__(self, db: Session):
        self.db = db

    def get_session(self, session_id: int) -> Optional[ConsultationSession]:
        """
        根据 session_id 查询 ConsultationSession，不做权限校验，仅供内部使用。
        """
        return self.db.query(ConsultationSession).filter(ConsultationSession.id == session_id).first()

    def create_session(self, user_id: int, topic: str) -> ConsultationSession:
        # 若 topic 为空或仅包含空白字符，则默认为“新对话”
        if not topic or (isinstance(topic, str) and topic.strip() == ""):
            topic = "新对话"
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
        保存 AI 消息，并在首次 AI 回复后自动生成 topic，异常时记录日志防止误生成
        :param session_id: 会话ID
        :param ai_content: AI 回复内容
        :param user_content: 用户首次提问内容（仅首次AI回复时需传入）
        :param sources: RAG 源
        :return: ConsultationMessage
        """
        session = self.db.query(ConsultationSession).filter(ConsultationSession.id == session_id).first()
        if session is None:
            print(f"[ERROR] save_ai_message_and_generate_topic: Session not found, session_id={session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        # 获取当前 topic 值，避免直接用 Column 对象
        current_topic = getattr(session, 'topic', None)
        if isinstance(current_topic, str):
            topic_value = current_topic
        else:
            topic_value = None

        # 判断是否首次生成 topic (幂等性检查)
        if (topic_value is None) or (topic_value == "新对话"):
            try:
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
                new_topic = generate_topic(safe_user_content, safe_ai_content)
                
                # 原子更新：仅当数据库中 topic 仍为空或“新对话”时更新，防止并发覆盖
                result = self.db.query(ConsultationSession).filter(
                    ConsultationSession.id == session_id,
                    (ConsultationSession.topic == None) | (ConsultationSession.topic == "新对话")  # noqa: E711
                ).update({"topic": new_topic}, synchronize_session=False)

                if result > 0:
                    self.db.commit()
                    self.db.refresh(session)
                else:
                    # 若并未更新（可能已被其他并发请求修改），则刷新 session 状态
                    self.db.expire(session, ['topic'])
                    self.db.refresh(session)

            except Exception as ex:
                print(f"[ERROR] topic 生成异常: {ex}, session_id={session_id}")
                # 不抛出，防止误生成
        # 保存 AI 消息
        message = ConsultationMessage(session_id=session_id, role="ai", content=ai_content, sources=sources)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def list_messages_all(self, session_id: int, user_id: int, roles: List[str]) -> List[ConsultationMessage]:
        _ = self.get_session_detail(session_id, user_id, roles)
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
