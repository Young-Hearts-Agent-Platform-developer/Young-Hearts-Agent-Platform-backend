from sqlalchemy import Column, Integer, BigInteger, String, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.models import Base


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    summary = Column(String(512))
    content = Column(Text, nullable=False)
    file_path = Column(String(512), nullable=True, comment="上传文件的本地存储路径")
    tags = Column(JSON, default=list)
    category = Column(String(100))
    risk_level = Column(String(32), default="low", comment="风险等级: high, medium, low")
    document_type = Column(String(64), comment="文档类型/证据等级")
    target_audience = Column(JSON, comment="适用人群")
    applicable_age = Column(JSON, comment="适用年龄")
    author_id = Column(BigInteger, ForeignKey("users.id"))
    status = Column(String(32), default="draft")  # draft, pending_review, published, rejected, archived
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
    parent_id = Column(Integer, ForeignKey("knowledge_chunks.id", ondelete="CASCADE"), nullable=True, comment="父切片ID")
    chunk_type = Column(String(32), default="independent", comment="切片类型: parent, child, independent")
    content_chunk = Column(Text, nullable=False)
    chunk_metadata = Column(JSON, default=dict, comment="切片专属元数据(继承自Item或提取自内容)")
    vector_id = Column(String(255))
    sequence = Column(Integer)
