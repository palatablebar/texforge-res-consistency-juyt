"""认证控制器：包装 service 并把 User 序列化为 schema。"""
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import QuotaOut, TokenOut, UserOut
from app.services import auth_service


def login(db: Session, email: str, password: str) -> TokenOut:
    user = auth_service.authenticate(db, email, password)
    token = auth_service.issue_token(user)
    return TokenOut(
        access_token=token["access_token"],
        token_type="bearer",
        expires_in=token["expires_in"],
        user=UserOut.model_validate(user),
        quota=QuotaOut(**auth_service.quota_snapshot(user)),
    )


def me(db: Session, user: dict) -> UserOut:
    row = auth_service.get_user(db, int(user["sub"]))
    return UserOut.model_validate(row)


def quota(db: Session, user: dict) -> QuotaOut:
    row = auth_service.get_user(db, int(user["sub"]))
    return QuotaOut(**auth_service.quota_snapshot(row))
