from celery import Celery
from app.core.config import settings

# 简单的 Celery 配置，使用 Redis 作为 broker 和 backend
celery_app = Celery(
    "young_hearts_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
)
