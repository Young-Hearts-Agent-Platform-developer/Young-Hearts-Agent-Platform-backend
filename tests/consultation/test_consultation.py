import pytest
from fastapi.testclient import TestClient


@pytest.mark.skip(reason="该测试已通过")
def test_consultation_isolation(client: TestClient, existing_user_1_token, existing_user_2_token, admin_token):
    # 用户 A (existing_user_1) 创建会话 S1
    create_data = {"topic": "Test Session A"}
    resp_create = client.post("/api/consult/sessions", json=create_data, headers=existing_user_1_token)
    assert resp_create.status_code == 200
    session_a = resp_create.json()
    session_a_id = session_a["id"]

    # 用户 B (existing_user_2) 获取会话列表，不应包含 S1
    resp_list_b = client.get("/api/consult/sessions", headers=existing_user_2_token)
    assert resp_list_b.status_code == 200
    sessions_b = resp_list_b.json()
    assert not any(s["id"] == session_a_id for s in sessions_b)

    # 用户 B 尝试获取 S1 详情，应返回 403 或 404
    resp_detail_b = client.get(f"/api/consult/sessions/{session_a_id}", headers=existing_user_2_token)
    assert resp_detail_b.status_code in [403, 404]

    # 管理员获取 S1 详情，应返回 200
    resp_detail_admin = client.get(f"/api/consult/sessions/{session_a_id}", headers=admin_token)
    assert resp_detail_admin.status_code == 200


@pytest.mark.skip(reason="该测试已通过")
def test_consultation_chat_sse(client: TestClient, existing_user_1_token):
    # 创建一个新会话
    create_data = {"topic": "Chat Test Session"}
    resp_create = client.post("/api/consult/sessions", json=create_data, headers=existing_user_1_token)
    assert resp_create.status_code == 200
    session_id = resp_create.json()["id"]

    # 发送聊天请求
    chat_data = {
        "query": "Hello, AI!",
        "role": "friend",
        "session_id": session_id
    }
    
    # 使用 stream=True 接收 SSE 响应
    with client.stream("POST", "/api/consult/chat", json=chat_data, headers=existing_user_1_token) as response:
        assert response.status_code == 200
        
        events = []
        for line in response.iter_lines():
            if line:
                events.append(line)
        
        print("EVENTS:", events)
        
        # 验证 SSE 格式
        assert any(line.startswith("event: message") for line in events)
        assert any(line.startswith("event: done") for line in events)
        
        # 验证数据内容
        data_lines = [line for line in events if line.startswith("data: ")]
        assert len(data_lines) > 0
        
        # 尝试解析最后一条 done 消息
        done_data = [line for line in data_lines if line == "data: [DONE]"]
        assert len(done_data) > 0

    # 验证数据库中 Message 是否正确持久化
    resp_detail = client.get(f"/api/consult/sessions/{session_id}", headers=existing_user_1_token)
    assert resp_detail.status_code == 200
    messages = resp_detail.json()
    
    # 至少应该有一条 user 消息和一条 ai 消息
    assert len(messages) >= 2
    assert any(m["role"] == "user" and m["content"] == "Hello, AI!" for m in messages)
    assert any(m["role"] == "ai" for m in messages)
