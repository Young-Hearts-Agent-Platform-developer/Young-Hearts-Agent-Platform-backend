from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Union
from datetime import datetime


class KnowledgeItemBase(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str
    file_path: Optional[str] = Field(default=None, description="文件路径")
    tags: Optional[List[str]] = []
    category: Optional[str] = None
    risk_level: Optional[str] = Field(default="low", description="风险等级: high, medium, low")
    document_type: Optional[str] = Field(default=None, description="文档类型/证据等级")
    target_audience: Optional[List[str]] = Field(default=None, description="适用人群")
    applicable_age: Optional[List[str]] = Field(default=None, description="适用年龄")


class KnowledgeItemCreate(KnowledgeItemBase):
    status: Optional[str] = "draft"  # 允许直接提交为 pending_review


class KnowledgeItemUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    file_path: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    risk_level: Optional[str] = None
    document_type: Optional[str] = None
    target_audience: Optional[List[str]] = None
    applicable_age: Optional[List[str]] = None
    status: Optional[str] = None


class KnowledgeItemAudit(BaseModel):
    status: str = Field(..., pattern="^(published|rejected)$")
    review_comments: Optional[str] = None


class KnowledgeItemResponse(KnowledgeItemBase):
    id: int
    author_id: int
    status: str
    review_comments: Optional[str] = None
    reviewed_by: Optional[Union[int, str]] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeItemListResponse(BaseModel):
    total: int
    items: List[KnowledgeItemResponse]
