from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
 
from app.core.config import settings
from app.db.session import init_db
from app.utils_openapi import generate_openapi_json
# --- 注册所有模型，确保 Base.metadata 包含知识库相关表 ---
from app.models.user import User
from app.models.knowledge import KnowledgeItem, KnowledgeChunk
# include routers
from app.api.v1.routes import auth as auth_router
try:
    from app.api.v1.routes import knowledge as knowledge_router
except Exception:
    knowledge_router = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize DB / indexes if needed
    init_db()
    # 生成 openapi.json
    generate_openapi_json(app, output_path="openapi.json")
    yield

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# 添加 CORS 中间件，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://10.15.9.148:5173",
        "http://localhost:5173"
    ],  # 可根据实际情况指定前端地址，如 ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# register API routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
if knowledge_router is not None:
    app.include_router(knowledge_router.router, prefix="/api", tags=["knowledge"])

@app.get("/health")
def health():
    return {"status": "ok"}
