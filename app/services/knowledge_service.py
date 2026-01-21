from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeItem, KnowledgeChunk
from app.schemas.knowledge import KnowledgeItemCreate, KnowledgeItemRead, KnowledgeItemUpdate, KnowledgeChunkCreate, KnowledgeChunkRead
from datetime import datetime
from typing import List, Optional

# --- 知识条目服务 ---

def create_knowledge_item(db: Session, item_in: KnowledgeItemCreate) -> KnowledgeItem:
    # 注意：created_at 和 updated_at 字段在数据库模型中是必须的，但在创建新条目时应由后端自动生成（如 datetime.now()），而不是由前端或 schema 传入。
    # 如果 schema 里有 created_at/updated_at 字段，且又在此处手动赋值，会导致“同名参数传递两次”报 TypeError。
    # 因此这里用 exclude 排除 schema 里的这两个字段，只在 ORM 层自动赋值，实际数据库和返回结果依然包含这两个字段。
    # 这样既保证字段完整，也保证代码健壮。
    data = item_in.model_dump(exclude={"created_at", "updated_at"})
    item = KnowledgeItem(**data, created_at=datetime.now(), updated_at=datetime.now())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def get_knowledge_item(db: Session, item_id: int) -> Optional[KnowledgeItem]:
    return db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()

def update_knowledge_item(db: Session, item_id: int, item_in: KnowledgeItemUpdate) -> Optional[KnowledgeItem]:
    """
    支持部分更新的更新函数：
    - 接受 `KnowledgeItemUpdate`（所有字段 Optional）
    - 只对传入（被设置）的字段进行赋值
    """
    item = get_knowledge_item(db, item_id)
    if not item:
        return None
    # 使用 pydantic v2 的 model_dump 保持与 create_knowledge_item 中的用法一致
    data = item_in.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(item, field, value)
    item.updated_at = datetime.now()  # type: ignore[assignment]
    db.commit()
    db.refresh(item)
    return item

def delete_knowledge_item(db: Session, item_id: int) -> bool:
    item = get_knowledge_item(db, item_id)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


# 新增：知识入库服务接口
from app.knowledge.ingest import ingest_knowledge

def ingest_knowledge_item(db: Session, title: str, content: str, tags: Optional[List] = None):
    """
    服务层：知识入库（严格对齐 create_knowledge_item 字段）
    """
    # 默认值与 create_knowledge_item 保持一致
    return ingest_knowledge(
        db,
        title=title,
        content=content,
        tags=tags,
        summary="",
        category="",
        author_id=0,
        status="draft"
    )
    return True

# --- 单次审核流 ---

def review_knowledge_item(db: Session, item_id: int, reviewer_id: int, review_comments: str, approve: bool) -> Optional[KnowledgeItem]:
    item = get_knowledge_item(db, item_id)
    if not item:
        return None
    item.reviewed_by = reviewer_id  # type: ignore[assignment]
    item.review_comments = review_comments  # type: ignore[assignment]
    item.reviewed_at = datetime.now()  # type: ignore[assignment]
    item.status = "published" if approve else "rejected"  # type: ignore[assignment]
    item.updated_at = datetime.now()  # type: ignore[assignment]
    db.commit()
    db.refresh(item)
    return item

# --- 知识切片服务（可选）---

def create_knowledge_chunk(db: Session, chunk_in: KnowledgeChunkCreate) -> KnowledgeChunk:
    chunk = KnowledgeChunk(**chunk_in.dict())
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk

def get_knowledge_chunks_by_item(db: Session, item_id: int) -> List[KnowledgeChunk]:
    return db.query(KnowledgeChunk).filter(KnowledgeChunk.item_id == item_id).all()
