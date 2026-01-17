import os
import json
import openai
from typing import AsyncGenerator, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr

PROMPT_DIR = os.path.join(os.path.dirname(__file__), 'prompts')

ARK_API_KEY = os.getenv('ARK_API_KEY')
if not ARK_API_KEY:
    raise RuntimeError('ARK_API_KEY 环境变量未设置')

openai.api_key = ARK_API_KEY

# 加载 prompt 配置
def load_prompt(role: str) -> str:
    path = os.path.join(PROMPT_DIR, f"{role}.json")
    if not os.path.exists(path):
        raise ValueError(f"Prompt 配置不存在: {role}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('prompt', '')

async def async_chat_with_rag(query: str, role: str, reasoning_effort: Optional[str] = None) -> AsyncGenerator[str, None]:
    prompt = load_prompt(role)
    if reasoning_effort:
        prompt = prompt.replace("{reasoning_effort}", reasoning_effort)
    else:
        prompt = prompt.replace("{reasoning_effort}", "")
    llm = ChatOpenAI(api_key=SecretStr(ARK_API_KEY or ""), streaming=True)
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=query)
    ]
    async for chunk in llm.astream(messages):
        # chunk 可能为 str、对象或 list，需兼容处理
        if hasattr(chunk, 'content'):
            yield str(chunk.content)
        elif isinstance(chunk, str):
            yield chunk
        elif isinstance(chunk, list):
            for c in chunk:
                if isinstance(c, str):
                    yield c
                elif isinstance(c, tuple) and len(c) > 0:
                    yield str(c[0])
