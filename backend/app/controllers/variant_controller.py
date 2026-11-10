"""变体控制器。"""
from fastapi import Request
from sqlalchemy.orm import Session

from app.services import variant_service


def list_variants(db: Session, recipe_id: int) -> list[dict]:
    return [variant_service.serialize_variant(v) for v in variant_service.list_variants(db, recipe_id)]


def get_variant(db: Session, variant_id: int) -> dict:
    return variant_service.serialize_variant(variant_service.get_variant(db, variant_id))


def generate(db: Session, user: dict, recipe_id: int, payload) -> dict:
    variant = variant_service.request_generation(db, user, recipe_id, payload)
    return {"variant": variant_service.serialize_variant(variant), "message": "生成任务已入队，请稍候"}


def set_current(db: Session, user: dict, variant_id: int) -> dict:
    variant = variant_service.set_current(db, user, variant_id)
    return {"variant": variant_service.serialize_variant(variant), "message": "已设为当前版本"}


def delete_variant(db: Session, user: dict, variant_id: int, request: Request) -> dict:
    variant_service.delete_variant(db, user, variant_id, request.client.host if request.client else None)
    request.state.audit_recorded = True
    return {"message": "变体已删除，共享卷文件已清理"}
