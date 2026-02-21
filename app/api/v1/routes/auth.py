
from fastapi import APIRouter, Request, Response, status, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserLogin, UserOut, UserUpdate, UserRegisterRequest, LoginResponse
from app.services import auth_service
from app.services import user_service
from app.services.user_service import update_user, delete_user
from app.services.auth_service import get_current_user, require_roles

router = APIRouter()


# ===== 以下接口迁移自 users.py =====

# 仅允许登录用户访问，示例：普通用户和志愿者均可
@router.get("/me", response_model=UserOut)
@require_roles(["user", "family", "volunteer", "expert", "admin"])
async def read_users_me(current_user=Depends(get_current_user)):
    # 敏感字段按角色脱敏示例
    if hasattr(current_user, 'model_dump'):
        user_dict = current_user.model_dump()
    elif hasattr(current_user, '__dict__'):
        user_dict = vars(current_user)
    else:
        user_dict = {}
    # 只依赖 schema 校验，roles 必为 List[str]
    if "admin" not in current_user.roles and "expert" not in current_user.roles:
        user_dict.pop("phone", None)
    return user_dict


# 仅允许本人或管理员修改
@router.put("/me", response_model=UserOut)
@require_roles(["user", "family", "admin"])
async def update_me(payload: UserUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        data.pop("password")
    user = update_user(db, current_user, data)
    return user


# 仅允许本人或管理员注销
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
@require_roles(["user", "family", "admin"])
async def delete_me(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    delete_user(db, current_user)
    return None


# 登录接口：成功后写 session 表，Web 端 set_cookie，App 端返回 session_id
@router.post("/login", response_model=LoginResponse)
async def login(user_in: UserLogin, response: Response, request: Request):
    user, session_id = await auth_service.login(user_in, request)
    user_agent = request.headers.get("user-agent", "")
    # 简单判断：web端用cookie，app端返回session_id
    if "web" in user_agent.lower():
        # 使用 SameSite=None 时需要同时设置 Secure=True（现代浏览器要求）
        response.set_cookie(key="session_id", value=session_id, httponly=True, samesite="none", secure=True)
    return LoginResponse(user=user, session_id=session_id)


# 登出接口：清理 session 表记录，清除 Cookie/Header
@router.post("/logout")
async def logout(request: Request, response: Response):
    await auth_service.logout(request)
    user_agent = request.headers.get("user-agent", "")
    if "web" in user_agent.lower():
        response.delete_cookie(key="session_id")
    return {"msg": "logout success"}


# 分角色注册接口：支持多角色、profile 创建、详细返回
@router.post("/register", response_model=UserOut)
async def register(user_in: UserRegisterRequest):
    """
    注册接口：支持多角色注册，自动创建 profile，事务一致性，返回详细信息。
    管理员/维护人员注册拦截。
    """
    from sqlalchemy.orm import Session
    from app.db.session import get_db

    db: Session = next(get_db())
    # 拦截管理员/维护人员注册
    if any(role in ["admin", "maintainer"] for role in user_in.roles):
        raise HTTPException(status_code=403, detail="管理员/维护人员仅允许后台创建")
    try:
        # 事务开始
        user = user_service.create_user(db, user_in)
        volunteer_profile = None
        expert_profile = None
        if "volunteer" in user_in.roles and user_in.volunteer_info is not None:
            from app.models.user import VolunteerProfile
            v = user_in.volunteer_info
            volunteer_profile = VolunteerProfile(
                user_id=user.id,
                full_name=getattr(v, "full_name", None),
                phone=getattr(v, "phone", None),
                public_email=getattr(v, "public_email", None),
                is_public_visible=getattr(v, "is_public_visible", False),
                skills=str(getattr(v, "skills", []) or []),
                status="pending",
                work_status="offline"
            )
            db.add(volunteer_profile)
        if "expert" in user_in.roles and user_in.expert_info is not None:
            from app.models.user import ExpertProfile
            e = user_in.expert_info
            expert_profile = ExpertProfile(
                user_id=user.id,
                full_name=getattr(e, "full_name", None),
                phone=getattr(e, "phone", None),
                public_email=getattr(e, "public_email", None),
                title=getattr(e, "title", None),
                org=getattr(e, "org", None),
                skills=str(getattr(e, "skills", []) or []),
                status="pending"
            )
            db.add(expert_profile)
        db.commit()
        db.refresh(user)
        # 查询 profile 详细信息
        if volunteer_profile:
            db.refresh(volunteer_profile)
        if expert_profile:
            db.refresh(expert_profile)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"注册失败: {e}")

    # 构造返回
    from app.schemas.user import UserOut, VolunteerProfileOut, ExpertProfileOut
    # 用 dict 构造，避免 from_orm
    user_dict = {**user.__dict__}
    import json
    # 兼容 roles 字段为 JSON 字符串的情况
    roles = user_dict.get("roles")
    if isinstance(roles, str):
        try:
            user_dict["roles"] = json.loads(roles)
        except Exception:
            user_dict["roles"] = []
    if volunteer_profile:
        # 修正 skills 字段类型为 list
        volunteer_profile_dict = dict(volunteer_profile.__dict__)
        if isinstance(volunteer_profile_dict.get("skills"), str):
            import json
            try:
                volunteer_profile_dict["skills"] = json.loads(volunteer_profile_dict["skills"])
            except Exception:
                volunteer_profile_dict["skills"] = []
        user_dict["volunteer_profile"] = VolunteerProfileOut(**volunteer_profile_dict)
    if expert_profile:
        # 修正 skills 字段类型为 list
        expert_profile_dict = dict(expert_profile.__dict__)
        if isinstance(expert_profile_dict.get("skills"), str):
            import json
            try:
                expert_profile_dict["skills"] = json.loads(expert_profile_dict["skills"])
            except Exception:
                expert_profile_dict["skills"] = []
        user_dict["expert_profile"] = ExpertProfileOut(**expert_profile_dict)
    user_out = UserOut(**user_dict)
    return user_out
