from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(ORMModel):
    id: int
    email: str
    display_name: str
    role: str
    workspace_role: str
    daily_generation_quota: int
    created_at: Optional[datetime] = None


class QuotaOut(BaseModel):
    daily_quota: int
    used_today: int
    remaining: int
    used_date: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
    quota: QuotaOut
