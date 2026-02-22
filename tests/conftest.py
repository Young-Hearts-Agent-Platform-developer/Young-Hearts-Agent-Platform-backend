import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.services.user_service import create_user
from app.schemas.user import UserRegisterRequest
from sqlalchemy.orm import Session


# @pytest.fixture(scope="session", autouse=True)
# def mock_celery_tasks():
#     with patch("app.services.knowledge_service.process_knowledge_document.delay") as mock_delay:
#         yield mock_delay


@pytest.fixture(scope="session")
def db():
    # 测试数据库生命周期管理
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def normal_user(db: Session):
    username = "12345"
    password = "12345"
    user = db.query(User).filter_by(username=username).first()
    if not user:
        user_in = UserRegisterRequest(
            username=username,
            password=password,
            roles=["family"]
        )
        user = create_user(db, user_in)
    else:
        import json
        setattr(user, "roles", json.dumps(["family"]))
        db.add(user)
    db.commit()
    return {"username": username, "password": password}


@pytest.fixture(scope="session")
def admin_user(db: Session):
    username = "123456"
    password = "123456"
    user = db.query(User).filter_by(username=username).first()
    if not user:
        user_in = UserRegisterRequest(
            username=username,
            password=password,
            roles=["admin"]
        )
        user = create_user(db, user_in)
    db.commit()
    return {"username": username, "password": password}


@pytest.fixture(scope="session")
def normal_user_token(client, normal_user):
    resp = client.post("/api/auth/login", json=normal_user)
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]
    return {"Cookie": f"session_id={session_id}"}


@pytest.fixture(scope="session")
def admin_token(client, admin_user):
    resp = client.post("/api/auth/login", json=admin_user)
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]
    return {"Cookie": f"session_id={session_id}"}


@pytest.fixture(scope="session")
def existing_user_1_token(client):
    resp = client.post("/api/auth/login", json={"username": "123456", "password": "123456"})
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]
    return {"Cookie": f"session_id={session_id}"}


@pytest.fixture(scope="session")
def existing_user_2_token(client):
    resp = client.post("/api/auth/login", json={"username": "12345", "password": "12345"})
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]
    return {"Cookie": f"session_id={session_id}"}
