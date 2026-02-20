import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.services.user_service import create_user
from app.schemas.user import UserRegisterRequest
from sqlalchemy.orm import Session

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
    username = "testuser"
    password = "password123"
    user = db.query(User).filter_by(username=username).first()
    if not user:
        user_in = UserRegisterRequest(
            username=username,
            password=password,
            roles=["family"]
        )
        user = create_user(db, user_in)
    db.commit()
    return {"username": username, "password": password}

@pytest.fixture(scope="session")
def admin_user(db: Session):
    username = "adminuser"
    password = "adminpass123"
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
    resp = client.post("/api/v1/auth/login", json=normal_user)
    assert resp.status_code == 200
    return resp.cookies

@pytest.fixture(scope="session")
def admin_token(client, admin_user):
    resp = client.post("/api/v1/auth/login", json=admin_user)
    assert resp.status_code == 200
    return resp.cookies
