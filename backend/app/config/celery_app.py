"""Celery 应用：Redis 既做 broker 也做 result backend。"""
from celery import Celery

from app.config.settings import settings

celery_app = Celery(
    "texforge",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.generate_texture",
        "app.tasks.pack_channels",
        "app.tasks.cleanup_orphan_files",
    ],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    worker_max_tasks_per_child=50,
)
