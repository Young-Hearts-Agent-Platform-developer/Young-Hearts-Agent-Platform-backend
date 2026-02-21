from typing import Optional, List, Literal
from pydantic import BaseModel, model_validator, field_validator, ConfigDict
from datetime import datetime
import json

# 用户角色类型
UserRole = Literal["family", "volunteer", "expert", "admin", "maintainer"]


# 登录用 Pydantic 模型
class UserLogin(BaseModel):
    username: str
    password: str


class UserBase(BaseModel):
    username: Optional[str]
    email: Optional[str]
    gender: Optional[str] = "hidden"  # ['male', 'female', 'hidden']
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    roles: List[UserRole] = []  # 只接受/输出 List[str]，由 ORM 层保证为 JSON 字符串
    status: Optional[str] = "active"
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


# --- Profile Schemas ---
class VolunteerProfileCreate(BaseModel):
    full_name: str
    phone: str
    public_email: Optional[str] = None
    is_public_visible: Optional[bool] = False
    skills: Optional[List[str]] = []


class ExpertProfileCreate(BaseModel):
    full_name: str
    phone: str
    public_email: Optional[str] = None
    title: Optional[str] = None
    org: Optional[str] = None
    skills: Optional[List[str]] = []


# 注册请求 schema
class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    gender: Optional[str] = "hidden"
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    roles: List[UserRole]
    volunteer_info: Optional[VolunteerProfileCreate] = None
    expert_info: Optional[ExpertProfileCreate] = None

    @model_validator(mode="after")
    def check_profile_required(self):
        errors = []
        if "volunteer" in self.roles and not self.volunteer_info:
            errors.append("volunteer_info is required when role includes 'volunteer'")
        if "expert" in self.roles and not self.expert_info:
            errors.append("expert_info is required when role includes 'expert'")
        if errors:
            raise ValueError(", ".join(errors))
        return self


# 输出 profile schema
class VolunteerProfileOut(VolunteerProfileCreate):
    user_id: int
    service_hours: Optional[str] = "0"
    status: Optional[str] = "pending"
    work_status: Optional[str] = "offline"

    model_config = ConfigDict(from_attributes=True)


class ExpertProfileOut(ExpertProfileCreate):
    user_id: int
    status: Optional[str] = "pending"

    model_config = ConfigDict(from_attributes=True)


class UserOut(UserBase):
    id: int
    volunteer_profile: Optional[VolunteerProfileOut] = None
    expert_profile: Optional[ExpertProfileOut] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("roles", mode="before")
    @classmethod
    def parse_roles(cls, v):
        """只做 json.loads，保证 roles 为 List[str]"""
        if isinstance(v, str):
            return json.loads(v)
        return v


class LoginResponse(BaseModel):
    user: UserOut
    session_id: str


# Session Pydantic 模型
class SessionBase(BaseModel):
    session_id: str
    user_id: int
    created_at: datetime
    expired_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip: Optional[str] = None


class SessionCreate(BaseModel):
    user_id: int
    expired_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip: Optional[str] = None


class SessionOut(SessionBase):
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
