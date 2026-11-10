"""通道打包服务：预检（重复/缺失）、异步打包、下载、预设。"""
import json

import numpy as np
from PIL import Image
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.constants.channel import CHANNEL_KEYS, TextureChannel
from app.constants.error_codes import (
    CHANNEL_DUPLICATE,
    CHANNEL_MISSING,
    ERROR_MESSAGES,
    PACK_FORMAT_UNSUPPORTED,
    RECIPE_NOT_FOUND,
    VARIANT_DELETED,
)
from app.models.channel_pack import ChannelPack
from app.models.material_recipe import MaterialRecipe
from app.models.texture_variant import TextureVariant
from app.services import audit_service
from app.services.recipe_service import can_write, get_recipe, require_write
from app.texture.packer import pack_channels
from app.utils import storage
from app.utils.cache import get_redis
from app.utils.errors import AppError
from app.utils.logger import log_event

PRESETS: dict[str, dict[str, str]] = {
    "orm": {"r": "roughness", "g": "metallic", "b": "ao", "a": "height"},
    "mra": {"r": "metallic", "g": "roughness", "b": "ao", "a": "height"},
    "custom": {},
}


def resolve_variant(db: Session, recipe: MaterialRecipe, variant_id: int | None) -> TextureVariant:
    if variant_id:
        variant = db.get(TextureVariant, variant_id)
    elif recipe.current_variant_id:
        variant = db.get(TextureVariant, recipe.current_variant_id)
    else:
        variant = None
    if not variant:
        variant = (
            db.query(TextureVariant)
            .filter(TextureVariant.recipe_id == recipe.id, TextureVariant.status == "ready")
            .order_by(TextureVariant.revision.desc())
            .first()
        )
    if not variant:
        raise AppError(VARIANT_DELETED, "该配方还没有可用变体，请先生成", http_status=409)
    return variant


def precheck(db: Session, recipe_id: int, variant_id: int | None, mapping: dict[str, str]) -> dict:
    recipe = get_recipe(db, recipe_id)
    variant = resolve_variant(db, recipe, variant_id)
    available = set((variant.file_paths_json or {}).keys())
    values = list(mapping.values())
    duplicate = sorted({value for value in values if values.count(value) > 1})
    missing = sorted({value for value in values if value not in available}) if available else []
    return {
        "ok": not duplicate and not missing,
        "missing_channels": missing,
        "duplicate_channels": duplicate,
        "size_ok": bool(available) and set(available) >= set(CHANNEL_KEYS),
        "resolution": recipe.resolution,
        "variant_id": variant.id,
        "message": ("映射可用" if not duplicate and not missing else "映射存在问题"),
    }


def pack_base_name(recipe: MaterialRecipe) -> str:
    slug = recipe.slug
    for prefix in ("prj-2611-", "prj-", "demo-"):
        if slug.startswith(prefix):
            slug = slug[len(prefix):]
    slug = slug.replace("-", "_")
    if slug == "terracotta":
        slug = "terracotta_wall"
    return slug


def pack_filename(recipe: MaterialRecipe, preset: str, output_format: str) -> str:
    return f"{pack_base_name(recipe)}_{preset}_{recipe.resolution}.{output_format}"


def create_pack(db: Session, user: dict, payload, ip: str | None = None) -> ChannelPack:
    require_write(user)
    if payload.output_format not in ("png", "tga"):
        raise AppError(PACK_FORMAT_UNSUPPORTED, ERROR_MESSAGES[PACK_FORMAT_UNSUPPORTED], http_status=422)
    recipe = get_recipe(db, payload.recipe_id)
    variant = resolve_variant(db, recipe, payload.variant_id)
    raw_mapping = payload.channel_mapping or {}
    if not set(raw_mapping.keys()) <= {"r", "g", "b", "a"}:
        raise AppError(CHANNEL_MISSING, "通道槽位只能是 r/g/b/a", http_status=422)
    unknown = [value for value in raw_mapping.values() if value not in CHANNEL_KEYS]
    if unknown:
        raise AppError(CHANNEL_MISSING, f"未知纹理通道 {unknown}", http_status=422)
    mapping = {slot: channel for slot, channel in raw_mapping.items() if slot in ("r", "g", "b", "a")}
    check = precheck(db, recipe.id, variant.id, mapping)
    if check["duplicate_channels"]:
        log_event("PACK_PRECHECK_FAILED", recipe_id=recipe.id, reason="duplicate", preset=payload.preset)
        raise AppError(CHANNEL_DUPLICATE, ERROR_MESSAGES[CHANNEL_DUPLICATE], http_status=422,
                       extra={"duplicate_channels": check["duplicate_channels"]})
    if check["missing_channels"]:
        log_event("PACK_PRECHECK_FAILED", recipe_id=recipe.id, reason="missing", preset=payload.preset)
        raise AppError(CHANNEL_MISSING, ERROR_MESSAGES[CHANNEL_MISSING], http_status=422,
                       extra={"missing_channels": check["missing_channels"]})
    name = payload.name.strip() or pack_filename(recipe, payload.preset, payload.output_format).rsplit(".", 1)[0]
    filename = pack_filename(recipe, payload.preset, payload.output_format)
    pack = ChannelPack(
        recipe_id=recipe.id,
        variant_id=variant.id,
        name=name,
        channel_mapping_json=mapping,
        output_format=payload.output_format,
        preset=payload.preset,
        file_path=f"packs/{filename}",
        status="pending",
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)
    log_event("PACK_CREATE", pack_id=pack.id, recipe_id=recipe.id, preset=payload.preset, mapping=json.dumps(mapping))
    try:
        from app.tasks.pack_channels import pack_channels_task

        pack_channels_task.delay(pack.id)
    except Exception:  # noqa: BLE001 - broker 不可用时同步兜底
        perform_pack(db, pack.id)
    return pack


