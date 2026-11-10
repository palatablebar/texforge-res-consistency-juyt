from datetime import datetime
from typing import Any, Optional

from app.schemas.common import ORMModel


class VariantOut(ORMModel):
    id: int
    recipe_id: int
    revision: int
    seed_used: int
    file_paths_json: dict[str, str] = {}
    preview_path: Optional[str] = None
    generation_ms: int = 0
    seam_score: int = 0
    status: str = "generating"
    checksum: Optional[str] = None
    algo_version: int = 1
    is_current: int = 0
    created_at: Optional[datetime] = None


class GenerateRequest(ORMModel):
    seed: Optional[int] = None
    resolution: Optional[int] = None


class GenerateOut(ORMModel):
    variant: VariantOut
    message: str = "生成任务已入队，请稍候"
