"""最近审计记录：供前端 <ActivityTrail> 展开显示。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.middlewares.auth import get_current_user
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/recent")
def recent_audit(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db),
                 user: dict = Depends(get_current_user)):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    actor_ids = {row.actor_id for row in rows if row.actor_id}
    actors = {u.id: u.display_name for u in db.query(User).filter(User.id.in_(actor_ids)).all()} if actor_ids else {}
    return [
        {
            "id": row.id,
            "actor_id": row.actor_id,
            "actor_name": actors.get(row.actor_id) if row.actor_id else None,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "payload_json": row.payload_json or {},
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]
