from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.config.database import Base


class MaterialRecipe(Base):
    __tablename__ = "material_recipes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    slug = Column(String(160), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False, default="")
    resolution = Column(Integer, nullable=False, default=512)
    seed = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="draft")
    thumbnail_path = Column(String(512), nullable=True)
    current_variant_id = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
