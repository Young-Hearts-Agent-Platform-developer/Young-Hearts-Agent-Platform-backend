import os
import json
from typing import AsyncGenerator, Optional

import openai
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

PROMPT_DIR = os.path.join(os.path.dirname(__file__), 'prompts')

ARK_API_KEY = settings.ark_api_key
ARK_BASE_URL = settings.ark_base_url
ARK_MODEL = settings.ark_model
if not ARK_API_KEY:
    raise RuntimeError('ARK_API_KEY 环境变量未设置')
if not ARK_BASE_URL:
    raise RuntimeError('ARK_BASE_URL 环境变量未设置')
if not ARK_MODEL:
    raise RuntimeError('ARK_MODEL 环境变量未设置')

openai.api_key = ARK_API_KEY
openai.base_url = ARK_BASE_URL

# 加载 prompt 配置
def load_prompt(role: str) -> str:
    path = os.path.join(PROMPT_DIR, f"{role}.json")
    if not os.path.exists(path):
        raise ValueError(f"Prompt 配置不存在: {role}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('prompt', '')

# 加载 topic 生成 prompt
def load_topic_prompt() -> str:
    path = os.path.join(PROMPT_DIR, "topic.json")
    if not os.path.exists(path):
        raise ValueError("Prompt 配置不存在: topic")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('prompt', '')

# topic 生成（同步，供服务层调用）
def generate_topic(user_message: str, ai_message: str) -> str:
    prompt = load_topic_prompt()
    prompt_filled = prompt.replace("{user_message}", user_message).replace("{ai_message}", ai_message)
    llm = ChatOpenAI(
        api_key=SecretStr(ARK_API_KEY or ""), 
        base_url=ARK_BASE_URL,
        model=str(ARK_MODEL or "gpt-3.5-turbo"), 
        temperature=0.7,                              # 生成随机性（0-1，值越高越灵活）  
        streaming=True)
    messages = [
        SystemMessage(content=prompt_filled)
    ]
    # 只取一次回复
    result = llm.invoke(messages)
    if hasattr(result, 'content'):
        return str(result.content).strip()
    return str(result).strip()

async def async_chat_with_rag(query: str, role: str, reasoning_effort: Optional[str] = None) -> AsyncGenerator[str, None]:
    prompt = load_prompt(role)
    if reasoning_effort:
        prompt = prompt.replace("{reasoning_effort}", reasoning_effort)
    else:
        prompt = prompt.replace("{reasoning_effort}", "")

    llm = ChatOpenAI(
        api_key=SecretStr(ARK_API_KEY or ""), 
        base_url=ARK_BASE_URL,
        model=str(ARK_MODEL or "gpt-3.5-turbo"), 
        temperature=0.7,                              # 生成随机性（0-1，值越高越灵活）  
        streaming=True)
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

# AI回复持久化辅助函数（供 consult.py 调用）
def save_ai_message(session_id: int, content: str, sources=None):
    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        from app.services.consultation_service import ConsultationService
        service = ConsultationService(db)
        retry = 0
        while retry < 2:
            try:
                service.save_message(session_id=session_id, role="ai", content=content, sources=sources)
                break
            except Exception as ex:
                retry += 1
                if retry >= 2:
                    print(f"[ERROR] AI消息持久化失败: {ex}")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
