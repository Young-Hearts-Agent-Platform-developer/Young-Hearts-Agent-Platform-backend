from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Any
from datetime import datetime
import json


class ConsultationMessageBase(BaseModel):
    role: str
    content: str
    sources: Optional[Any] = None

    @field_validator('sources', mode='before')
    @classmethod
    def parse_sources(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v


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
