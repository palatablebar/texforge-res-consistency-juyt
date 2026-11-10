"""Celery 周期任务：清理共享卷里不被任何变体引用的目录（默认手动触发）。"""
import os

from app.config.celery_app import celery_app
from app.config.database import SessionLocal
from app.config.settings import settings
from app.models.texture_variant import TextureVariant
from app.utils.logger import log_event


@celery_app.task(name="texforge.cleanup_orphan_files")
def cleanup_orphan_files() -> dict:
    db = SessionLocal()
    removed = 0
    kept = 0
    try:
        referenced = set()
        for variant in db.query(TextureVariant).all():
            for rel in (variant.file_paths_json or {}).values():
                referenced.add(os.path.dirname(rel))
        for root in (settings.ARTIFACT_DIR, settings.PREVIEW_DIR):
            if not os.path.isdir(root):
                continue
            for slug in os.listdir(root):
                slug_dir = os.path.join(root, slug)
                if not os.path.isdir(slug_dir):
                    continue
                for rev in os.listdir(slug_dir):
                    rel = f"{slug}/{rev}"
                    if rel in referenced:
                        kept += 1
                    else:
                        import shutil

                        shutil.rmtree(os.path.join(slug_dir, rev), ignore_errors=True)
                        removed += 1
        log_event("CLEANUP_ORPHAN_FILES", removed=removed, kept=kept)
        return {"removed": removed, "kept": kept}
    finally:
        db.close()
