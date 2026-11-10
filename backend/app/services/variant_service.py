"""变体服务：生成请求（配额+锁+Celery）、真实渲染落盘、设当前版本、删除。"""
import hashlib
from datetime import datetime

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.constants.channel import CHANNEL_KEYS
from app.constants.error_codes import (
    ERROR_MESSAGES,
    GENERATION_TIMEOUT,
    PERMISSION_DENIED,
    QUOTA_EXHAUSTED,
    RATE_LIMITED,
    RECIPE_NOT_FOUND,
    VARIANT_DELETED,
)
from app.constants.recipe_status import RecipeStatus
from app.models.material_recipe import MaterialRecipe
from app.models.recipe_node import RecipeNode
from app.models.texture_variant import TextureVariant
from app.models.user import User
from app.services import audit_service
from app.texture.renderer import encode_channels, make_preview_png, render_recipe
from app.utils import storage
from app.utils.cache import acquire_generation_lock, release_generation_lock
from app.utils.errors import AppError
from app.utils.logger import log_event
from app.services.recipe_service import can_write, get_recipe, require_write


def list_variants(db: Session, recipe_id: int) -> list[TextureVariant]:
    return (
        db.query(TextureVariant)
        .filter(TextureVariant.recipe_id == recipe_id)
        .order_by(TextureVariant.revision.desc())
        .all()
    )


def get_variant(db: Session, variant_id: int) -> TextureVariant:
    variant = db.get(TextureVariant, variant_id)
    if not variant:
        raise AppError(VARIANT_DELETED, ERROR_MESSAGES[VARIANT_DELETED], http_status=404)
    return variant


def serialize_variant(variant: TextureVariant) -> dict:
    return {
        "id": variant.id,
        "recipe_id": variant.recipe_id,
        "revision": variant.revision,
        "seed_used": variant.seed_used,
        "file_paths_json": variant.file_paths_json or {},
        "preview_path": variant.preview_path,
        "generation_ms": variant.generation_ms,
        "seam_score": variant.seam_score,
        "status": variant.status,
        "checksum": variant.checksum,
        "is_current": variant.is_current,
        "created_at": variant.created_at,
    }


def request_generation(db: Session, user: dict, recipe_id: int, payload) -> TextureVariant:
    require_write(user)
    recipe = get_recipe(db, recipe_id)
    user_row = db.get(User, int(user["sub"]))
    if not user_row:
        raise AppError(PERMISSION_DENIED, "用户不存在", http_status=401)

    if payload.resolution is not None:
        if int(payload.resolution) not in settings.SUPPORTED_RESOLUTIONS:
            raise AppError("TEX-1004", ERROR_MESSAGES["TEX-1004"], http_status=422)
        recipe.resolution = int(payload.resolution)
    if payload.seed is not None:
        recipe.seed = int(payload.seed) % 2147483647

    today = datetime.utcnow().date()
    if user_row.quota_used_date != today:
        user_row.quota_used_date = today
        user_row.quota_used_count = 0
    if user_row.quota_used_count >= user_row.daily_generation_quota:
        log_event("QUOTA_REJECTED", user_id=user_row.id, route="/recipes/generate",
                  used=user_row.quota_used_count, quota=user_row.daily_generation_quota)
        raise AppError(QUOTA_EXHAUSTED, ERROR_MESSAGES[QUOTA_EXHAUSTED], http_status=429,
                       extra={"retry_after": 3600})

    if not acquire_generation_lock(recipe.id):
        log_event("LOCK_REJECTED", recipe_id=recipe.id, user_id=user_row.id)
        raise AppError(RATE_LIMITED, "该配方正在生成中，请等待本次完成", http_status=429,
                       extra={"retry_after": 20})

    try:
        revision = (db.query(TextureVariant)
                    .filter(TextureVariant.recipe_id == recipe.id)
                    .order_by(TextureVariant.revision.desc())
                    .first())
        next_revision = (revision.revision + 1) if revision else 1
        variant = TextureVariant(
            recipe_id=recipe.id,
            revision=next_revision,
            seed_used=recipe.seed,
            status="generating",
            file_paths_json={},
        )
        recipe.status = RecipeStatus.GENERATING.value
        user_row.quota_used_count += 1
        db.add(variant)
        db.add(recipe)
        db.add(user_row)
        db.commit()
        db.refresh(variant)
    except Exception:
        release_generation_lock(recipe.id)
        raise

    log_event("GENERATION_ENQUEUED", recipe_id=recipe.id, variant_id=variant.id,
              resolution=recipe.resolution, seed=variant.seed_used)
    try:
        from app.tasks.generate_texture import generate_texture_task

        generate_texture_task.delay(variant.id)
    except Exception as exc:  # noqa: BLE001 - broker 不可用时同步兜底
        log_event("GENERATION_FAILED", recipe_id=recipe.id, variant_id=variant.id, error=f"enqueue_failed:{exc}")
        perform_generation(db, variant.id)
    return variant


