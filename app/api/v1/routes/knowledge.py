import json
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
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


@router.post("/upload")
async def upload_knowledge_file(
    title: Optional[str] = Form(None, description="标题，纯文本上传时作为文件名"),
    text_content: Optional[str] = Form(None, description="纯文本内容"),
    file: Optional[UploadFile] = File(None, description="上传的文件"),
    category: Optional[str] = Form(None),
    risk_level: Optional[str] = Form("low"),
    document_type: Optional[str] = Form(None),
    target_audience: Optional[str] = Form(None),
    applicable_age: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(get_knowledge_service)
):
    roles = get_user_roles(current_user)
    if not any(role in roles for role in ["volunteer", "expert", "admin"]):
        raise HTTPException(status_code=403, detail="Permission denied")
        
    if not text_content and not file:
        raise HTTPException(status_code=400, detail="Either text_content or file must be provided")
        
    base_dir = "./data/raw_data"
    os.makedirs(base_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    
    content_text = ""
    final_title = title
    
    if text_content:
        # 纯文本（不是文件）
        original_title = title or "untitled"
        filename = f"{original_title}.txt"
        base_name, ext = os.path.splitext(filename)
        
        new_filename = f"{date_str}-{base_name}{ext}"
        file_path = os.path.join(base_dir, new_filename)
        
        counter = 1
        while os.path.exists(file_path):
            new_filename = f"{date_str}-{base_name}_{counter}{ext}"
            file_path = os.path.join(base_dir, new_filename)
            counter += 1
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_content)
            
        content_text = text_content
        final_title = title or original_title
        
    elif file:
        # 文件
        original_title = file.filename or "untitled"
        base_name, ext = os.path.splitext(original_title)
        
        new_filename = f"{date_str}-{original_title}"
        file_path = os.path.join(base_dir, new_filename)
        
        counter = 1
        while os.path.exists(file_path):
            new_filename = f"{date_str}-{base_name}_{counter}{ext}"
            file_path = os.path.join(base_dir, new_filename)
            counter += 1
            
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
            
        # 实际的解析工作交由 Celery 异步任务处理
        content_text = file_path
        final_title = title or base_name
        if not document_type:
            document_type = ext.lstrip('.').lower()

    # 触发解析流程
    # 创建 KnowledgeItem 并触发异步任务
    item_data = KnowledgeItemCreate(
        title=final_title or "untitled",
        content=content_text,
        category=category,
        risk_level=risk_level,
        document_type=document_type,
        target_audience=[target_audience] if target_audience else [],
        applicable_age=[applicable_age] if applicable_age else [],
        status="published" # 直接发布以触发解析流程
    )
    
    user_id = int(getattr(current_user, 'id', 0))
    item = service.create_item(user_id=user_id, data=item_data)
    
    return {"message": "File uploaded and processing started", "item_id": item.id}
