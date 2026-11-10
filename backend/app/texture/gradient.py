"""渐变场与调色：由高度/噪声场生成 base_color。"""
import numpy as np


def gradient_field(res: int, angle: float = 0.0, softness: float = 0.35) -> np.ndarray:
    axis = np.linspace(0.0, 1.0, res, dtype=np.float32)
    gx, gy = np.meshgrid(axis, axis)
    rad = np.deg2rad(float(angle))
    field = gx * np.cos(rad) + gy * np.sin(rad)
    field = (field - field.min()) / max(field.max() - field.min(), 1e-6)
    soft = np.clip(float(softness), 0.02, 1.0)
    return np.clip((field - 0.5) / (soft * 0.5) * 0.5 + 0.5, 0.0, 1.0).astype(np.float32)


def colorize(field: np.ndarray, color_from, color_to, tint: np.ndarray | None = None) -> np.ndarray:
    """把 0~1 场映射到两色之间，返回 HxWx3 uint8。"""
    t = np.clip(field, 0.0, 1.0).astype(np.float32)
    if tint is not None:
        t = np.clip(t * 0.86 + tint * 0.14, 0.0, 1.0)
    frm = np.array(color_from, dtype=np.float32)
    to = np.array(color_to, dtype=np.float32)
    rgb = frm[None, None, :] * (1 - t[..., None]) + to[None, None, :] * t[..., None]
    return np.clip(rgb, 0, 255).astype(np.uint8)
