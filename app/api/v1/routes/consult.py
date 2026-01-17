from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from app.rag.service import async_chat_with_rag
from app.services.auth import get_current_user
from pydantic import BaseModel
from typing import Optional, AsyncGenerator

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ChatRequest(BaseModel):
    query: str
    role: str
    reasoning_effort: Optional[str] = None

@router.post("/chat")
async def consult_chat(
    req: ChatRequest,
    current_user=Depends(get_current_user)
):
    try:
        async def event_stream() -> AsyncGenerator[str, None]:
            async for chunk in async_chat_with_rag(req.query, req.role, req.reasoning_effort):
                yield chunk
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
