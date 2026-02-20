# 功能测试脚本：AI对话流式输出及自动生成标题（方法直调版）
# 说明：本脚本直接调用后端方法（不走API），覆盖会话创建、AI流式回复、topic生成等主流程与关键边界情况。
# 依赖：标准库+SQLAlchemy+langchain-openai等，需本地配置好数据库和ARK_API_KEY。

import asyncio
import sys
import os
from app.db.session import SessionLocal, init_db
from app.models.user import User
from app.services.consultation_service import ConsultationService
from app.services.rag.service import async_chat_with_rag


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


def print_divider(title):
    print("\n" + "=" * 10 + f" {title} " + "=" * 10)


def create_test_user(db):
    # 若已存在则复用
    user = db.query(User).filter(User.username == "testuser").first()
    if user:
        return user
    user = User(username="testuser", password_hash="test", roles=["family"])
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_session(service, user_id, topic=""):
    session = service.create_session(user_id=user_id, topic=topic)
    # session.id 可能为 SQLAlchemy Column，需要取实际值
    session_id = getattr(session, "id", None)
    if hasattr(session_id, "__class__") and "Column" in str(type(session_id)):
        # Column对象，取数据库刷新后的值
        session_id = session.__dict__.get("id")
    print(f"[Session] 新会话创建成功，session_id={session_id}")
    return session_id


async def stream_chat_print(query, role, reasoning_effort=None):
    print("[Stream] AI回复流式输出：")
    ai_reply = ""
    async for chunk in async_chat_with_rag(query, role, reasoning_effort):
        print(chunk, end="", flush=True)
        ai_reply += chunk
    print()
    return ai_reply


def get_session_topic(service, session_id):
    session = service.get_session(session_id)
    return getattr(session, "topic", None)


if __name__ == "__main__":
    print_divider("AI对话流式输出主流程（方法直调）")
    init_db()
    db = SessionLocal()
    user = create_test_user(db)
    service = ConsultationService(db)

    # 1. 创建新会话
    session_id = create_session(service, user.id)
    assert session_id, "会话创建失败，无法继续测试"

    # 2. 发送用户提问，流式获取AI回复
    user_query = "我最近总是失眠，怎么办？"
    ai_reply = asyncio.run(stream_chat_print(user_query, "counselor"))
    # AI回复持久化
    # 确保传入的是int类型session_id
    real_session_id = int(session_id) if not isinstance(session_id, int) and session_id is not None else session_id
    service.save_message(real_session_id, role="ai", content=ai_reply)
    # topic生成（模拟首次AI回复后自动生成）
    topic = get_session_topic(service, session_id)
    print(f"[Result] AI回复: {ai_reply[:50]}...\n[Result] 自动生成topic: {topic}")

    # 3. 再次发送消息，topic不应再变化
    print_divider("AI对话流式输出-多轮会话topic不变")
    ai_reply2 = asyncio.run(stream_chat_print("谢谢你的建议！", "counselor"))
    service.save_message(real_session_id, role="ai", content=ai_reply2)
    topic2 = get_session_topic(service, session_id)
    assert topic2 == topic, f"多轮会话topic应保持不变，期望: {topic}，实际: {topic2}"
    print(f"[Result] 多轮会话topic未变: {topic2}")

    # 4. 边界情况：无session_id
    print_divider("边界情况-无session_id")
    try:
        ai_reply3 = asyncio.run(stream_chat_print("测试无session_id", "counselor"))
        print(f"[Result] AI回复: {ai_reply3}")
    except Exception as e:
        print(f"[EdgeCase] 无session_id异常: {e}")

    # 5. 边界情况：AI回复异常
    print_divider("边界情况-AI回复异常")
    try:
        ai_reply4 = asyncio.run(stream_chat_print("", "invalid_role"))
        print(f"[Result] AI回复: {ai_reply4}")
    except Exception as e:
        print(f"[EdgeCase] AI回复异常: {e}")

    print_divider("全部测试完成")
    print("如需测试鉴权，可补充用户角色。请确保本地数据库和ARK_API_KEY等配置正确。")
