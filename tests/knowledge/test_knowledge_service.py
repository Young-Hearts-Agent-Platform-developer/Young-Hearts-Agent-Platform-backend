import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from app.services.knowledge_service import KnowledgeService
from app.schemas.knowledge import KnowledgeItemCreate, KnowledgeItemUpdate, KnowledgeItemAudit
from app.models import Base
from app.models.knowledge import KnowledgeItem


@pytest.fixture(scope="function")
def mock_extract_task():
    with patch("app.services.knowledge_service.extract_knowledge_text.delay") as mock:
        yield mock


@pytest.fixture(scope="function")
def mock_vectorize_task():
    with patch("app.services.knowledge_service.vectorize_knowledge_document.delay") as mock:
        yield mock


@pytest.fixture(scope="function")
def mock_get_chroma_collection():
    with patch("app.services.knowledge_service.get_chroma_collection") as mock:
        yield mock


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


@pytest.mark.parametrize("title,content,risk_level", [
    ("知识标题1", "知识内容1", "low"),
    ("知识标题2", "知识内容2", "high")
])
def test_create_and_get_item(service, db_session, user_id, title, content, risk_level, mock_extract_task, mock_vectorize_task):
    data = KnowledgeItemCreate(title=title, content=content, risk_level=risk_level, status="draft")
    item = service.create_item(user_id=user_id, data=data)
    assert item.id > 0
    fetched = service.get_item(item.id)
    assert fetched.title == title
    assert fetched.content == content
    assert fetched.risk_level == risk_level
    
    # 验证调用了 extract_knowledge_text 任务
    mock_extract_task.assert_called_once_with(item.id)
    mock_vectorize_task.assert_not_called()


def test_create_published_item(service, db_session, user_id, mock_extract_task, mock_vectorize_task):
    data = KnowledgeItemCreate(title="已发布", content="内容", status="published")
    item = service.create_item(user_id=user_id, data=data)
    
    # 验证调用了 vectorize_knowledge_document 任务
    mock_vectorize_task.assert_called_once_with(item.id)
    mock_extract_task.assert_not_called()


# @pytest.mark.skip(reason="该测试已通过")
def test_get_nonexistent_item(service, db_session):
    with pytest.raises(HTTPException) as exc_info:
        service.get_item(999)
    assert exc_info.value.status_code == 404


# @pytest.mark.skip(reason="该测试已通过")
def test_get_deleted_item(service, db_session, user_id, user_roles):
    data = KnowledgeItemCreate(title="删除测试", content="内容")
    item = service.create_item(user_id=user_id, data=data)
    service.delete_item(item.id, user_id, user_roles)
    with pytest.raises(HTTPException) as exc_info:
        service.get_item(item.id)
    assert exc_info.value.status_code == 404


# @pytest.mark.skip(reason="该测试已通过")
def test_update_item(service, db_session, user_id, user_roles, mock_extract_task, mock_vectorize_task):
    data = KnowledgeItemCreate(title="原始标题", content="原始内容", status="draft")
    item = service.create_item(user_id=user_id, data=data)
    
    # 重置 mock
    mock_extract_task.reset_mock()
    mock_vectorize_task.reset_mock()
    
    update = KnowledgeItemUpdate(title="新标题", content="新内容", status="published")
    updated = service.update_item(item.id, user_id, update, user_roles)
    assert updated.title == "新标题"
    assert updated.content == "新内容"
    assert updated.status == "published"
    
    # 状态变更为 published，应该调用 vectorize_knowledge_document
    mock_vectorize_task.assert_called_once_with(item.id)
    mock_extract_task.assert_not_called()



# @pytest.mark.skip(reason="该测试已通过")
def test_update_item_by_expert(service, db_session, user_id, expert_id, expert_roles):
    data = KnowledgeItemCreate(title="原始标题", content="原始内容")
    item = service.create_item(user_id=user_id, data=data)
    update = KnowledgeItemUpdate(title="专家修改标题", content="专家修改内容")
    updated = service.update_item(item.id, expert_id, update, expert_roles)
    assert updated.title == "专家修改标题"
    assert updated.content == "专家修改内容"


# @pytest.mark.skip(reason="该测试已通过")
def test_update_item_by_unauthorized_user(service, db_session, user_id):
    data = KnowledgeItemCreate(title="原始标题", content="原始内容")
    item = service.create_item(user_id=user_id, data=data)
    update = KnowledgeItemUpdate(title="非法修改标题", content="非法修改内容")
    with pytest.raises(HTTPException) as exc_info:
        service.update_item(item.id, 999, update, ["user"])
    assert exc_info.value.status_code == 403


