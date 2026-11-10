from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import auth_controller
from app.middlewares.auth import get_current_user
from app.schemas.auth import QuotaOut

router = APIRouter(prefix="/quota", tags=["quota"])


@router.get("/me", response_model=QuotaOut)
def my_quota(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return auth_controller.quota(db, user)
