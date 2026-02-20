import sys
import os
from unittest.mock import MagicMock
from app.db.session import SessionLocal
from app.services.consultation_service import ConsultationService
from app.models.user import User
import app.services.consultation_service  # Patch target

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


def create_test_user(db):
    user = db.query(User).filter(User.username == "test_idempotency").first()
    if not user:
        user = User(username="test_idempotency", password_hash="test", roles=["family"])
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def run_test():
    print(">>> 开始验证 topic 生成幂等性 Test...")
    db = SessionLocal()
    service = ConsultationService(db)
    
    try:
        user = create_test_user(db)
        # 1. 创建新会话
        session = service.create_session(user.id, "新对话")
        session_id = session.id
        print(f"[Setup] Created session {session_id} with topic: '{session.topic}'")

        # 保存原始函数以便恢复
        original_generate_topic = app.services.consultation_service.generate_topic
        
        # --- 第一次调用 ---
        # 模拟生成 "Topic A"
        app.services.consultation_service.generate_topic = MagicMock(return_value="Topic A")
        
        print("[Action] 第一次调用 save_ai_message_and_generate_topic (User query: 'Q1')...")
        service.save_ai_message_and_generate_topic(session_id, "AI response 1", "User query 1")
        
        db.expire_all()  # 强制刷新
        session = service.get_session(session_id)
        print(f"[Check 1] Current topic is: '{session.topic}'")
        
        if session.topic != "Topic A":
            print("[Result] FAILED: Topic should be 'Topic A'")
            return
            
        # --- 第二次调用 ---
        # 模拟生成 "Topic B" (如果逻辑不正确，这里会被覆盖为 B)
        # 即使入参是新的 Q2/A2，topic 也不应该变
        app.services.consultation_service.generate_topic = MagicMock(return_value="Topic B")
        
        print("[Action] 第二次调用 save_ai_message_and_generate_topic (User query: 'Q2')...")
        service.save_ai_message_and_generate_topic(session_id, "AI response 2", "User query 2")
        
        db.expire_all()
        session = service.get_session(session_id)
        print(f"[Check 2] Current topic is: '{session.topic}'")
        
        if session.topic == "Topic A":
            print("[Result] SUCCESS: Topic remained 'Topic A'")
        else:
            print(f"[Result] FAILED: Topic changed to '{session.topic}' (Expected 'Topic A')")

    except Exception as e:
        print(f"[Error] 测试运行异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore
        if 'original_generate_topic' in locals():
            app.services.consultation_service.generate_topic = original_generate_topic
        db.close()


if __name__ == "__main__":
    run_test()
