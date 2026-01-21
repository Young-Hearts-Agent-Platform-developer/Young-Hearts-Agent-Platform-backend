from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class KnowledgeItemBase(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    author_id: int
    status: str
    review_comments: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class KnowledgeItemCreate(KnowledgeItemBase):
    pass

class KnowledgeItemRead(KnowledgeItemBase):
    id: int

    class Config:
        orm_mode = True


class KnowledgeItemUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    author_id: Optional[int] = None
    status: Optional[str] = None
    review_comments: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class KnowledgeChunkBase(BaseModel):
    item_id: int
    content_chunk: str
    vector_id: Optional[str] = None
    sequence: int
    source: Optional[str] = None
    reference: Optional[str] = None

class KnowledgeChunkCreate(KnowledgeChunkBase):
    pass

class KnowledgeChunkRead(KnowledgeChunkBase):
    id: int

    class Config:
        orm_mode = True
