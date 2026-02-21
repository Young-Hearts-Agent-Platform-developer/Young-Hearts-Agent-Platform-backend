import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def register_user(client, username, password, roles=None):
    if roles is None:
        roles = ["family"]
    data = {"username": username, "password": password, "roles": roles}
    return client.post("/api/auth/register", json=data)

def login_user(client, username, password, user_agent=None):
    # 默认模拟 Web 端，确保获取 Cookie
    if user_agent is None:
        user_agent = "web-test-client"
    headers = {"User-Agent": user_agent}
    return client.post("/api/auth/login", json={"username": username, "password": password}, headers=headers)


def test_register_and_login(client):
    # 注册普通用户
    resp = register_user(client, "user1", "pass1234")
    assert resp.status_code == 200
    # 注册已存在用户
    resp2 = register_user(client, "user1", "pass1234")
    assert resp2.status_code in (400, 409)
    # 注册 admin 角色
    resp3 = register_user(client, "admin1", "pass1234", roles=["admin"])
    assert resp3.status_code == 403

    # 登录
    resp4 = login_user(client, "user1", "pass1234")
    assert resp4.status_code == 200
    # 检查 session_id Cookie
    assert "session_id" in resp4.cookies

    # Web端 User-Agent
    resp5 = login_user(client, "user1", "pass1234")
    assert resp5.status_code == 200
    assert "session_id" in resp5.cookies
    # # App端 User-Agent
    # resp6 = login_user(client, "user1", "pass1234", user_agent="AppClient/1.0")
    # assert resp6.status_code == 200
    # # App端通常返回体内含 session_id
    # assert ("session_id" in resp6.cookies) or (resp6.json().get("session_id"))


def test_me_info(client):
    # 注册并登录
    register_user(client, "user2", "pass5678")
    resp = login_user(client, "user2", "pass5678")
    assert resp.status_code == 200
    # 手动设置 session_id Cookie 到 client
    session_id = resp.cookies.get("session_id")
    assert session_id is not None
    client.cookies.set("session_id", session_id)
    # 获取当前用户信息
    resp2 = client.get("/api/auth/me")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["username"] == "user2"
    # 检查敏感字段脱敏（如 phone 字段）
    if "phone" in data:
        assert data["phone"].startswith("***") or data["phone"] == ""
    # 注销
    resp3 = client.post("/api/auth/logout")
    assert resp3.status_code == 200
    # 注销后再访问
    resp4 = client.get("/api/auth/me")
    assert resp4.status_code == 401
