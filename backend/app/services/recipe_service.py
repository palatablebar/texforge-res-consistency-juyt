"""配方服务：工作区角色判定、增删改查、复制、序列化。"""
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.constants.error_codes import ERROR_MESSAGES, PERMISSION_DENIED, RECIPE_NOT_FOUND, RESOLUTION_UNSUPPORTED
from app.constants.recipe_status import RecipeStatus
from app.models.material_recipe import MaterialRecipe
from app.models.recipe_node import RecipeNode
from app.models.texture_variant import TextureVariant
from app.models.user import User
from app.config.settings import settings
from app.utils.errors import AppError
from app.utils.logger import log_event

WRITE_ROLES = {"owner", "editor"}


def can_write(user: dict) -> bool:
    return str(user.get("workspace_role", "viewer")) in WRITE_ROLES or str(user.get("role")) == "admin"


def can_delete(user: dict, recipe: MaterialRecipe) -> bool:
    if str(user.get("role")) == "admin":
        return True
    return str(user.get("workspace_role")) == "owner" and int(user.get("sub", 0)) == recipe.owner_id


def require_write(user: dict) -> None:
    if not can_write(user):
        raise AppError(PERMISSION_DENIED, ERROR_MESSAGES[PERMISSION_DENIED], http_status=403)


def require_owner(user: dict, recipe: MaterialRecipe) -> None:
    if not can_delete(user, recipe):
        raise AppError(PERMISSION_DENIED, "只有工作区 owner 可以删除配方", http_status=403)


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return base or f"recipe-{int(datetime.utcnow().timestamp())}"


def unique_slug(db: Session, name: str) -> str:
    slug = _slugify(name)
    candidate = slug
    index = 2
    while db.query(MaterialRecipe).filter(MaterialRecipe.slug == candidate).first():
        candidate = f"{slug}-{index}"
        index += 1
    return candidate


def get_recipe(db: Session, recipe_id: int, include_deleted: bool = False) -> MaterialRecipe:
    recipe = db.get(MaterialRecipe, recipe_id)
    if not recipe or (recipe.is_deleted and not include_deleted):
        raise AppError(RECIPE_NOT_FOUND, ERROR_MESSAGES[RECIPE_NOT_FOUND], http_status=404)
    return recipe


def list_recipes(db: Session, user: dict, status: str | None = None, resolution: int | None = None,
                 q: str | None = None) -> list[MaterialRecipe]:
    query = db.query(MaterialRecipe).filter(MaterialRecipe.is_deleted.is_(False))
    if status:
        query = query.filter(MaterialRecipe.status == status)
    if resolution:
        query = query.filter(MaterialRecipe.resolution == int(resolution))
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(MaterialRecipe.name.like(like))
    return query.order_by(MaterialRecipe.id.asc()).all()


def serialize_recipe(db: Session, recipe: MaterialRecipe) -> dict:
    node_count = db.query(RecipeNode).filter(RecipeNode.recipe_id == recipe.id).count()
    variants = (
        db.query(TextureVariant)
        .filter(TextureVariant.recipe_id == recipe.id, TextureVariant.status == "ready")
        .order_by(TextureVariant.revision.desc())
        .all()
    )
    owner = db.get(User, recipe.owner_id)
    current = next((v for v in variants if v.id == recipe.current_variant_id), variants[0] if variants else None)
    return {
        "id": recipe.id,
        "owner_id": recipe.owner_id,
        "name": recipe.name,
        "slug": recipe.slug,
        "description": recipe.description or "",
        "resolution": recipe.resolution,
        "seed": recipe.seed,
        "status": recipe.status,
        "thumbnail_path": recipe.thumbnail_path,
        "current_variant_id": recipe.current_variant_id or (current.id if current else None),
        "created_at": recipe.created_at,
        "updated_at": recipe.updated_at,
        "node_count": node_count,
        "variant_count": len(variants),
        "last_seam_score": current.seam_score if current else None,
        "owner_name": owner.display_name if owner else None,
    }


def serialize_recipe_detail(db: Session, recipe: MaterialRecipe) -> dict:
    data = serialize_recipe(db, recipe)
    nodes = db.query(RecipeNode).filter(RecipeNode.recipe_id == recipe.id).order_by(RecipeNode.order_index).all()
    variants = (
        db.query(TextureVariant)
        .filter(TextureVariant.recipe_id == recipe.id)
        .order_by(TextureVariant.revision.desc())
        .all()
    )
    data["nodes"] = [
        {
            "id": n.id,
            "recipe_id": n.recipe_id,
            "node_type": n.node_type,
            "label": n.label,
            "position_x": n.position_x,
            "position_y": n.position_y,
            "params_json": n.params_json or {},
            "input_refs_json": n.input_refs_json or [],
            "order_index": n.order_index,
            "is_disabled": n.is_disabled,
        }
        for n in nodes
    ]
    data["recent_variants"] = [
        {
            "id": v.id,
            "revision": v.revision,
            "seed_used": v.seed_used,
            "seam_score": v.seam_score,
            "generation_ms": v.generation_ms,
            "status": v.status,
            "preview_path": v.preview_path,
            "is_current": v.is_current,
        }
        for v in variants[:6]
    ]
    return data


