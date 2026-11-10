"""响应阶段写审计日志：控制器显式记录过的请求不重复写，失败只告警。"""
import re

from fastapi import Request

from app.services import audit_service

ACTION_MAP = [
    (re.compile(r"^/recipes/[0-9]+/duplicate$"), "recipe_copy", "material_recipe"),
    (re.compile(r"^/recipes/[0-9]+$"), "recipe_delete", "material_recipe"),
    (re.compile(r"^/recipes$"), "recipe_create", "material_recipe"),
    (re.compile(r"^/recipes/[0-9]+/nodes$"), "node_batch_update", "recipe_node"),
    (re.compile(r"^/variants/[0-9]+$"), "variant_delete", "texture_variant"),
    (re.compile(r"^/packs/[0-9]+/download$"), "pack_download", "channel_pack"),
]


def audit_middleware(app):
    @app.middleware("http")
    async def audit_after_response(request: Request, call_next):
        response = await call_next(request)
        try:
            if request.method in ("GET", "OPTIONS", "HEAD") or response.status_code >= 400:
                return response
            if getattr(request.state, "audit_recorded", False):
                return response
            path = request.url.path
            for pattern, action, entity_type in ACTION_MAP:
                if pattern.match(path):
                    entity_id = None
                    match = re.search(r"/([0-9]+)(?:/|$)", path)
                    if match:
                        entity_id = int(match.group(1))
                    user = getattr(request.state, "user", None) or {}
                    from app.config.database import SessionLocal

                    db = SessionLocal()
                    try:
                        audit_service.record_audit(
                            db, int(user["sub"]) if user.get("sub") else None, action, entity_type, entity_id,
                            {"method": request.method, "path": path}, request.client.host if request.client else None,
                        )
                    finally:
                        db.close()
                    break
        except Exception:  # noqa: BLE001 - 审计不阻断主流程
            pass
        return response

    return app
