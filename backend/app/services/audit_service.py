"""审计写入：失败不阻断主流程，仅记告警。"""
import json

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.utils.logger import log_event


def record_audit(db: Session, actor_id: int | None, action: str, entity_type: str, entity_id: int | None,
                 payload: dict | None = None, ip: str | None = None) -> None:
    try:
        db.add(
            AuditLog(
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                payload_json=json.loads(json.dumps(payload or {}, default=str)),
                ip=ip,
            )
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001 - 审计失败不能影响业务
        db.rollback()
        log_event("AUDIT_WRITE_FAILED", action=action, entity_type=entity_type, error=str(exc))