def perform_generation(db: Session, variant_id: int) -> TextureVariant:
    """真实渲染并写入共享卷（worker task / 同步兜底 / seed 共用同一实现）。"""
    variant = db.get(TextureVariant, variant_id)
    if not variant:
        raise AppError(VARIANT_DELETED, ERROR_MESSAGES[VARIANT_DELETED], http_status=404)
    if variant.status == "ready" and variant.file_paths_json:
        return variant
    recipe = db.get(MaterialRecipe, variant.recipe_id)
    if not recipe:
        raise AppError(RECIPE_NOT_FOUND, ERROR_MESSAGES[RECIPE_NOT_FOUND], http_status=404)
    nodes = (
        db.query(RecipeNode)
        .filter(RecipeNode.recipe_id == recipe.id)
        .order_by(RecipeNode.order_index)
        .all()
    )
    log_event("GENERATION_START", recipe_id=recipe.id, variant_id=variant.id, revision=variant.revision)
    try:
        result = render_recipe(nodes, recipe.resolution, variant.seed_used)
        images = encode_channels(result)
        rel_dir = f"{recipe.slug}/rev-{variant.revision}"
        file_paths: dict[str, str] = {}
        digest = hashlib.sha256()
        for key in CHANNEL_KEYS:
            rel_path = f"{rel_dir}/{key}.png"
            storage.write_bytes(rel_path, images[key])
            file_paths[key] = rel_path
            digest.update(images[key])
        preview_bytes = make_preview_png(
            result["base_color"], result["normal"], result["roughness"], result["metallic"], result["ao"], 512
        )
        preview_rel = f"{rel_dir}/preview.png"
        storage.write_bytes(preview_rel, preview_bytes, preview=True)

        variant.file_paths_json = file_paths
        variant.preview_path = preview_rel
        variant.generation_ms = int(result["generation_ms"])
        variant.seam_score = int(result["seam_score"])
        variant.checksum = digest.hexdigest()
        variant.status = "ready"
        recipe.status = RecipeStatus.READY.value
        recipe.thumbnail_path = preview_rel
        if not recipe.current_variant_id:
            recipe.current_variant_id = variant.id
            variant.is_current = 1
        elif recipe.current_variant_id == variant.id:
            variant.is_current = 1
        db.add(variant)
        db.add(recipe)
        db.commit()
        db.refresh(variant)
        log_event("GENERATION_DONE", recipe_id=recipe.id, variant_id=variant.id,
                  duration_ms=variant.generation_ms, seam_score=variant.seam_score)
        return variant
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        variant = db.get(TextureVariant, variant_id)
        if variant:
            variant.status = "failed"
            db.add(variant)
        recipe_row = db.get(MaterialRecipe, recipe.id)
        if recipe_row:
            recipe_row.status = RecipeStatus.FAILED.value
            db.add(recipe_row)
        db.commit()
        log_event("GENERATION_FAILED", recipe_id=recipe.id, variant_id=variant_id, error=str(exc))
        raise AppError(GENERATION_TIMEOUT, f"生成失败：{exc}", http_status=500) from exc
    finally:
        release_generation_lock(recipe.id)


def set_current(db: Session, user: dict, variant_id: int) -> TextureVariant:
    require_write(user)
    variant = get_variant(db, variant_id)
    if variant.status != "ready":
        raise AppError(GENERATION_TIMEOUT, "该版本尚未生成完成", http_status=409)
    db.query(TextureVariant).filter(TextureVariant.recipe_id == variant.recipe_id).update({"is_current": 0})
    variant.is_current = 1
    recipe = db.get(MaterialRecipe, variant.recipe_id)
    recipe.current_variant_id = variant.id
    db.add(variant)
    db.add(recipe)
    db.commit()
    db.refresh(variant)
    log_event("VARIANT_SET_CURRENT", variant_id=variant.id, recipe_id=variant.recipe_id, revision=variant.revision)
    return variant


def delete_variant(db: Session, user: dict, variant_id: int, ip: str | None = None) -> None:
    variant = get_variant(db, variant_id)
    if not can_write(user):
        raise AppError(PERMISSION_DENIED, ERROR_MESSAGES[PERMISSION_DENIED], http_status=403)
    recipe = db.get(MaterialRecipe, variant.recipe_id)
    slug = recipe.slug if recipe else "unknown"
    revision = variant.revision
    storage.remove_variant_dir(slug, revision)
    was_current = recipe is not None and recipe.current_variant_id == variant.id
    db.delete(variant)
    db.commit()
    if was_current and recipe:
        replacement = (
            db.query(TextureVariant)
            .filter(TextureVariant.recipe_id == recipe.id, TextureVariant.status == "ready")
            .order_by(TextureVariant.revision.desc())
            .first()
        )
        recipe.current_variant_id = replacement.id if replacement else None
        if replacement:
            replacement.is_current = 1
            recipe.thumbnail_path = replacement.preview_path
        db.add(recipe)
        db.commit()
    log_event("VARIANT_DELETE", variant_id=variant_id, recipe_id=recipe.id if recipe else None, revision=revision)
    audit_service.record_audit(db, int(user["sub"]), "variant_delete", "texture_variant", variant_id,
                               {"revision": revision}, ip)
