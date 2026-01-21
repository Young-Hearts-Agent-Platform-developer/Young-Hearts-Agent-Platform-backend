from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Any
from app.services.knowledge_service import ingest_knowledge_item, update_knowledge_item
from app.db.session import get_db
from app.schemas.knowledge import KnowledgeItemUpdate

router = APIRouter()


@router.post("/knowledge/ingest")
def ingest_knowledge_api(title: str, content: str, tags: Optional[List[Any]] = None, db: Session = Depends(get_db)):
    """
    知识入库 API
    """
    knowledge = ingest_knowledge_item(db, title, content, tags)
    return {"id": knowledge.id, "title": knowledge.title, "content": knowledge.content, "tags": knowledge.tags}


@router.patch("/knowledge/{item_id}")
def patch_knowledge_api(item_id: int, item_in: KnowledgeItemUpdate, db: Session = Depends(get_db)):
    """
    部分更新知识条目，接收 KnowledgeItemUpdate（所有字段可选）
    """
    item = update_knowledge_item(db, item_id, item_in)
    if not item:
        raise HTTPException(status_code=404, detail="knowledge item not found")
    return {"id": item.id, "title": item.title, "content": item.content, "tags": item.tags}
