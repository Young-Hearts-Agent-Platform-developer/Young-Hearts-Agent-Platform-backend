from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime


class ConsultationMessageBase(BaseModel):
    role: str
    content: str
    sources: Optional[Any] = None


class ConsultationMessageCreate(ConsultationMessageBase):
    pass


class ConsultationMessage(ConsultationMessageBase):
    id: int
    session_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsultationSessionBase(BaseModel):
    topic: Optional[str] = None  # 会话主题，可为空，首次 AI 回复后自动生成
    is_archived: Optional[bool] = False


class ConsultationSessionCreate(ConsultationSessionBase):
    pass


class ConsultationSession(ConsultationSessionBase):
    id: int
    user_id: int
    created_at: datetime
    messages: Optional[List[ConsultationMessage]] = None

    model_config = ConfigDict(from_attributes=True)
