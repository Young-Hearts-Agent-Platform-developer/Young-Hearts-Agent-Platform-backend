import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.services.knowledge_service import KnowledgeService
from app.schemas.knowledge import KnowledgeItemCreate, KnowledgeItemUpdate, KnowledgeItemResponse, KnowledgeItemAudit, KnowledgeItemListResponse
from app.models.user import User

router = APIRouter()


def get_knowledge_service(db: Session = Depends(get_db)):
    return KnowledgeService(db)


def get_user_roles(user: User) -> List[str]:
    roles = getattr(user, 'roles', [])
    if isinstance(roles, str):
        try:
            return json.loads(roles)
        except Exception:
            return []
    return list(roles)


@router.post("/items", response_model=KnowledgeItemResponse)
async def create_item(
    req: KnowledgeItemCreate,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service)
):
    roles = get_user_roles(current_user)
    if not any(role in roles for role in ["volunteer", "expert", "admin"]):
        raise HTTPException(status_code=403, detail="Permission denied")
    user_id = int(getattr(current_user, 'id', 0))
    return service.create_item(user_id=user_id, data=req)


@router.get("/items", response_model=KnowledgeItemListResponse)
async def list_items(
    status: Optional[str] = Query("published", description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: KnowledgeService = Depends(get_knowledge_service)
):
    total, items = service.list_items(status=status, skip=skip, limit=limit)
    return {"total": total, "items": items}


@router.get("/items/{item_id}", response_model=KnowledgeItemResponse)
async def get_item(
    item_id: int,
    service: KnowledgeService = Depends(get_knowledge_service)
):
    return service.get_item(item_id)


@router.put("/items/{item_id}", response_model=KnowledgeItemResponse)
async def update_item(
    item_id: int,
    req: KnowledgeItemUpdate,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service)
):
    user_id = int(getattr(current_user, 'id', 0))
    roles = get_user_roles(current_user)
    return service.update_item(item_id=item_id, user_id=user_id, data=req, user_roles=roles)


@router.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service)
):
    user_id = int(getattr(current_user, 'id', 0))
    roles = get_user_roles(current_user)
    service.delete_item(item_id=item_id, user_id=user_id, user_roles=roles)
    return {"message": "Item deleted successfully"}


@router.get("/audit-list", response_model=KnowledgeItemListResponse)
async def get_audit_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service)
):
    roles = get_user_roles(current_user)
    if not any(role in roles for role in ["expert", "admin"]):
        raise HTTPException(status_code=403, detail="Permission denied")
    total, items = service.list_items(status="pending_review", skip=skip, limit=limit)
    return {"total": total, "items": items}


@router.post("/{item_id}/audit", response_model=KnowledgeItemResponse)
async def audit_item(
    item_id: int,
    req: KnowledgeItemAudit,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service)
):
    roles = get_user_roles(current_user)
    if not any(role in roles for role in ["expert", "admin"]):
        raise HTTPException(status_code=403, detail="Permission denied")
    expert_id = int(getattr(current_user, 'id', 0))
    return service.audit_item(item_id=item_id, expert_id=expert_id, audit_data=req)


from fastapi import UploadFile, File
@router.post("/upload")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service)
):
    roles = get_user_roles(current_user)
    if not any(role in roles for role in ["volunteer", "expert", "admin"]):
        raise HTTPException(status_code=403, detail="Permission denied")
    # TODO: 接收并保存文件，同步调用 rag/ 中的相关服务进行切片
    # 具体实现方式待定，此处仅为接口占位
    return {"message": f"File {file.filename} uploaded successfully. Processing will be implemented later."}
