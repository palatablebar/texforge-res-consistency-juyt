from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String

from app.config.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(190), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(120), nullable=False)
    role = Column(String(20), nullable=False, default="member")  # admin / member
    workspace_role = Column(String(20), nullable=False, default="editor")  # owner / editor / viewer
    daily_generation_quota = Column(Integer, nullable=False, default=60)
    quota_used_date = Column(Date, nullable=True)
    quota_used_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def quota_snapshot(self) -> dict:
        today = date.today()
        used = self.quota_used_count if self.quota_used_date == today else 0
        return {
            "daily_quota": self.daily_generation_quota,
            "used_today": used,
            "remaining": max(0, self.daily_generation_quota - used),
            "used_date": (self.quota_used_date or today).isoformat(),
        }
