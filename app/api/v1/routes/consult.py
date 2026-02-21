from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse
from app.services.rag.rag_service import async_chat_with_rag
from app.services.auth_service import get_current_user
from app.services.consultation_service import ConsultationService
from app.db.session import get_db
from app.schemas.consultation import ConsultationSession, ConsultationMessage
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, AsyncGenerator, List
import json

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    role: str
    reasoning_effort: Optional[str] = None  # 用于控制 AI 回答的复杂度、详细程度或推理方式
    session_id: Optional[int] = None
    # sources 字段不再由前端传递，仅后端持久化时预留


class SessionCreateRequest(BaseModel):
    topic: Optional[str] = None


def get_consult_service(db: Session = Depends(get_db)):
    return ConsultationService(db)


# 创建会话
@router.post("/sessions", response_model=ConsultationSession)
async def create_session(
    req: SessionCreateRequest,
    current_user=Depends(get_current_user),
    service: ConsultationService = Depends(get_consult_service)
):
    session = service.create_session(user_id=current_user.id, topic=req.topic or "")
    return session


# 会话列表（仅返回最近20条，无分页）
@router.get("/sessions", response_model=List[ConsultationSession])
async def list_sessions(
    current_user=Depends(get_current_user),
    service: ConsultationService = Depends(get_consult_service)
):
    return service.list_sessions_recent(user_id=current_user.id, roles=current_user.roles)


# 会话详情（消息列表，分页）
@router.get("/sessions/{session_id}", response_model=List[ConsultationMessage])
async def get_session_detail(
    session_id: int = Path(...),
    current_user=Depends(get_current_user),
    service: ConsultationService = Depends(get_consult_service)
):
    return service.list_messages_all(session_id=session_id, user_id=current_user.id, roles=current_user.roles)


# 删除会话
@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int = Path(...),
    current_user=Depends(get_current_user),
    service: ConsultationService = Depends(get_consult_service)
):
    service.delete_session(session_id=session_id, user_id=current_user.id, roles=current_user.roles)
    return {"msg": "deleted"}


# 咨询对话（流式，支持 session_id，AI回复持久化）
@router.post("/chat")
async def consult_chat(
    req: ChatRequest,
    current_user=Depends(get_current_user),
    service: ConsultationService = Depends(get_consult_service)
):

    # 先持久化用户消息，异常时返回 500
    if not req.session_id or not req.query:
        raise HTTPException(status_code=400, detail="session_id 和 query 不能为空")
    try:
        service.save_message(
            session_id=req.session_id,
            role="user",
            content=req.query,
            sources=None
        )
    except Exception as ex:
        # 可接入日志系统
        print(f"[ERROR] 用户消息持久化失败: {ex}")
        raise HTTPException(status_code=500, detail="用户消息持久化失败")
    
    def _format_sse(event: str, data) -> str:
        """
        格式化为 SSE 消息字符串。
        Args:
            event: 事件类型 (message, topic, error, done)
            data: 数据载荷。
                - 如果是 dict，将被 json.dumps
                - 如果是 str 且 event != 'done'，将被封装为 {"content": str} 后 dumps (针对 message)
                - 如果是 'done' 事件，data 保持原样 (通常为 [DONE])
        """
        payload = ""
        if event == "done":
            payload = str(data)
        elif event == "message" and isinstance(data, str):
            payload = json.dumps({"content": data}, ensure_ascii=False)
        else:
            payload = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {payload}\n\n"

    async def event_stream() -> AsyncGenerator[str, None]:
        ai_reply = ""
        topic = None
        user_first_query = req.query
        error_flag = False
        error_msg = ""
        # session_id 缺失，直接返回 error 和 done
        if not req.session_id:
            yield _format_sse("error", {"detail": "session_id missing"})
            yield _format_sse("done", "[DONE]")
            return
        try:
            async for chunk in async_chat_with_rag(req.query, req.role, req.reasoning_effort):
                ai_reply += chunk
                yield _format_sse("message", chunk)
        except Exception as e:
            error_flag = True
            error_msg = str(e)
            yield _format_sse("error", {"detail": error_msg})
        # AI回复异常或无内容，不生成 topic，尾包返回 error 和 done
        if error_flag or not ai_reply:
            if not error_flag:  # 如果没有异常，但无内容
                yield _format_sse("error", {"detail": "AI回复为空"})
            yield _format_sse("done", "[DONE]")
            return
        # AI回复持久化并生成 topic
        retry = 0
        while retry < 2:
            try:
                service.save_ai_message_and_generate_topic(
                    session_id=req.session_id,
                    ai_content=ai_reply,
                    user_content=user_first_query,
                    sources=None
                )
                break
            except Exception as ex:
                retry += 1
                if retry >= 2:
                    print(f"[ERROR] AI消息持久化失败: {ex}")
                    yield _format_sse("error", {"detail": "AI消息持久化失败"})
                    yield _format_sse("done", "[DONE]")
                    return
        # 查询 session topic
        session = service.get_session(req.session_id)
        topic = getattr(session, "topic", None)
        # 尾包带上 topic 信息 和 done
        yield _format_sse("topic", {"topic": topic})
        yield _format_sse("done", "[DONE]")
    return StreamingResponse(event_stream(), media_type="text/event-stream")
