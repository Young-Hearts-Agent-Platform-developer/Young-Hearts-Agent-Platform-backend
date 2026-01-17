from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_db
# include routers
from app.api.v1.routes import auth as auth_router
from app.api.v1.routes import consult as consult_router
# openapi utils
from app.utils_openapi import generate_openapi_json



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
app.include_router(consult_router.router, prefix="/api/consult", tags=["consult"])


@app.get("/health")
def health():
    return {"status": "ok"}
