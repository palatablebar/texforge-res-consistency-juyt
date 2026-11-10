from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import auth_controller
from app.middlewares.auth import get_current_user
from app.schemas.auth import LoginRequest, QuotaOut, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return auth_controller.login(db, payload.email, payload.password)


@router.get("/me", response_model=UserOut)
def me(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return auth_controller.me(db, user)


@router.get("/quota", response_model=QuotaOut)
def quota(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return auth_controller.quota(db, user)
