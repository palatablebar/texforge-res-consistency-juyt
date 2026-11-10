from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import pack_controller
from app.middlewares.auth import get_current_user, require_roles
from app.schemas.pack import PackCreate, PackOut, PackPrecheckOut, PackPrecheckRequest

router = APIRouter(prefix="/packs", tags=["packs"])


class PresetSaveRequest(BaseModel):
    name: str
    mapping: dict[str, str]


@router.get("/presets")
def presets(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    data = pack_controller.presets()
    data["saved"] = pack_controller.list_presets(user)
    return data


@router.post("/presets")
def save_preset(payload: PresetSaveRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return pack_controller.save_preset(user, payload)


@router.post("/precheck", response_model=PackPrecheckOut)
def precheck(payload: PackPrecheckRequest, db: Session = Depends(get_db),
             user: dict = Depends(get_current_user)):
    return pack_controller.precheck(db, payload)


@router.get("", response_model=list[PackOut])
def list_packs(recipe_id: int | None = None, db: Session = Depends(get_db),
               user: dict = Depends(get_current_user)):
    return pack_controller.list_packs(db, recipe_id)


@router.post("", response_model=PackOut, dependencies=[Depends(require_roles("owner", "editor"))])
def create_pack(payload: PackCreate, request: Request, db: Session = Depends(get_db),
                user: dict = Depends(get_current_user)):
    return pack_controller.create_pack(db, user, payload, request)


@router.get("/{pack_id}", response_model=PackOut)
def get_pack(pack_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return pack_controller.get_pack(db, pack_id)


@router.get("/{pack_id}/download")
def download(pack_id: int, request: Request, db: Session = Depends(get_db),
             user: dict = Depends(get_current_user)):
    abs_path, filename = pack_controller.download(db, user, pack_id, request)
    return FileResponse(abs_path, media_type="image/png", filename=filename)