# @pytest.mark.skip(reason="该测试已通过")
def test_delete_item(service, db_session, user_id, user_roles, mock_get_chroma_collection):
    data = KnowledgeItemCreate(title="删除测试", content="内容")
    item = service.create_item(user_id=user_id, data=data)
    
    # 模拟 ChromaDB 集合
    mock_collection = mock_get_chroma_collection.return_value
    
    # 添加一些模拟的切片数据
    from app.models.knowledge import KnowledgeChunk
    chunk1 = KnowledgeChunk(item_id=item.id, content_chunk="chunk1", vector_id="vec1")
    chunk2 = KnowledgeChunk(item_id=item.id, content_chunk="chunk2", vector_id="vec2")
    db_session.add_all([chunk1, chunk2])
    db_session.commit()
    
    service.delete_item(item.id, user_id, user_roles)
    
    # 验证 ChromaDB 的 delete 方法被调用
    mock_get_chroma_collection.assert_called_once()
    mock_collection.delete.assert_called_once_with(ids=["vec1", "vec2"])
    
    with pytest.raises(Exception):
        service.get_item(item.id)


# @pytest.mark.skip(reason="该测试已通过")
def test_delete_item_by_expert(service, db_session, user_id, expert_id, expert_roles, mock_get_chroma_collection):
    data = KnowledgeItemCreate(title="删除测试", content="内容")
    item = service.create_item(user_id=user_id, data=data)
    
    # 模拟 ChromaDB 集合
    mock_collection = mock_get_chroma_collection.return_value
    
    service.delete_item(item.id, expert_id, expert_roles)
    
    # 验证 ChromaDB 的 delete 方法被调用（即使没有切片，也会尝试获取集合，但不会调用 delete）
    mock_get_chroma_collection.assert_not_called()
    mock_collection.delete.assert_not_called()
    
    with pytest.raises(HTTPException) as exc_info:
        service.get_item(item.id)
    assert exc_info.value.status_code == 404


# @pytest.mark.skip(reason="该测试已通过")
def test_delete_item_by_unauthorized_user(service, db_session, user_id):
    data = KnowledgeItemCreate(title="删除测试", content="内容")
    item = service.create_item(user_id=user_id, data=data)
    with pytest.raises(HTTPException) as exc_info:
        service.delete_item(item.id, 999, ["user"])
    assert exc_info.value.status_code == 403


# @pytest.mark.skip(reason="该测试已通过")
def test_list_items(service, db_session, user_id, user_roles, mock_get_chroma_collection):
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


# @pytest.mark.skip(reason="该测试已通过")
def test_audit_item(service, db_session, user_id, expert_id, expert_roles, mock_extract_task, mock_vectorize_task):
    # 创建待审核条目
    data = KnowledgeItemCreate(title="待审核", content="内容", status="pending_review")
    item = service.create_item(user_id=user_id, data=data)
    
    # 创建时应该调用 extract_knowledge_text
    mock_extract_task.assert_called_once_with(item.id)
    mock_vectorize_task.assert_not_called()
    
    # 重置 mock
    mock_extract_task.reset_mock()
    mock_vectorize_task.reset_mock()
    
    audit = KnowledgeItemAudit(status="published", review_comments="通过")
    audited = service.audit_item(item.id, expert_id, audit)
    assert audited.status == "published"
    assert audited.review_comments == "通过"
    assert audited.reviewed_by == expert_id
    assert audited.reviewed_at is not None
    
    # 审核通过后应该调用 vectorize_knowledge_document
    mock_vectorize_task.assert_called_once_with(item.id)
    mock_extract_task.assert_not_called()

    # 重置 mock
    mock_extract_task.reset_mock()
    mock_vectorize_task.reset_mock()

    # 审核拒绝
    data2 = KnowledgeItemCreate(title="待审核2", content="内容2", status="pending_review")
    item2 = service.create_item(user_id=user_id, data=data2)
    
    # 重置 mock
    mock_extract_task.reset_mock()
    mock_vectorize_task.reset_mock()
    
    audit2 = KnowledgeItemAudit(status="rejected", review_comments="不通过")
    audited2 = service.audit_item(item2.id, expert_id, audit2)
    assert audited2.status == "rejected"
    assert audited2.review_comments == "不通过"
    assert audited2.reviewed_by == expert_id
    assert audited2.reviewed_at is not None
    
    # 审核拒绝不应该调用 vectorize_knowledge_document
    mock_vectorize_task.assert_not_called()
    mock_extract_task.assert_not_called()

    # 非待审核状态不能审核
    data3 = KnowledgeItemCreate(title="已发布", content="内容3", status="published")
    item3 = service.create_item(user_id=user_id, data=data3)
    audit3 = KnowledgeItemAudit(status="published", review_comments="无")
    with pytest.raises(HTTPException) as exc_info:
        service.audit_item(item3.id, expert_id, audit3)
    assert exc_info.value.status_code == 400