def _load_channel_arrays(variant: TextureVariant) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for key, rel_path in (variant.file_paths_json or {}).items():
        with Image.open(storage.artifact_abs(rel_path)) as img:
            arr = np.asarray(img.convert("RGB") if key in ("base_color", "normal") else img.convert("L"),
                             dtype=np.float32)
        arrays[key] = arr / 255.0
    return arrays


def perform_pack(db: Session, pack_id: int) -> ChannelPack:
    pack = db.get(ChannelPack, pack_id)
    if not pack:
        raise AppError("TEX-1011", "通道包不存在", http_status=404)
    if pack.status == "ready" and pack.file_path:
        return pack
    variant = db.get(TextureVariant, pack.variant_id)
    if not variant or variant.status != "ready":
        raise AppError(VARIANT_DELETED, ERROR_MESSAGES[VARIANT_DELETED], http_status=409)
    started = __import__("time").perf_counter()
    try:
        arrays = _load_channel_arrays(variant)
        data = pack_channels(arrays, pack.channel_mapping_json or {}, pack.output_format or "png")
        rel_path = pack.file_path or f"packs/pack-{pack.id}.png"
        storage.write_bytes(rel_path, data)
        pack.file_path = rel_path
        pack.byte_size = len(data)
        pack.status = "ready"
        db.add(pack)
        db.commit()
        db.refresh(pack)
        duration_ms = int((__import__("time").perf_counter() - started) * 1000)
        log_event("PACK_DONE", pack_id=pack.id, byte_size=pack.byte_size, duration_ms=duration_ms)
        return pack
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        pack = db.get(ChannelPack, pack_id)
        if pack:
            pack.status = "failed"
            db.add(pack)
            db.commit()
        log_event("GENERATION_FAILED", recipe_id=pack.recipe_id if pack else None, variant_id=pack.variant_id if pack else None,
                  error=f"pack:{exc}")
        raise


def list_packs(db: Session, recipe_id: int | None = None) -> list[ChannelPack]:
    query = db.query(ChannelPack)
    if recipe_id:
        query = query.filter(ChannelPack.recipe_id == recipe_id)
    return query.order_by(ChannelPack.created_at.desc()).all()


def serialize_pack(pack: ChannelPack) -> dict:
    return {
        "id": pack.id,
        "recipe_id": pack.recipe_id,
        "variant_id": pack.variant_id,
        "name": pack.name,
        "channel_mapping_json": pack.channel_mapping_json or {},
        "output_format": pack.output_format,
        "preset": pack.preset,
        "file_path": pack.file_path,
        "byte_size": pack.byte_size,
        "status": pack.status,
        "created_at": pack.created_at,
    }


def download_pack(db: Session, user: dict, pack_id: int, ip: str | None = None) -> tuple[str, str]:
    pack = db.get(ChannelPack, pack_id)
    if not pack or not pack.file_path:
        raise AppError("TEX-1011", "通道包文件不存在", http_status=404)
    abs_path = storage.artifact_abs(pack.file_path)
    log_event("PACK_DOWNLOAD", pack_id=pack.id, actor_id=user.get("sub"), file=pack.file_path)
    audit_service.record_audit(db, int(user["sub"]), "pack_download", "channel_pack", pack.id,
                               {"file": pack.file_path, "preset": pack.preset}, ip)
    return abs_path, pack.file_path.split("/")[-1]


def save_preset(user: dict, name: str, mapping: dict[str, str]) -> dict:
    key = f"rp:texforge:preset:{int(user['sub'])}:{name}"
    get_redis().set(key, json.dumps(mapping))
    return {"name": name, "mapping": mapping, "saved": True}


def list_presets(user: dict) -> list[dict]:
    client = get_redis()
    result = []
    for key in client.scan_iter(match=f"rp:texforge:preset:{int(user['sub'])}:*"):
        try:
            result.append({"name": key.split(":")[-1], "mapping": json.loads(client.get(key) or "{}")})
        except (ValueError, TypeError):
            continue
    return result
