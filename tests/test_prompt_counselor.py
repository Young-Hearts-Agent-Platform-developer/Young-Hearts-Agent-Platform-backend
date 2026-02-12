import sys
import os
import asyncio

# 添加项目根目录到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# 需要设置环境变量，或者确保 app.core.config 能加载 .env
# 为了保险起见，这里主动加载一下 dotenv，虽然 app.core.config 会尝试加载
from dotenv import load_dotenv
load_dotenv()

from app.rag.service import async_chat_with_rag

async def test_counselor_persona():
    query = "我家孩子3岁了，确诊孤独症，最近总是咬手，我该怎么办？"
    role = "counselor"
    print(f"User Query: {query}")
    print(f"Role: {role}")
    print("\n--- AI Response Start ---\n")
    
    try:
        async for chunk in async_chat_with_rag(query, role):
            print(chunk, end="", flush=True)
    except Exception as e:
        print(f"\nError: {e}")
    
    print("\n\n--- AI Response End ---")

if __name__ == "__main__":
    asyncio.run(test_counselor_persona())
