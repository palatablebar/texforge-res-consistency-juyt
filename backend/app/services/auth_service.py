"""认证与配额：JWT 登录、当前用户、当日配额快照。"""
from datetime import date

from sqlalchemy.orm import Session

from app.constants.error_codes import ERROR_MESSAGES, INVALID_CREDENTIALS
from app.constants.log_templates import LOG_TEMPLATES  # noqa: F401  (模板集中引用)
from app.models.user import User
from app.utils.errors import AppError
from app.utils.jwt import create_access_token
from app.utils.logger import log_event
from app.utils.password import verify_password


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email.lower().strip(), User.is_active.is_(True)).first()
    if not user or not verify_password(password, user.password_hash):
        log_event("AUTH_LOGIN_FAILED", email=email, reason="invalid_credentials")
        raise AppError(INVALID_CREDENTIALS, ERROR_MESSAGES[INVALID_CREDENTIALS], http_status=401)
    log_event("AUTH_LOGIN_SUCCESS", email=user.email, role=user.role, workspace_role=user.workspace_role)
    return user


def issue_token(user: User) -> dict:
    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "workspace_role": user.workspace_role,
            "display_name": user.display_name,
        }
    )
    return {"access_token": token, "token_type": "bearer", "expires_in": 8 * 3600, "user": user}


def quota_snapshot(user: User) -> dict:
    return user.quota_snapshot()


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise AppError("TEX-1014", "用户不存在", http_status=401)
    return user


def ensure_quota_row(db: Session, user: User) -> User:
    today = date.today()
    if user.quota_used_date != today:
        user.quota_used_date = today
        user.quota_used_count = 0
        db.add(user)
        db.commit()
    return user
