
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
	pass


# 导入所有模型以便 metadata 注册
from app.models import user  # noqa: F401
from app.models import knowledge  # noqa: F401
