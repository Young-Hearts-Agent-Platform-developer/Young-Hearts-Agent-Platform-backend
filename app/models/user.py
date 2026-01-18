
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, JSON, ForeignKeyConstraint
from sqlalchemy.sql import func

from app.models import Base



# 用户主表
class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(150), nullable=False, unique=True)
    email = Column(String(320), unique=True)
    gender = Column(String(16), default="hidden")  # ['male', 'female', 'hidden']
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(255))
    avatar = Column(String(512))
    roles = Column(JSON, nullable=False, default=list, comment="用户角色，JSON 数组（如 ['user', 'admin']，原生 JSON 存储）")
    status = Column(String(32), default="active")  # ['active', 'banned', 'pending_review']
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())


# 志愿者扩展表
class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"

    user_id = Column(BigInteger, primary_key=True, nullable=False, comment="外键，关联 users.id")
    __table_args__ = (
        ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    full_name = Column(String(255))
    phone = Column(String(32))
    public_email = Column(String(320))
    is_public_visible = Column(Boolean, default=False)
    service_hours = Column(String(32), default="0")
    skills = Column(String(255), default='[]')  # JSON 字符串数组
    status = Column(String(32), default="pending")  # ['pending', 'approved', 'rejected']
    work_status = Column(String(32), default="offline")  # ['online', 'busy', 'offline']


# 专家扩展表
class ExpertProfile(Base):
    __tablename__ = "expert_profiles"

    user_id = Column(BigInteger, primary_key=True, nullable=False, comment="外键，关联 users.id")
    __table_args__ = (
        ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    full_name = Column(String(255))
    phone = Column(String(32))
    public_email = Column(String(320))
    title = Column(String(255))
    org = Column(String(255))
    skills = Column(String(255), default='[]')  # JSON 字符串数组
    status = Column(String(32), default="pending")


# Session 会话表
class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String(128), primary_key=True)
    user_id = Column(BigInteger)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    expired_at = Column(DateTime(timezone=False))
    user_agent = Column(String(255))
    ip = Column(String(64))
