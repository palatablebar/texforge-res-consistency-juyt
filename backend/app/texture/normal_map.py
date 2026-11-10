"""高度图经 Sobel 求梯度生成切线空间法线，normal_scale 参与强度。"""
import numpy as np

SOBEL_X = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32) / 8.0
SOBEL_Y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32) / 8.0


def _convolve(field: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    padded = np.pad(field, 1, mode="wrap")
    out = np.zeros_like(field, dtype=np.float32)
    for ky in range(3):
        for kx in range(3):
            out += padded[ky : ky + field.shape[0], kx : kx + field.shape[1]] * kernel[ky, kx]
    return out


def height_to_normal(height: np.ndarray, normal_scale: float = 1.0, flip_y: bool = False) -> np.ndarray:
    """返回 HxWx3 uint8 切线空间法线（+Z 朝外）。"""
    height = np.clip(height.astype(np.float32), 0.0, 1.0)
    dx = _convolve(height, SOBEL_X) * float(normal_scale) * 8.0
    dy = _convolve(height, SOBEL_Y) * float(normal_scale) * 8.0
    if flip_y:
        dy = -dy
    nx = -dx
    ny = dy
    nz = np.ones_like(height)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= length
    ny /= length
    nz /= length
    rgb = np.stack([nx * 0.5 + 0.5, ny * 0.5 + 0.5, nz * 0.5 + 0.5], axis=-1)
    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
