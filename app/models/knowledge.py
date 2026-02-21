from sqlalchemy import Column, Integer, BigInteger, String, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.models import Base

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    summary = Column(String(512))
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    category = Column(String(100))
    author_id = Column(BigInteger, ForeignKey("users.id"))
    status = Column(String(32), default="draft") # draft, pending_review, published, rejected, archived
    review_comments = Column(Text)
    reviewed_by = Column(BigInteger, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    is_deleted = Column(Boolean, default=False, comment="软删除标记")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("knowledge_items.id", ondelete="CASCADE"))
    content_chunk = Column(Text, nullable=False)
    vector_id = Column(String(255))
    sequence = Column(Integer)