def _validate_resolution(resolution: int) -> int:
    if int(resolution) not in settings.SUPPORTED_RESOLUTIONS:
        raise AppError(RESOLUTION_UNSUPPORTED, ERROR_MESSAGES[RESOLUTION_UNSUPPORTED], http_status=422)
    return int(resolution)


def _default_node_seed() -> int:
    return int(datetime.utcnow().timestamp()) % 2147483647


def create_recipe(db: Session, user: dict, payload) -> MaterialRecipe:
    require_write(user)
    resolution = _validate_resolution(payload.resolution)
    seed = payload.seed if payload.seed is not None else _default_node_seed()
    recipe = MaterialRecipe(
        owner_id=int(user["sub"]),
        name=payload.name.strip(),
        slug=unique_slug(db, payload.name),
        description=payload.description or "",
        resolution=resolution,
        seed=int(seed) % 2147483647,
        status=RecipeStatus.DRAFT.value,
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    log_event("RECIPE_CREATE", recipe_id=recipe.id, owner_id=recipe.owner_id,
              resolution=recipe.resolution, seed=recipe.seed)
    return recipe


def update_recipe(db: Session, user: dict, recipe_id: int, payload) -> MaterialRecipe:
    require_write(user)
    recipe = get_recipe(db, recipe_id)
    changed = []
    data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else {}
    if "resolution" in data and data["resolution"] is not None:
        recipe.resolution = _validate_resolution(data["resolution"])
        changed.append("resolution")
    if "seed" in data and data["seed"] is not None:
        recipe.seed = int(data["seed"]) % 2147483647
        changed.append("seed")
    if data.get("name"):
        recipe.name = data["name"].strip()
        changed.append("name")
    if data.get("description") is not None:
        recipe.description = data["description"]
        changed.append("description")
    db.commit()
    db.refresh(recipe)
    log_event("RECIPE_UPDATE", recipe_id=recipe.id, fields=",".join(changed) or "none")
    return recipe


def duplicate_recipe(db: Session, user: dict, recipe_id: int, new_name: str | None = None) -> MaterialRecipe:
    require_write(user)
    source = get_recipe(db, recipe_id)
    name = (new_name or f"{source.name} 副本").strip()
    copy = MaterialRecipe(
        owner_id=int(user["sub"]),
        name=name,
        slug=unique_slug(db, name),
        description=source.description or "",
        resolution=source.resolution,
        seed=(source.seed + 7919) % 2147483647,
        status=RecipeStatus.DRAFT.value,
    )
    db.add(copy)
    db.flush()
    nodes = db.query(RecipeNode).filter(RecipeNode.recipe_id == source.id).order_by(RecipeNode.order_index).all()
    id_map: dict[int, int] = {}
    for node in nodes:
        clone = RecipeNode(
            recipe_id=copy.id,
            node_type=node.node_type,
            label=node.label,
            position_x=node.position_x,
            position_y=node.position_y,
            params_json=node.params_json or {},
            input_refs_json=[],
            order_index=node.order_index,
            is_disabled=node.is_disabled,
        )
        db.add(clone)
        db.flush()
        id_map[node.id] = clone.id
    for node in nodes:
        clone_id = id_map[node.id]
        clone = db.get(RecipeNode, clone_id)
        clone.input_refs_json = [
            {"slot": ref.get("slot", "a"), "from_node_id": id_map.get(ref.get("from_node_id"), ref.get("from_node_id"))}
            for ref in (node.input_refs_json or [])
            if isinstance(ref, dict)
        ]
        db.add(clone)
    db.commit()
    db.refresh(copy)
    log_event("RECIPE_COPY", recipe_id=source.id, new_recipe_id=copy.id, node_count=len(nodes))
    return copy


def soft_delete(db: Session, user: dict, recipe_id: int) -> None:
    recipe = get_recipe(db, recipe_id)
    require_owner(user, recipe)
    recipe.is_deleted = True
    recipe.status = RecipeStatus.DRAFT.value
    db.add(recipe)
    db.commit()
    log_event("RECIPE_DELETE", recipe_id=recipe.id, actor_id=user.get("sub"))
