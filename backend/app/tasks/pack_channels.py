"""Celery 任务：按映射合成为 RGBA 打包 PNG。"""
from app.config.celery_app import celery_app
from app.config.database import SessionLocal


@celery_app.task(name="texforge.pack_channels", bind=True, max_retries=2, default_retry_delay=5)
def pack_channels_task(self, pack_id: int):
    from app.services.pack_service import perform_pack

    db = SessionLocal()
    try:
        perform_pack(db, pack_id)
        return {"pack_id": pack_id, "status": "ready"}
    finally:
        db.close()
