"""Placeholder for knowledge ingestion utilities.

Functions to add:
"""

from typing import Iterable


def ingest_documents(docs: Iterable[str]):
    """Stub: accept iterable of strings and return count."""
    count = 0
    for _ in docs:
        count += 1
    return {"ingested": count}


from app.models.knowledge import KnowledgeItem
from sqlalchemy.orm import Session

def ingest_knowledge(session: Session, title: str, content: str, tags: list = None, summary: str = "", category: str = "", author_id: int = 0, status: str = "draft"):
    """
    严格对齐 create_knowledge_item 的字段补全逻辑，完整入库 KnowledgeItem。
    """
    from datetime import datetime
    knowledge = KnowledgeItem(
        title=title,
        summary=summary,
        content=content,
        tags=tags or [],
        category=category,
        author_id=author_id,
        status=status,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    session.add(knowledge)
    session.commit()
    session.refresh(knowledge)
    return knowledge
