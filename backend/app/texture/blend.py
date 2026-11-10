"""BlendMode 分派表：schemas/node.py 与 texture/renderer.py 共用。"""
import numpy as np

from app.constants.blend import BlendMode


def blend_normal(a, b):
    return b


def blend_add(a, b):
    return np.clip(a + b, 0.0, 1.0)


def blend_multiply(a, b):
    return a * b


def blend_overlay(a, b):
    return np.where(a < 0.5, 2 * a * b, 1 - 2 * (1 - a) * (1 - b))


def blend_screen(a, b):
    return 1 - (1 - a) * (1 - b)


BLEND_OPS = {
    BlendMode.NORMAL.value: blend_normal,
    BlendMode.ADD.value: blend_add,
    BlendMode.MULTIPLY.value: blend_multiply,
    BlendMode.OVERLAY.value: blend_overlay,
    BlendMode.SCREEN.value: blend_screen,
}


def apply_blend(a: np.ndarray, b: np.ndarray, mode: str, opacity: float = 1.0) -> np.ndarray:
    op = BLEND_OPS.get(mode, blend_multiply)
    mixed = op(a, b)
    opacity = float(np.clip(opacity, 0.0, 1.0))
    return np.clip(a * (1 - opacity) + mixed * opacity, 0.0, 1.0).astype(np.float32)
