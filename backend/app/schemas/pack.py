from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel

from app.constants.channel import TextureChannel
from app.schemas.common import ORMModel

ChannelLiteral = Literal["base_color", "normal", "roughness", "metallic", "ao", "height"]


class PackOut(ORMModel):
    id: int
    recipe_id: int
    variant_id: Optional[int] = None
    name: str
    channel_mapping_json: dict[str, str] = {}
    output_format: str = "png"
    preset: str = "custom"
    file_path: Optional[str] = None
    byte_size: int = 0
    status: str = "pending"
    created_at: Optional[datetime] = None


class PackCreate(BaseModel):
    recipe_id: int
    variant_id: Optional[int] = None
    name: str = ""
    channel_mapping: dict[str, str]
    output_format: Literal["png", "tga"] = "png"
    preset: Literal["orm", "mra", "custom"] = "custom"


class PackPrecheckRequest(BaseModel):
    recipe_id: int
    variant_id: Optional[int] = None
    channel_mapping: dict[str, str]


class PackPrecheckOut(BaseModel):
    ok: bool
    missing_channels: list[str] = []
    duplicate_channels: list[str] = []
    size_ok: bool = True
    resolution: int = 0
    message: str = ""
