"""通道打包控制器。"""
from fastapi import Request
from sqlalchemy.orm import Session

from app.services import pack_service


def presets() -> dict:
    return {"presets": pack_service.PRESETS}


def precheck(db: Session, payload) -> dict:
    return pack_service.precheck(db, payload.recipe_id, payload.variant_id, payload.channel_mapping)


def create_pack(db: Session, user: dict, payload, request: Request) -> dict:
    pack = pack_service.create_pack(db, user, payload, request.client.host if request.client else None)
    request.state.audit_recorded = True
    return pack_service.serialize_pack(pack)


def list_packs(db: Session, recipe_id: int | None) -> list[dict]:
    return [pack_service.serialize_pack(p) for p in pack_service.list_packs(db, recipe_id)]


def get_pack(db: Session, pack_id: int) -> dict:
    from app.models.channel_pack import ChannelPack

    pack = db.get(ChannelPack, pack_id)
    return pack_service.serialize_pack(pack)


def download(db: Session, user: dict, pack_id: int, request: Request):
    abs_path, filename = pack_service.download_pack(db, user, pack_id, request.client.host if request.client else None)
    request.state.audit_recorded = True
    return abs_path, filename


def save_preset(user: dict, payload) -> dict:
    return pack_service.save_preset(user, payload.name, payload.mapping)


def list_presets(user: dict) -> list[dict]:
    return pack_service.list_presets(user)
