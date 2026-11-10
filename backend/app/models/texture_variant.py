from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String

from app.config.database import Base
from app.texture.normal_map import GENERATION_ALGO_VERSION


class TextureVariant(Base):
    __tablename__ = "texture_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("material_recipes.id"), nullable=False, index=True)
    revision = Column(Integer, nullable=False, default=1)
    seed_used = Column(Integer, nullable=False, default=0)
    # 生成算法版本：历史变体固定为 1（按像素的梯度/AO 半径），新生成固定为 2（UV 空间补偿）。
    # 历史记录不重算不覆盖；对比页跨版本只做视觉对比，不把 checksum 当同一基准。
    algo_version = Column(Integer, nullable=False, default=GENERATION_ALGO_VERSION)
    file_paths_json = Column(JSON, nullable=False, default=dict)
    preview_path = Column(String(512), nullable=True)
    generation_ms = Column(Integer, nullable=False, default=0)
    seam_score = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="generating")
    checksum = Column(String(64), nullable=True)
    is_current = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
