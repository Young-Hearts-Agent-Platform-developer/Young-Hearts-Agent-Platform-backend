from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.responses import StreamingResponse, JSONResponse
from app.rag.service import async_chat_with_rag, save_ai_message
from app.services.auth import get_current_user
from app.services.consultation_service import ConsultationService
from app.db.session import get_db
from app.schemas.consultation import ConsultationSessionCreate, ConsultationSession, ConsultationMessageCreate, ConsultationMessage
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, AsyncGenerator, List, Any
import json

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    role: str
    reasoning_effort: Optional[str] = None
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
    
    async def event_stream() -> AsyncGenerator[str, None]:
        ai_reply = ""
        topic = None
        try:
            async for chunk in async_chat_with_rag(req.query, req.role, req.reasoning_effort):
                ai_reply += chunk
                yield chunk
        except Exception as e:
            # 流式输出异常时，前端可感知
            yield f"[ERROR]{str(e)}"
            raise
        # AI回复持久化，sources 预留参数，当前为 None
        if req.session_id and ai_reply:
            retry = 0
            while retry < 2:
                try:
                    service.save_message(session_id=req.session_id, role="ai", content=ai_reply, sources=None)
                    break
                except Exception as ex:
                    retry += 1
                    if retry >= 2:
                        # 兜底日志，实际可接入日志系统
                        print(f"[ERROR] AI消息持久化失败: {ex}")
            # 查询 session topic
            session = service.get_session(req.session_id)
            topic = getattr(session, "topic", None)
        # 尾包带上 topic 信息
        yield f"[TOPIC]{json.dumps({'topic': topic})}"
    return StreamingResponse(event_stream(), media_type="text/event-stream")
