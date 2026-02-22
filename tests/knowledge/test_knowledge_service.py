import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from app.services.knowledge_service import KnowledgeService
from app.schemas.knowledge import KnowledgeItemCreate, KnowledgeItemUpdate, KnowledgeItemAudit
from app.models import Base
from app.models.knowledge import KnowledgeItem


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def service(db_session):
    return KnowledgeService(db_session)


@pytest.fixture(scope="function")
def user_id():
    return 1


@pytest.fixture(scope="function")
def user_roles():
    return ["volunteer"]


@pytest.fixture(scope="function")
def expert_id():
    return 2


@pytest.fixture(scope="function")
def expert_roles():
    return ["expert"]


@pytest.mark.parametrize("title,content", [
    ("知识标题1", "知识内容1"),
    ("知识标题2", "知识内容2")
])
def test_create_and_get_item(service, db_session, user_id, title, content):
    data = KnowledgeItemCreate(title=title, content=content)
    item = service.create_item(user_id=user_id, data=data)
    assert item.id > 0
    fetched = service.get_item(item.id)
    assert fetched.title == title
    assert fetched.content == content


def test_get_nonexistent_item(service, db_session):
    with pytest.raises(HTTPException) as exc_info:
        service.get_item(999)
    assert exc_info.value.status_code == 404

def test_get_deleted_item(service, db_session, user_id, user_roles):
    data = KnowledgeItemCreate(title="删除测试", content="内容")
    item = service.create_item(user_id=user_id, data=data)
    service.delete_item(item.id, user_id, user_roles)
    with pytest.raises(HTTPException) as exc_info:
        service.get_item(item.id)
    assert exc_info.value.status_code == 404

def test_update_item(service, db_session, user_id, user_roles):
    data = KnowledgeItemCreate(title="原始标题", content="原始内容")
    item = service.create_item(user_id=user_id, data=data)
    update = KnowledgeItemUpdate(title="新标题", content="新内容")
    updated = service.update_item(item.id, user_id, update, user_roles)
    assert updated.title == "新标题"
    assert updated.content == "新内容"


def test_update_item_by_expert(service, db_session, user_id, expert_id, expert_roles):
    data = KnowledgeItemCreate(title="原始标题", content="原始内容")
    item = service.create_item(user_id=user_id, data=data)
    update = KnowledgeItemUpdate(title="专家修改标题", content="专家修改内容")
    updated = service.update_item(item.id, expert_id, update, expert_roles)
    assert updated.title == "专家修改标题"
    assert updated.content == "专家修改内容"

def test_update_item_by_unauthorized_user(service, db_session, user_id):
    data = KnowledgeItemCreate(title="原始标题", content="原始内容")
    item = service.create_item(user_id=user_id, data=data)
    update = KnowledgeItemUpdate(title="非法修改标题", content="非法修改内容")
    with pytest.raises(HTTPException) as exc_info:
        service.update_item(item.id, 999, update, ["user"])
    assert exc_info.value.status_code == 403

def test_delete_item(service, db_session, user_id, user_roles):
    data = KnowledgeItemCreate(title="删除测试", content="内容")
    item = service.create_item(user_id=user_id, data=data)
    service.delete_item(item.id, user_id, user_roles)
    with pytest.raises(Exception):
        service.get_item(item.id)


def test_delete_item_by_expert(service, db_session, user_id, expert_id, expert_roles):
    data = KnowledgeItemCreate(title="删除测试", content="内容")
    item = service.create_item(user_id=user_id, data=data)
    service.delete_item(item.id, expert_id, expert_roles)
    with pytest.raises(HTTPException) as exc_info:
        service.get_item(item.id)
    assert exc_info.value.status_code == 404

def test_delete_item_by_unauthorized_user(service, db_session, user_id):
    data = KnowledgeItemCreate(title="删除测试", content="内容")
    item = service.create_item(user_id=user_id, data=data)
    with pytest.raises(HTTPException) as exc_info:
        service.delete_item(item.id, 999, ["user"])
    assert exc_info.value.status_code == 403

def test_list_items(service, db_session, user_id, user_roles):
    for i in range(5):
        service.create_item(user_id=user_id, data=KnowledgeItemCreate(title=f"标题{i}", content=f"内容{i}", status="published"))
    for i in range(3):
        service.create_item(user_id=user_id, data=KnowledgeItemCreate(title=f"草稿{i}", content=f"内容{i}", status="draft"))
    
    # 测试分页
    total, items = service.list_items(status=None, skip=0, limit=3)
    assert total == 8
    assert len(items) == 3

    # 测试状态过滤
    total, items = service.list_items(status="published", skip=0, limit=10)
    assert total == 5
    assert len(items) == 5

    # 测试软删除过滤
    item_to_delete = items[0]
    service.delete_item(item_to_delete.id, user_id, user_roles)
    total, items = service.list_items(status="published", skip=0, limit=10)
    assert total == 4
    assert len(items) == 4

def test_audit_item(service, db_session, user_id, expert_id, expert_roles):
    # 创建待审核条目
    data = KnowledgeItemCreate(title="待审核", content="内容", status="pending_review")
    item = service.create_item(user_id=user_id, data=data)
    audit = KnowledgeItemAudit(status="published", review_comments="通过")
    audited = service.audit_item(item.id, expert_id, audit)
    assert audited.status == "published"
    assert audited.review_comments == "通过"
    assert audited.reviewed_by == expert_id
    assert audited.reviewed_at is not None

    # 审核拒绝
    data2 = KnowledgeItemCreate(title="待审核2", content="内容2", status="pending_review")
    item2 = service.create_item(user_id=user_id, data=data2)
    audit2 = KnowledgeItemAudit(status="rejected", review_comments="不通过")
    audited2 = service.audit_item(item2.id, expert_id, audit2)
    assert audited2.status == "rejected"
    assert audited2.review_comments == "不通过"
    assert audited2.reviewed_by == expert_id
    assert audited2.reviewed_at is not None

    # 非待审核状态不能审核
    data3 = KnowledgeItemCreate(title="已发布", content="内容3", status="published")
    item3 = service.create_item(user_id=user_id, data=data3)
    audit3 = KnowledgeItemAudit(status="published", review_comments="无")
    with pytest.raises(HTTPException) as exc_info:
        service.audit_item(item3.id, expert_id, audit3)
    assert exc_info.value.status_code == 400
