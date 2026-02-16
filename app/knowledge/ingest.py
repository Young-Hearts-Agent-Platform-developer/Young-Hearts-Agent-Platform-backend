# 预留：人工审核流程对接
def manual_review_failed_entries():
    """
    获取并处理解析失败的文档（预留接口，实际应对接管理后台/人工审核页面）。
    """
    from app.knowledge.clean_parse import get_failed_entries, submit_manual_entry
    failed = get_failed_entries()
    # TODO: 实现人工审核流程，如推送到管理后台、等待人工补录
    return failed
"""Placeholder for knowledge ingestion utilities.

Functions to add:
"""

from typing import Iterable


def ingest_documents(docs: Iterable[str]):
    """
    支持异常兜底的文档入库流程。
    :param docs: 可迭代的文档路径或内容
    :return: 入库统计与异常日志
    """
    from app.knowledge.clean_parse import parse_and_clean_entry
    count = 0
    errors = []
    for doc in docs:
        try:
            results = parse_and_clean_entry(doc)
            # 检查是否全部为异常块
            if all(r.get("meta", {}).get("error") for r in results):
                errors.append({"doc": doc, "reason": results[0]["meta"].get("log", "解析失败")})
            else:
                count += 1
        except Exception as e:
            errors.append({"doc": doc, "reason": str(e)})
    return {"ingested": count, "errors": errors}


from app.models.knowledge import KnowledgeItem
from sqlalchemy.orm import Session
from typing import Optional, List, Any


def ingest_knowledge(session: Session, title: str, content: str, tags: Optional[List[Any]] = None, summary: str = "", category: str = "", author_id: int = 0, status: str = "draft"):
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
