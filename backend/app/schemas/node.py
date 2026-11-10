from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from app.constants.blend import BlendMode
from app.constants.noise import NoiseType
from app.schemas.common import ORMModel

InputRef = dict


class NodeOut(ORMModel):
    id: int
    recipe_id: int
    node_type: str
    label: str
    position_x: float
    position_y: float
    params_json: dict[str, Any] = {}
    input_refs_json: list[dict[str, Any]] = []
    order_index: int = 0
    is_disabled: bool = False


class NodeCreate(BaseModel):
    node_type: str
    label: str = ""
    position_x: float = 0
    position_y: float = 0
    params_json: dict[str, Any] = {}
    input_refs_json: list[dict[str, Any]] = []


class NodePatch(BaseModel):
    label: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    params_json: Optional[dict[str, Any]] = None
    input_refs_json: Optional[list[dict[str, Any]]] = None
    is_disabled: Optional[bool] = None


class NodeBatchItem(BaseModel):
    id: int
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    params_json: Optional[dict[str, Any]] = None
    input_refs_json: Optional[list[dict[str, Any]]] = None
    is_disabled: Optional[bool] = None


class NodeBatchUpdate(BaseModel):
    nodes: list[NodeBatchItem] = []


class NoiseParamsOut(BaseModel):
    noise_type: Literal["value", "perlin", "worley", "fbm"] = NoiseType.FBM.value
    blend_mode: Literal["normal", "add", "multiply", "overlay", "screen"] = BlendMode.MULTIPLY.value
    octaves: int = 5


class ConnectionRequest(BaseModel):
    from_node_id: int
    to_node_id: int
    slot: Literal["a", "b"] = "a"
