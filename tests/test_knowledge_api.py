from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from app.main import app
from app.db.session import get_db
from app.models import Base
from app.schemas.knowledge import KnowledgeItemCreate
from app.services.knowledge_service import create_knowledge_item


def test_patch_knowledge_api_partial_update():
    # 使用内存 sqlite，并确保路由中的 get_db 使用相同的会话
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    db_path = tmp.name
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # 通过 service 在同一数据库中创建初始条目
    db = SessionLocal()
    item_in = KnowledgeItemCreate(
        title="原始标题",
        summary="原始摘要",
        content="原始内容",
        tags=["t1"],
        category="分类",
        author_id=1,
        status="draft",
    )
    item = create_knowledge_item(db, item_in)
    db.close()

    client = TestClient(app)

    # 部分更新：只更新 title
    resp = client.patch(f"/knowledge/{item.id}", json={"title": "新标题"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["title"] == "新标题"
    assert data["content"] == "原始内容"

    # cleanup temp db file
    try:
        os.unlink(db_path)
    except Exception:
        pass


def test_patch_knowledge_api_full_update():
    # 使用内存 sqlite，并确保路由中的 get_db 使用相同的会话
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    db_path = tmp.name
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = SessionLocal()
    item_in = KnowledgeItemCreate(
        title="原始标题",
        summary="原始摘要",
        content="原始内容",
        tags=["t1"],
        category="分类",
        author_id=1,
        status="draft",
    )
    item = create_knowledge_item(db, item_in)
    db.close()

    client = TestClient(app)

    # 全量更新：提供所有字段
    payload = {
        "title": "新标题",
        "summary": "新摘要",
        "content": "新内容",
        "tags": ["a", "b"],
        "category": "新分类",
        "author_id": 2,
        "status": "published"
    }
    resp = client.patch(f"/knowledge/{item.id}", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["title"] == "新标题"
    assert data["content"] == "新内容"

    try:
        os.unlink(db_path)
    except Exception:
        pass


def test_patch_knowledge_api_no_change():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    db_path = tmp.name
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = SessionLocal()
    item_in = KnowledgeItemCreate(
        title="保持标题",
        summary="保持摘要",
        content="保持内容",
        tags=["keep"],
        category="分类",
        author_id=1,
        status="draft",
    )
    item = create_knowledge_item(db, item_in)
    db.close()

    client = TestClient(app)

    # 无字段更新：发送空对象
    resp = client.patch(f"/knowledge/{item.id}", json={})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["title"] == "保持标题"
    assert data["content"] == "保持内容"

    try:
        os.unlink(db_path)
    except Exception:
        pass
