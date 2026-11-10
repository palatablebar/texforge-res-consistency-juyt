"""BlendMode 后端唯一真源，被 texture/blend.py 的 BLEND_OPS 与 schemas/node.py 引用。"""
from enum import Enum


class BlendMode(str, Enum):
    NORMAL = "normal"
    ADD = "add"
    MULTIPLY = "multiply"
    OVERLAY = "overlay"
    SCREEN = "screen"


BLEND_LABELS = {
    BlendMode.NORMAL: "正常",
    BlendMode.ADD: "相加",
    BlendMode.MULTIPLY: "正片叠底",
    BlendMode.OVERLAY: "叠加",
    BlendMode.SCREEN: "滤色",
}
