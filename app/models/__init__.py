from sqlalchemy.orm import declarative_base

Base = declarative_base()

# 导入所有模型以便 metadata 注册
from app.models import user  # noqa: F401, E402
from app.models.consultation import ConsultationSession, ConsultationMessage  # noqa: F401, E402
from app.models.knowledge import KnowledgeItem, KnowledgeChunk  # 新增，供 Alembic 识别
