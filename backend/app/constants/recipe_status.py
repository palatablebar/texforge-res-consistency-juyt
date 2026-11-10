"""RecipeStatus：material_recipes.status 列与前端 StatusBadge 的唯一真源。"""
from enum import Enum


class RecipeStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


RECIPE_STATUS_LABELS = {
    RecipeStatus.DRAFT: "草稿",
    RecipeStatus.GENERATING: "生成中",
    RecipeStatus.READY: "就绪",
    RecipeStatus.FAILED: "失败",
}
