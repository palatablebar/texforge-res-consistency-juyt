from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import recipe_controller
from app.middlewares.auth import get_current_user, require_roles
from app.schemas.recipe import RecipeCreate, RecipeDetailOut, RecipeDuplicateRequest, RecipeOut, RecipeUpdate
from app.services import variant_service

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("", response_model=list[RecipeOut])
def list_recipes(status: str | None = None, resolution: int | None = None, q: str | None = None,
                 db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return recipe_controller.list_recipes(db, user, status, resolution, q)


@router.post("", response_model=RecipeOut, dependencies=[Depends(require_roles("owner", "editor"))])
def create_recipe(payload: RecipeCreate, request: Request, db: Session = Depends(get_db),
                  user: dict = Depends(get_current_user)):
    return recipe_controller.create_recipe(db, user, payload, request)


@router.get("/{recipe_id}", response_model=RecipeDetailOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return recipe_controller.get_recipe(db, recipe_id)


@router.patch("/{recipe_id}", response_model=RecipeOut, dependencies=[Depends(require_roles("owner", "editor"))])
def patch_recipe(recipe_id: int, payload: RecipeUpdate, db: Session = Depends(get_db),
                 user: dict = Depends(get_current_user)):
    return recipe_controller.patch_recipe(db, user, recipe_id, payload)


@router.post("/{recipe_id}/duplicate", response_model=RecipeOut,
             dependencies=[Depends(require_roles("owner", "editor"))])
def duplicate_recipe(recipe_id: int, request: Request, payload: RecipeDuplicateRequest | None = None,
                     db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return recipe_controller.duplicate_recipe(db, user, recipe_id, payload, request)


@router.delete("/{recipe_id}")
def delete_recipe(recipe_id: int, request: Request, db: Session = Depends(get_db),
                  user: dict = Depends(get_current_user)):
    return recipe_controller.delete_recipe(db, user, recipe_id, request)


@router.get("/{recipe_id}/variants")
def list_recipe_variants(recipe_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return [variant_service.serialize_variant(v) for v in variant_service.list_variants(db, recipe_id)]
