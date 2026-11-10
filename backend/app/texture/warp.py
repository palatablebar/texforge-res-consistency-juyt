"""域扭曲：用两层噪声偏移采样坐标，再做双线性重采样。"""
import numpy as np

from app.texture.noise import value_noise


def _bilinear_wrap(field: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    res = field.shape[0]
    x = np.mod(xs, 1.0) * (res - 1)
    y = np.mod(ys, 1.0) * (res - 1)
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = (x0 + 1) % res
    y1 = (y0 + 1) % res
    fx = (x - x0).astype(np.float32)
    fy = (y - y0).astype(np.float32)
    v00 = field[y0, x0]
    v10 = field[y0, x1]
    v01 = field[y1, x0]
    v11 = field[y1, x1]
    top = v00 * (1 - fx) + v10 * fx
    bot = v01 * (1 - fx) + v11 * fx
    return (top * (1 - fy) + bot * fy).astype(np.float32)


def domain_warp(field: np.ndarray, strength: float, scale: float, seed: int, iterations: int = 2) -> np.ndarray:
    """两层噪声偏移采样坐标；iterations 控制叠加次数（>=2 时再叠一层）。"""
    res = field.shape[0]
    axis = np.arange(res, dtype=np.float32) / res
    gx, gy = np.meshgrid(axis, axis)
    out = field.astype(np.float32)
    iterations = int(np.clip(iterations, 1, 4))
    for step in range(iterations):
        dx = value_noise(res, max(2.0, scale), (seed + step * 977) & 0xFFFFFFFF, contrast=1.0) - 0.5
        dy = value_noise(res, max(2.0, scale), (seed + step * 1583 + 7) & 0xFFFFFFFF, contrast=1.0) - 0.5
        out = _bilinear_wrap(out, gx + dx * float(strength), gy + dy * float(strength))
    return np.clip(out, 0.0, 1.0).astype(np.float32)
