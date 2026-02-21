import pytest
from fastapi.testclient import TestClient

def test_update_me_success(client: TestClient, normal_user_token):
    # 尝试修改 email 和 gender
    update_data = {
        "email": "newemail@example.com",
        "gender": "male"
    }
    response = client.put("/api/auth/me", json=update_data, headers=normal_user_token)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newemail@example.com"
    assert data["gender"] == "male"

    # 验证 GET /auth/me 也能获取到新数据
    response_get = client.get("/api/auth/me", headers=normal_user_token)
    assert response_get.status_code == 200
    data_get = response_get.json()
    assert data_get["email"] == "newemail@example.com"
    assert data_get["gender"] == "male"

def test_update_me_restricted_fields(client: TestClient, normal_user_token):
    # 尝试修改 password 和 roles
    # password 在路由中会被 pop 掉，roles 不在 UserUpdate schema 中，会被忽略
    update_data = {
        "password": "newpassword123",
        "roles": ["admin"]
    }
    response = client.put("/api/auth/me", json=update_data, headers=normal_user_token)
    # Pydantic 可能会忽略未定义的字段，或者路由中处理了
    assert response.status_code == 200
    
    # 验证 roles 没有被修改
    response_get = client.get("/api/auth/me", headers=normal_user_token)
    assert response_get.status_code == 200
    data_get = response_get.json()
    assert "admin" not in data_get["roles"]

    # 验证密码没有被修改（尝试用新密码登录应该失败）
    # 需要先获取用户名
    username = data_get["username"]
    login_data = {"username": username, "password": "newpassword123"}
    login_response = client.post("/api/auth/login", json=login_data)
    assert login_response.status_code == 401
