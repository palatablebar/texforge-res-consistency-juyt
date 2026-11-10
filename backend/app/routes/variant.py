from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import variant_controller
from app.middlewares.auth import get_current_user, require_roles
from app.schemas.variant import GenerateRequest, VariantOut

router = APIRouter(tags=["variants"])


@router.post("/recipes/{recipe_id}/generate", response_model=dict,
             dependencies=[Depends(require_roles("owner", "editor"))])
def generate(recipe_id: int, payload: GenerateRequest | None = None, db: Session = Depends(get_db),
             user: dict = Depends(get_current_user)):
    return variant_controller.generate(db, user, recipe_id, payload or GenerateRequest())


@router.get("/variants/{variant_id}", response_model=VariantOut)
def get_variant(variant_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return variant_controller.get_variant(db, variant_id)


@router.post("/variants/{variant_id}/current", response_model=dict,
             dependencies=[Depends(require_roles("owner", "editor"))])
def set_current(variant_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return variant_controller.set_current(db, user, variant_id)


@router.delete("/variants/{variant_id}", dependencies=[Depends(require_roles("owner", "editor"))])
def delete_variant(variant_id: int, request: Request, db: Session = Depends(get_db),
                   user: dict = Depends(get_current_user)):
    return variant_controller.delete_variant(db, user, variant_id, request)
