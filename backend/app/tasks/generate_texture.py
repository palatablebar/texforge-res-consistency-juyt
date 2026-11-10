"""Celery 任务：生成纹理六通道 + 预览 + 接缝评分。"""
from app.config.celery_app import celery_app
from app.config.database import SessionLocal
from app.utils.logger import log_event


@celery_app.task(name="texforge.generate_texture", bind=True, max_retries=2, default_retry_delay=5)
def generate_texture_task(self, variant_id: int):
    from app.services.variant_service import perform_generation

    db = SessionLocal()
    try:
        perform_generation(db, variant_id)
        return {"variant_id": variant_id, "status": "ready"}
    except Exception as exc:  # noqa: BLE001
        log_event("GENERATION_FAILED", recipe_id=None, variant_id=variant_id, error=str(exc))
        raise
    finally:
        db.close()
