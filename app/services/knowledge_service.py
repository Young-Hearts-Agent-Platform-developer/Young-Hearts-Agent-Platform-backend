from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException
from typing import List, Optional, Any
from datetime import datetime
from app.models.knowledge import KnowledgeItem
from app.schemas.knowledge import KnowledgeItemCreate, KnowledgeItemUpdate, KnowledgeItemAudit
from app.tasks.knowledge_tasks import extract_knowledge_text, vectorize_knowledge_document


class KnowledgeService:
	def __init__(self, db: Session):
		self.db = db

	def create_item(self, user_id: int, data: KnowledgeItemCreate) -> KnowledgeItem:
		item = KnowledgeItem(
			**data.model_dump(),
			author_id=user_id
		)
		self.db.add(item)
		self.db.commit()
		self.db.refresh(item)
		
		# 如果创建时状态为 published，触发异步任务进行切片和向量化
		if getattr(item, "status") == "published":
			task: Any = vectorize_knowledge_document
			task.delay(getattr(item, "id"))
		else:
			# 否则仅触发文本提取任务
			task: Any = extract_knowledge_text
			task.delay(getattr(item, "id"))
			
		return item

	def get_item(self, item_id: int) -> Optional[KnowledgeItem]:
		item = self.db.query(KnowledgeItem).filter(
			KnowledgeItem.id == item_id,
			KnowledgeItem.is_deleted == False
		).first()
		if not item:
			raise HTTPException(status_code=404, detail="Knowledge item not found")
		return item

	def update_item(self, item_id: int, user_id: int, data: KnowledgeItemUpdate, user_roles: List[str]) -> KnowledgeItem:
		item = self.get_item(item_id)
		# 权限校验：作者本人或管理员/专家
		if getattr(item, "author_id") != user_id and not any(role in user_roles for role in ["admin", "expert"]):
			raise HTTPException(status_code=403, detail="Permission denied to edit this item")
		
		old_status = getattr(item, "status")
		update_data = data.model_dump(exclude_unset=True)
		for key, value in update_data.items():
			setattr(item, key, value)
		self.db.commit()
		self.db.refresh(item)
		
		# 如果状态变更为 published，触发异步任务进行切片和向量化
		if old_status != "published" and getattr(item, "status") == "published":
			task: Any = vectorize_knowledge_document
			task.delay(getattr(item, "id"))
			
		return item

	def delete_item(self, item_id: int, user_id: int, user_roles: List[str]):
		item = self.get_item(item_id)
		if getattr(item, "author_id") != user_id and not any(role in user_roles for role in ["admin", "expert"]):
			raise HTTPException(status_code=403, detail="Permission denied to delete this item")
		setattr(item, "is_deleted", True)
		self.db.commit()

	def list_items(self, status: Optional[str] = "published", author_id: Optional[int] = None, skip: int = 0, limit: int = 20) -> tuple[int, List[KnowledgeItem]]:
		query = self.db.query(KnowledgeItem).filter(KnowledgeItem.is_deleted == False)
		if status:
			query = query.filter(KnowledgeItem.status == status)
		if author_id is not None:
			query = query.filter(KnowledgeItem.author_id == author_id)
		total = query.count()
		items = query.order_by(desc(KnowledgeItem.created_at)).offset(skip).limit(limit).all()
		return total, items

	def audit_item(self, item_id: int, expert_id: int, audit_data: KnowledgeItemAudit) -> KnowledgeItem:
		item = self.get_item(item_id)
		if getattr(item, "status") != "pending_review":
			raise HTTPException(status_code=400, detail="Item is not pending review")
		setattr(item, "status", audit_data.status)
		setattr(item, "review_comments", audit_data.review_comments)
		setattr(item, "reviewed_by", expert_id)
		setattr(item, "reviewed_at", datetime.now())
		self.db.commit()
		self.db.refresh(item)
		
		# 如果审核通过并发布，触发异步任务进行切片和向量化
		if getattr(item, "status") == "published":
			task: Any = vectorize_knowledge_document
			task.delay(getattr(item, "id"))
			
		return item
