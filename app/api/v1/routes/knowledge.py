from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.knowledge_service import ingest_knowledge_item
from app.db.session import get_db

router = APIRouter()

@router.post("/knowledge/ingest")
def ingest_knowledge_api(title: str, content: str, tags: list = None, db: Session = Depends(get_db)):
    """
    知识入库 API
    """
    knowledge = ingest_knowledge_item(db, title, content, tags)
    return {"id": knowledge.id, "title": knowledge.title, "content": knowledge.content, "tags": knowledge.tags}
