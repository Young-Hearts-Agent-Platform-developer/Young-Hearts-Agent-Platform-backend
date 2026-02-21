from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class KnowledgeItemBase(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str
    tags: Optional[List[str]] = []
    category: Optional[str] = None


class KnowledgeItemCreate(KnowledgeItemBase):
    status: Optional[str] = "draft"  # 允许直接提交为 pending_review


class KnowledgeItemUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    status: Optional[str] = None


class KnowledgeItemAudit(BaseModel):
    status: str = Field(..., pattern="^(published|rejected)$")
    review_comments: Optional[str] = None


class KnowledgeItemResponse(KnowledgeItemBase):
    id: int
    author_id: int
    status: str
    review_comments: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeItemListResponse(BaseModel):
    total: int
    items: List[KnowledgeItemResponse]
