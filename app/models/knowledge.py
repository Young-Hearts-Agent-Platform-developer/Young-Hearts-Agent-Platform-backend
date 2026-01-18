

from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, JSON
from app.models import Base

class KnowledgeItem(Base):
    __tablename__ = 'knowledge_items'
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    summary = Column(Text)
    content = Column(Text)
    tags = Column(JSON)
    category = Column(String(255))  # 分类（如: "情绪干预", "生活自理"）
    author_id = Column(BigInteger, ForeignKey('users.id'))  # 作者（用户ID），类型修正
    status = Column(String(32))  # ['draft', 'pending_review', 'published', 'rejected', 'archived']
    review_comments = Column(Text)  # 审核意见
    reviewed_by = Column(BigInteger, ForeignKey('users.id'))  # 审核专家，类型修正
    reviewed_at = Column(DateTime)  # 审核时间
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class KnowledgeChunk(Base):
    __tablename__ = 'knowledge_chunks'
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('knowledge_items.id'))
    content_chunk = Column(Text)
    vector_id = Column(String(64))
    sequence = Column(Integer)
    source = Column(String(255))  # 切片来源（如原文页码、章节）
    reference = Column(String(255))  # 切片级引用（如具体文献、URL）
