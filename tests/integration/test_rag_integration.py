import pytest
from fastapi.testclient import TestClient
from app.tasks.knowledge_tasks import process_knowledge_document
from app.core.config import settings
from app.services.rag.vectorstore.chroma import get_chroma_collection
import json
import uuid

@pytest.mark.integration
def test_end_to_end_rag_flow(client: TestClient, admin_token: dict, db):
    # 1. 确保使用测试专用的 Chroma 集合
    # 为了避免并发冲突，使用 UUID 生成唯一的集合名
    test_collection_name = f"test_knowledge_base_{uuid.uuid4().hex[:8]}"
    original_collection_name = settings.CHROMA_COLLECTION_NAME
    settings.CHROMA_COLLECTION_NAME = test_collection_name
    
    try:
        # 2. 创建知识条目 (包含罕见词汇以便于检索验证)
        rare_keyword = "测试专用罕见词汇X99"
        knowledge_data = {
            "title": "集成测试文档",
            "content": f"这是一个用于集成测试的文档。核心知识点是：{rare_keyword}代表一种特殊的测试状态。",
            "category": "test",
            "risk_level": "low",
            "status": "published"
        }
        
        resp = client.post("/api/knowledge/items", json=knowledge_data, headers=admin_token)
        assert resp.status_code == 200
        doc_id = resp.json()["id"]
        
        # 3. 同步执行向量化任务 (绕过 Celery)
        process_knowledge_document(doc_id)
        
        # 4. 创建咨询会话
        resp = client.post("/api/consult/sessions", json={"topic": "测试会话"}, headers=admin_token)
        assert resp.status_code == 200
        session_id = resp.json()["id"]
        
        # 5. 发起 RAG 对话请求
        chat_req = {
            "query": f"请问{rare_keyword}代表什么？",
            "role": "friend",
            "session_id": session_id
        }
        
        # 由于是流式接口，需要特殊处理响应
        with client.stream("POST", "/api/consult/chat", json=chat_req, headers=admin_token) as response:
            assert response.status_code == 200
            full_response = ""
            current_event = None
            for line in response.iter_lines():
                if line.startswith("event: "):
                    current_event = line[7:]
                elif line.startswith("data: "):
                    data_str = line[6:]
                    if data_str != "[DONE]":
                        try:
                            data = json.loads(data_str)
                            if current_event == "message" and isinstance(data, dict):
                                full_response += data.get("content", "")
                        except json.JSONDecodeError:
                            pass
            
            # 6. 断言大模型回答中包含了我们注入的知识
            assert "特殊的测试状态" in full_response
            
    finally:
        # 7. 清理测试数据
        try:
            vectorstore = get_chroma_collection(settings.CHROMA_COLLECTION_NAME)
            vectorstore.delete_collection()
        except Exception as e:
            print(f"Failed to delete test collection: {e}")
        
        # 恢复原始集合名
        settings.CHROMA_COLLECTION_NAME = original_collection_name
