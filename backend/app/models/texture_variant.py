from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String

from app.config.database import Base


class TextureVariant(Base):
    __tablename__ = "texture_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("material_recipes.id"), nullable=False, index=True)
    revision = Column(Integer, nullable=False, default=1)
    seed_used = Column(Integer, nullable=False, default=0)
    file_paths_json = Column(JSON, nullable=False, default=dict)
    preview_path = Column(String(512), nullable=True)
    generation_ms = Column(Integer, nullable=False, default=0)
    seam_score = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="generating")
    checksum = Column(String(64), nullable=True)
    is_current = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
