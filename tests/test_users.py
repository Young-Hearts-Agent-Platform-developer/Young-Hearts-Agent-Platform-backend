import uuid
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def register_user(username, password, roles=None):
    payload = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "gender": "male",
        "nickname": "Test User",
    }
    if roles is not None:
        # 明确 roles 只允许 List[str]，不做类型兼容
        assert isinstance(roles, list) and all(isinstance(r, str) for r in roles)
        payload["roles"] = roles
    r = client.post("/api/users/register", json=payload)
    assert r.status_code == 201, r.text
    return r.json()

def login_user(username, password, use_cookie=False):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    data = r.json()
    session_id = data.get("session_id")
    # Web端用cookie
    if use_cookie:
        cookies = r.cookies
        return session_id, cookies
    # App端用header
    return session_id, {"X-Session-ID": session_id}

def logout_user(session_id=None, cookies=None):
    if cookies:
        r = client.post("/api/auth/logout", cookies=cookies)
    elif session_id:
        r = client.post("/api/auth/logout", headers={"X-Session-ID": session_id})
    else:
        r = client.post("/api/auth/logout")
    assert r.status_code == 200, r.text

def get_me(headers=None, cookies=None):
    if cookies:
        r = client.get("/api/users/me", cookies=cookies)
    elif headers:
        r = client.get("/api/users/me", headers=headers)
    else:
        r = client.get("/api/users/me")
    return r

def test_register_login_logout_web_and_app():
    username = f"webappuser_{uuid.uuid4().hex[:8]}"
    password = "testpass123"
    # 注册
    register_user(username, password)
    # Web端登录（cookie）
    session_id_web, cookies = login_user(username, password, use_cookie=True)
    r = get_me(cookies=cookies)
    assert r.status_code == 200
    assert r.json()["username"] == username
    # App端登录（header）
    session_id_app, headers = login_user(username, password, use_cookie=False)
    r2 = get_me(headers=headers)
    assert r2.status_code == 200
    assert r2.json()["username"] == username
    # 登出后会话失效
    logout_user(session_id=session_id_app)
    r3 = get_me(headers=headers)
    assert r3.status_code == 401
    logout_user(cookies=cookies)
    r4 = get_me(cookies=cookies)
    assert r4.status_code == 401

def test_role_permission_and_sensitive_field():
    # 注册多角色用户
    username = f"roleuser_{uuid.uuid4().hex[:8]}"
    password = "testpass123"
    roles = ["user", "expert"]
    resp = register_user(username, password, roles=roles)
    # 注册返回 roles 必须为 List[str]
    assert isinstance(resp["roles"], list)
    assert set(resp["roles"]) == set(roles)
    session_id, headers = login_user(username, password)
    # 访问需要 expert 角色的接口
    r = client.get("/protected/expert", headers=headers)
    assert r.status_code == 200
    # 访问需要 volunteer 角色的接口应 403
    r2 = client.get("/protected/volunteer", headers=headers)
    assert r2.status_code == 403
    # 敏感字段脱敏校验（如有）
    # r3 = client.get("/api/users/me", headers=headers)
    # assert "sensitive_field" not in r3.json()  # 示例

def test_session_expiry():
    username = f"expireuser_{uuid.uuid4().hex[:8]}"
    password = "testpass123"
    register_user(username, password)
    session_id, headers = login_user(username, password)
    # 模拟会话过期（假设有接口可强制失效）
    client.post("/debug/expire_session", headers=headers)
    r = get_me(headers=headers)
    assert r.status_code == 401

def test_register_duplicate():
    username = f"dupuser_{uuid.uuid4().hex[:8]}"
    password = "testpass123"
    register_user(username, password)
    r = client.post("/api/users/register", json={
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "gender": "male",
        "nickname": "Test User",
    })
    assert r.status_code in (400, 409)

# --- 分角色注册功能 Phase 4: 多角色注册与 profile 测试 ---
import pytest

def test_register_multi_roles_and_profiles():
    """注册多角色用户，校验 profile 创建与状态"""
    username = f"multi_{uuid.uuid4().hex[:8]}"
    password = "testpass123"
    roles = ["family", "volunteer", "expert"]
    payload = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "gender": "male",
        "nickname": "多角色用户",
        "roles": roles,
        "volunteer_info": {
            "full_name": "志愿者张三",
            "phone": "13800000000",
            "skills": ["陪伴", "心理疏导"],
            "is_public_visible": True
        },
        "expert_info": {
            "full_name": "专家李四",
            "title": "心理咨询师",
            "organization": "XX医院",
            "qualifications": ["cert1.pdf"],
            "specialties": ["孤独症干预"],
            "is_public_visible": False
        }
    }
    r = client.post("/api/users/register", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert set(data["roles"]) == set(roles)
    # 检查 profile 信息
    assert "volunteer_profile" in data and data["volunteer_profile"]["status"] == "pending"
    assert "expert_profile" in data and data["expert_profile"]["status"] == "pending"

def test_register_admin_maintainer_forbidden():
    """注册管理员/维护人员应被拦截"""
    username = f"admin_{uuid.uuid4().hex[:8]}"
    password = "testpass123"
    for role in ["admin", "maintainer"]:
        payload = {
            "username": f"{username}_{role}",
            "password": password,
            "email": f"{username}_{role}@example.com",
            "gender": "male",
            "nickname": "非法角色",
            "roles": [role]
        }
        r = client.post("/api/users/register", json=payload)
        assert r.status_code in (400, 403)

def test_profile_required_for_roles():
    """注册志愿者/专家缺 profile 信息应报错"""
    username = f"noprofile_{uuid.uuid4().hex[:8]}"
    password = "testpass123"
    # 缺 volunteer_info
    payload = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "gender": "male",
        "nickname": "无profile",
        "roles": ["volunteer"]
    }
    r = client.post("/api/users/register", json=payload)
    assert r.status_code in (400, 422)
    # 缺 expert_info
    payload["roles"] = ["expert"]
    r2 = client.post("/api/users/register", json=payload)
    assert r2.status_code in (400, 422)
