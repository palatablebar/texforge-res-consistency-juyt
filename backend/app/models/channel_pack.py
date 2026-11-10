from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String

from app.config.database import Base


class ChannelPack(Base):
    __tablename__ = "channel_packs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("material_recipes.id"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("texture_variants.id"), nullable=True)
    name = Column(String(160), nullable=False)
    channel_mapping_json = Column(JSON, nullable=False, default=dict)
    output_format = Column(String(10), nullable=False, default="png")
    preset = Column(String(20), nullable=False, default="custom")
    file_path = Column(String(512), nullable=True)
    byte_size = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
