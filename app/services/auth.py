from datetime import datetime, timedelta, timezone
from typing import cast

from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status, Request
from functools import wraps
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.user_service import get_user_by_username, get_user_by_id
from app.db.session import get_db
from app.models.user import Session as SessionModel, User
import secrets

# 初始化密码加密上下文，指定用 argon2 算法，自动处理过时的加密方式
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
# OAuth2 密码模式，指定 token URL（登录接口）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, cast(str, user.password_hash)):
        return None
    return user


# 权限装饰器：校验 current_user.roles
def require_roles(roles):
    import json
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or not hasattr(current_user, 'roles'):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限校验失败：未获取到用户信息或缺少 roles 属性")
            user_roles = getattr(current_user, 'roles', [])
            if isinstance(user_roles, str):
                user_roles = json.loads(user_roles)
            if not isinstance(user_roles, list):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限校验失败：user.roles 类型应为 list[str]，实际为 {type(user_roles).__name__}，值为 {user_roles}"
                )
            required_roles = set(roles)
            user_roles_set = set(user_roles)
            if not user_roles_set & required_roles:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"权限不足：用户角色 {list(user_roles_set)} 不包含所需角色 {list(required_roles)}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 登录：生成 session_id 并写入 session 表
async def login(user_in, request: Request):
    db: Session = next(get_db())
    user = get_user_by_username(db, user_in.username)
    if not user or not verify_password(user_in.password, getattr(user, "password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user_agent = request.headers.get("user-agent", "")
    ip = request.client.host if request.client else ""
    session_id = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expired_at = now + timedelta(minutes=getattr(settings, "SESSION_EXPIRE_MINUTES", 10080))
    session = SessionModel(
        session_id=session_id,
        user_id=user.id,
        created_at=now,
        expired_at=expired_at,
        user_agent=user_agent,
        ip=ip
    )
    db.add(session)
    db.commit()
    # 关键：刷新 user，转换为 Pydantic 模型，防止 DetachedInstanceError
    db.refresh(user)
    from app.schemas.user import UserOut
    user_out = UserOut.model_validate(user)
    return user_out, session_id

# 登出：清理 session 表记录，支持 Cookie/Header
async def logout(request: Request):
    db: Session = next(get_db())
    session_id = None
    if "session_id" in request.cookies:
        session_id = request.cookies["session_id"]
    elif "x-session-id" in request.headers:
        session_id = request.headers["x-session-id"]
    if session_id:
        db.query(SessionModel).filter(SessionModel.session_id == session_id).delete()
        db.commit()

# 注册：字段与校验对齐 API 设计
async def register(user_in):
    db: Session = next(get_db())
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    user = User(
        username=user_in.username,
        email=user_in.email,
        nickname=getattr(user_in, "nickname", None),
        avatar=getattr(user_in, "avatar", None),
        roles=str(user_in.roles) if user_in.roles else '[]',
        status=user_in.status or "active",
        is_active=True,
        password_hash=get_password_hash(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# 自动识别 Cookie/Header，查 session 表，注入 user
def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_id = None
    # 优先 Cookie
    if settings.SESSION_COOKIE_NAME in request.cookies:
        session_id = request.cookies[settings.SESSION_COOKIE_NAME]
        session_id_source = "cookie"
    elif request.headers.get("X-Session-ID"):
        session_id = request.headers.get("X-Session-ID")
        session_id_source = "header"
    else:
        session_id_source = None
    if not session_id:
        raise HTTPException(status_code=401, detail="SessionID required（未在 Cookie 或 Header 中找到 session_id）")
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=401, detail=f"Session 失效或不存在（session_id={session_id}，来源={session_id_source}）")
    expired_at = getattr(session, "expired_at", None)
    if expired_at is not None and isinstance(expired_at, datetime):
        now = datetime.now(timezone.utc)
        if expired_at.tzinfo is None:
            expired_at_utc = expired_at.replace(tzinfo=timezone.utc)
        else:
            expired_at_utc = expired_at.astimezone(timezone.utc)
        if expired_at_utc < now:
            raise HTTPException(status_code=401, detail=f"Session 已过期（session_id={session_id}，expired_at={expired_at_utc.isoformat()}，now={now.isoformat()}）")
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail=f"Session 关联用户不存在（user_id={session.user_id}，session_id={session_id}）")
    # 可选：校验用户状态
    if hasattr(user, "status") and getattr(user, "status", None) == "banned":
        raise HTTPException(status_code=403, detail=f"用户已被禁用（user_id={user.id}，username={user.username}）")
    return user
