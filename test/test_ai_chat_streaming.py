# AI 对话流式输出功能测试脚本
# 本脚本用于直接测试 app/rag/service.py 中的 async_chat_with_rag 方法，检验流式输出效果
# 仅依赖标准 Python，便于理解和维护
# 注意：需在本地配置好 ARK_API_KEY 环境变量，并确保相关依赖已安装

import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from app.rag.service import async_chat_with_rag

# 测试参数
TEST_QUERY = "你好，请帮我分析一下最近的情绪变化。"
TEST_ROLE = "counselor"  # 可选：counselor, friend
TEST_REASONING_EFFORT = "高"  # 可选：高、中、低 或 None

async def test_streaming_chat():
    print("--- AI 对话流式输出功能测试 ---")
    print(f"输入内容: {TEST_QUERY}")
    print(f"角色: {TEST_ROLE}")
    print(f"推理强度: {TEST_REASONING_EFFORT}")
    print("AI 回复（流式输出）:")
    # 调用 async_chat_with_rag，逐步输出结果
    async for chunk in async_chat_with_rag(TEST_QUERY, TEST_ROLE, TEST_REASONING_EFFORT):
        print(chunk, end='', flush=True)
    print("\n--- 测试结束 ---")

if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(test_streaming_chat())

# 边界情况测试
# 1. 空输入
# 2. 不存在的角色
# 3. reasoning_effort 为空
async def test_edge_cases():
    print("\n--- 边界情况测试 ---")
    cases = [
        {"query": "", "role": TEST_ROLE, "reasoning_effort": TEST_REASONING_EFFORT, "desc": "空输入"},
        {"query": TEST_QUERY, "role": "unknown_role", "reasoning_effort": TEST_REASONING_EFFORT, "desc": "不存在的角色"},
        {"query": TEST_QUERY, "role": TEST_ROLE, "reasoning_effort": None, "desc": "推理强度为空"},
    ]
    for case in cases:
        print(f"\n用例: {case['desc']}")
        try:
            async for chunk in async_chat_with_rag(case["query"], case["role"], case["reasoning_effort"]):
                print(chunk, end='', flush=True)
            print()
        except Exception as e:
            print(f"异常: {e}")
    print("--- 边界测试结束 ---")

if __name__ == "__main__":
    # 运行主流程测试
    asyncio.run(test_streaming_chat())
    # 运行边界情况测试
    asyncio.run(test_edge_cases())
