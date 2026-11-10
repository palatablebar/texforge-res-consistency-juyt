"""配方控制器：调用 service 补实体上下文，并显式记录审计。"""
from fastapi import Request
from sqlalchemy.orm import Session

from app.services import audit_service, recipe_service


def list_recipes(db: Session, user: dict, status: str | None, resolution: int | None, q: str | None) -> list[dict]:
    recipes = recipe_service.list_recipes(db, user, status, resolution, q)
    return [recipe_service.serialize_recipe(db, recipe) for recipe in recipes]


def get_recipe(db: Session, recipe_id: int) -> dict:
    recipe = recipe_service.get_recipe(db, recipe_id)
    return recipe_service.serialize_recipe_detail(db, recipe)


def create_recipe(db: Session, user: dict, payload, request: Request) -> dict:
    recipe = recipe_service.create_recipe(db, user, payload)
    audit_service.record_audit(db, int(user["sub"]), "recipe_create", "material_recipe", recipe.id,
                               {"name": recipe.name, "resolution": recipe.resolution, "seed": recipe.seed},
                               request.client.host if request.client else None)
    request.state.audit_recorded = True
    return recipe_service.serialize_recipe(db, recipe)


def patch_recipe(db: Session, user: dict, recipe_id: int, payload) -> dict:
    recipe = recipe_service.update_recipe(db, user, recipe_id, payload)
    return recipe_service.serialize_recipe(db, recipe)


def duplicate_recipe(db: Session, user: dict, recipe_id: int, payload, request: Request) -> dict:
    copy = recipe_service.duplicate_recipe(db, user, recipe_id, payload.name if payload else None)
    audit_service.record_audit(db, int(user["sub"]), "recipe_copy", "material_recipe", copy.id,
                               {"source_recipe_id": recipe_id, "name": copy.name},
                               request.client.host if request.client else None)
    request.state.audit_recorded = True
    return recipe_service.serialize_recipe(db, copy)


def delete_recipe(db: Session, user: dict, recipe_id: int, request: Request) -> dict:
    recipe_service.soft_delete(db, user, recipe_id)
    audit_service.record_audit(db, int(user["sub"]), "recipe_delete", "material_recipe", recipe_id,
                               {"name": "soft-deleted"}, request.client.host if request.client else None)
    request.state.audit_recorded = True
    return {"message": "配方已删除，操作已记录"}
