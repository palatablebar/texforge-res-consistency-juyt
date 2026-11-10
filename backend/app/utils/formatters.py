"""多职责格式化：分辨率文案、毫秒、字节、seam 分档、通道中文名、状态中文名。
被 controller 响应序列化、审计 payload、任务日志三处调用。"""
from app.constants.channel import CHANNEL_LABELS, TextureChannel
from app.constants.recipe_status import RECIPE_STATUS_LABELS, RecipeStatus


def format_resolution(resolution: int) -> str:
    return f"{resolution} × {resolution}"


def format_ms(value: int | None) -> str:
    if value is None:
        return "—"
    if value < 1000:
        return f"{int(value)} ms"
    return f"{value / 1000:.2f} s"


def format_bytes(size: int | None) -> str:
    if not size:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def seam_grade(score: int) -> str:
    if score >= 88:
        return "优"
    if score >= 75:
        return "良"
    if score >= 60:
        return "可接受"
    return "需修补"


def channel_label(channel: str) -> str:
    try:
        return CHANNEL_LABELS[TextureChannel(channel)]
    except ValueError:
        return channel


def status_label(status: str) -> str:
    try:
        return RECIPE_STATUS_LABELS[RecipeStatus(status)]
    except ValueError:
        return status


def format_variant_summary(variant) -> dict:
    return {
        "resolution": format_resolution(variant.recipe.resolution) if getattr(variant, "recipe", None) else None,
        "generation": format_ms(variant.generation_ms),
        "seam": f"{variant.seam_score} · {seam_grade(variant.seam_score)}",
    }
