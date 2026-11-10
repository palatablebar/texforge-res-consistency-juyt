"""集中环境配置。所有端口/路径/密钥只从这里读取。"""
import os


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class Settings:
    PROJECT_NAME = "TexForge"
    SHORT_NAME = "texforge"
    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://texforge_user:texforge_pwd@db:3306/texforge_db?charset=utf8mb4",
    )
    REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    JWT_SECRET = os.environ.get("JWT_SECRET", "change_me_to_a_long_random_string")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_HOURS = _int("JWT_EXPIRE_HOURS", 8)
    ARTIFACT_DIR = os.environ.get("ARTIFACT_DIR", "/data/artifacts")
    PREVIEW_DIR = os.environ.get("PREVIEW_DIR", "/data/previews")
    SEED_DEMO = os.environ.get("SEED_DEMO", "true").lower() in ("1", "true", "yes", "on")
    GENERATION_DAILY_QUOTA = _int("GENERATION_DAILY_QUOTA", 60)
    MAX_UPLOAD_MB = _int("MAX_UPLOAD_MB", 16)
    SUPPORTED_RESOLUTIONS = (256, 512, 1024, 2048)
    DEMO_PASSWORD = "TexForge@2026"


settings = Settings()
