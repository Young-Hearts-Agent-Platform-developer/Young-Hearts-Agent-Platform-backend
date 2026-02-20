from sqlalchemy.orm import Session
from app.models.user import User


def create_user(db: Session, user_in):
    """
    创建用户，roles 支持多角色，兼容 UserRegisterRequest。
    """
    from app.services.auth import get_password_hash
    from app.models.user import User
    import json
    user = User(
        username=user_in.username,
        email=getattr(user_in, "email", None),
        gender=getattr(user_in, "gender", "hidden"),
        password_hash=get_password_hash(user_in.password),
        nickname=getattr(user_in, "nickname", None),
        avatar=getattr(user_in, "avatar", None),
        roles=json.dumps(user_in.roles) if hasattr(user_in, "roles") else '[]',
        status=getattr(user_in, "status", "active"),
    )
    db.add(user)
    db.flush()  # 不提交，便于后续 profile 关联
    return user


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def update_user(db: Session, user: User, data: dict):
    for field, value in data.items():
        if hasattr(user, field) and value is not None:
            setattr(user, field, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User):
    db.delete(user)
    db.commit()
