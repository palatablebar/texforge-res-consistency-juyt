"""TexForge 后端入口：中间件按 auth -> quota -> audit 顺序注册，启动时建表 + seed。"""
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.database import Base, SessionLocal, engine
from app.config.settings import settings
from app.middlewares.audit_logger import audit_middleware
from app.middlewares.auth import auth_middleware
from app.middlewares.error_handler import app_error_handler, request_id_middleware_factory, unhandled_error_handler
from app.middlewares.quota import quota_middleware
from app.routes import audit, auth, files, health, node, pack, quota, recipe, variant
from app.utils.errors import AppError
from app.utils.logger import log_event
from app.utils.storage import ensure_dirs


def _watchdog_loop() -> None:
    """兜底：生成任务卡在 generating 超过 60 秒时由后端同步补算，保证演示不断链。"""
    while True:
        time.sleep(20)
        try:
            from app.models.texture_variant import TextureVariant
            from app.services.variant_service import perform_generation

            db = SessionLocal()
            try:
                cutoff = datetime.utcnow() - timedelta(seconds=60)
                stuck = (
                    db.query(TextureVariant)
                    .filter(TextureVariant.status == "generating", TextureVariant.created_at < cutoff)
                    .all()
                )
                for row in stuck:
                    try:
                        perform_generation(db, row.id)
                    except Exception:  # noqa: BLE001
                        db.rollback()
            finally:
                db.close()
        except Exception:  # noqa: BLE001
            continue


def _run_seed() -> None:
    try:
        from scripts.seed_demo import seed_demo

        seed_demo()
    except Exception as exc:  # noqa: BLE001 - seed 失败不阻塞启动
        log_event("SEED_DEMO_FAILED", error=str(exc))


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    Base.metadata.create_all(bind=engine)
    if settings.SEED_DEMO:
        _run_seed()
    thread = threading.Thread(target=_watchdog_loop, daemon=True, name="texforge-watchdog")
    thread.start()
    yield


app = FastAPI(
    title="TexForge API",
    description="过程式材质纹理生成与通道打包工坊 · 后端",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

quota_middleware(app)
auth_middleware(app)
audit_middleware(app)
request_id_middleware_factory(app)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(recipe.router)
app.include_router(node.router)
app.include_router(variant.router)
app.include_router(pack.router)
app.include_router(quota.router)
app.include_router(files.router)
app.include_router(audit.router)


@app.get("/")
def root():
    return {
        "service": "texforge-backend",
        "name": settings.PROJECT_NAME,
        "docs": "/docs",
        "frontend": "http://localhost:18111",
    }
