from fastapi import APIRouter
from sqlalchemy import text

from app.config.database import SessionLocal
from app.utils.cache import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    db_ok = False
    redis_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False
    try:
        redis_ok = bool(get_redis().ping())
    except Exception:  # noqa: BLE001
        redis_ok = False
    return {
        "status": "ok" if db_ok and redis_ok else "degraded",
        "service": "texforge-backend",
        "db": db_ok,
        "redis": redis_ok,
    }
