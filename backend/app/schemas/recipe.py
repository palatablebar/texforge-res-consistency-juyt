from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class RecipeOut(ORMModel):
    id: int
    owner_id: int
    name: str
    slug: str
    description: str = ""
    resolution: int
    seed: int
    status: str
    thumbnail_path: Optional[str] = None
    current_variant_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    node_count: int = 0
    variant_count: int = 0
    last_seam_score: Optional[int] = None
    owner_name: Optional[str] = None


class RecipeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = ""
    resolution: int = 512
    seed: Optional[int] = None
    palette: str = "terracotta"


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    resolution: Optional[int] = None
    seed: Optional[int] = None


class RecipeDuplicateRequest(BaseModel):
    name: Optional[str] = None


class RecipeDetailOut(RecipeOut):
    nodes: list[dict[str, Any]] = []
    recent_variants: list[dict[str, Any]] = []
