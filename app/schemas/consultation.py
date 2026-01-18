from pydantic import BaseModel, Field
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

    class Config:
        from_attributes = True

class ConsultationSessionBase(BaseModel):
    topic: Optional[str] = None
    is_archived: Optional[bool] = False

class ConsultationSessionCreate(ConsultationSessionBase):
    pass

class ConsultationSession(ConsultationSessionBase):
    id: int
    user_id: int
    created_at: datetime
    messages: Optional[List[ConsultationMessage]] = None

    class Config:
        from_attributes = True
