import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.knowledge import KnowledgeItem, KnowledgeChunk
from app.models import Base
from app.services.knowledge_service import (
    create_knowledge_item,
    get_knowledge_item,
    review_knowledge_item,
    delete_knowledge_item,
)
from app.schemas.knowledge import KnowledgeItemCreate
from app.services.knowledge_service import update_knowledge_item
from app.schemas.knowledge import KnowledgeItemUpdate

@pytest.fixture(scope="function")
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # 确保所有模型都已 import，users 表会被自动创建
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_create_review_delete(db):
    # 创建知识条目
    item_in = KnowledgeItemCreate(
        title="测试条目",
        summary="摘要",
        content="内容",
        tags=["tag1", "tag2"],
        category="测试分类",
        author_id=1,
        status="draft"
    )
    item = create_knowledge_item(db, item_in)
    assert item.id is not None
    assert item.status == "draft"

    # 审核通过
    # ...existing code...


def test_ingest_knowledge_item(db):
    from app.services.knowledge_service import ingest_knowledge_item
    title = "知识入库测试"
    content = "这是知识内容"
    tags = ["test", "ingest"]
    knowledge = ingest_knowledge_item(db, title, content, tags)
    assert knowledge.id is not None
    assert knowledge.title == title
    assert knowledge.content == content
    assert knowledge.tags == tags
    reviewed = review_knowledge_item(db, knowledge.id, reviewer_id=2, review_comments="通过", approve=True)
    assert reviewed.status == "published"
    assert reviewed.review_comments == "通过"
    assert reviewed.reviewed_by == 2

    # 审核失败
    item2_in = KnowledgeItemCreate(
        title="待审核条目",
        summary="摘要2",
        content="内容2",
        tags=["tag3"],
        category="分类2",
        author_id=3,
        status="draft"
    )
    item2 = create_knowledge_item(db, item2_in)
    reviewed2 = review_knowledge_item(db, item2.id, reviewer_id=4, review_comments="不通过", approve=False)
    assert reviewed2.status == "rejected"
    assert reviewed2.review_comments == "不通过"
    assert reviewed2.reviewed_by == 4

    # 删除条目
    assert delete_knowledge_item(db, item2.id) is True
    assert get_knowledge_item(db, item2.id) is None


def test_update_partial(db):
    # 创建初始条目
    item_in = KnowledgeItemCreate(
        title="原标题",
        summary="原摘要",
        content="原内容",
        tags=["a"],
        category="原分类",
        author_id=10,
        status="draft"
    )
    item = create_knowledge_item(db, item_in)

    # 部分更新：仅更新 title 和 tags
    update_in = KnowledgeItemUpdate(title="新标题", tags=["b", "c"]) 
    updated = update_knowledge_item(db, item.id, update_in)
    assert updated is not None
    assert updated.title == "新标题"
    assert updated.tags == ["b", "c"]
    # 未更新字段保持原值
    assert updated.content == "原内容"
    assert updated.author_id == 10
