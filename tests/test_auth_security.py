import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def register_user(client, username, password):
    return client.post("/api/auth/register", json={"username": username, "password": password, "roles": ["family"]})

def login_user(client, username, password):
    return client.post("/api/auth/login", json={"username": username, "password": password})

def test_login_wrong_password(client):
    register_user(client, "user3", "rightpass")
    resp = login_user(client, "user3", "wrongpass")
    assert resp.status_code == 401

def test_login_nonexistent_user(client):
    resp = login_user(client, "nouser", "nopass")
    assert resp.status_code == 401

def test_me_unauthorized(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401

def test_session_expired_sim(client):
    # 注册并登录
    register_user(client, "user4", "pass9999")
    resp = login_user(client, "user4", "pass9999")
    assert resp.status_code == 200
    # 模拟 session 失效：直接清除 Cookie
    client.cookies.clear()
    resp2 = client.get("/api/auth/me")
    assert resp2.status_code == 401
