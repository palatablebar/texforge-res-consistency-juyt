"""高度图经 Sobel 求梯度生成切线空间法线，normal_scale 参与强度。

分辨率一致性（v2）
------------------
v1 直接对像素网格做 Sobel，梯度是「每像素高度差」：同一高度场在 2048 下的
像素间距只有 512 的 1/4，法线自然平 4 倍。v2 把梯度换算到 UV 空间
（du = 1/res），并以 512 为参考分辨率归一化，使 normal_scale 的语义固定为
「512 参考下的强度」。res=512 时补偿系数恰好为 1，输出与 v1 逐位一致，
已有的 normal_scale 调参不需要任何修改。
"""
import numpy as np

# 配方参数（normal_scale / AO radius 等）的参考分辨率，历史参数均按此调校。
REFERENCE_RESOLUTION = 512
# 生成算法版本：v1 = 修复前（按像素的梯度/半径），v2 = UV 空间分辨率补偿。
# 历史变体在数据库里固定记录其生成时的版本，不会被重算；同一版本号下
# 同配方同 seed 同分辨率仍逐像素一致（checksum 可复现）。
GENERATION_ALGO_VERSION = 2

# 模块级开关，仅供 scripts/verify_resolution_consistency.py --legacy 复现 v1 基线。
ALGO_VERSION = GENERATION_ALGO_VERSION

SOBEL_X = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32) / 8.0
SOBEL_Y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32) / 8.0


def _convolve(field: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    padded = np.pad(field, 1, mode="wrap")
    out = np.zeros_like(field, dtype=np.float32)
    for ky in range(3):
        for kx in range(3):
            out += padded[ky : ky + field.shape[0], kx : kx + field.shape[1]] * kernel[ky, kx]
    return out


def height_to_normal(height: np.ndarray, normal_scale: float = 1.0, flip_y: bool = False,
                     resolution: int | None = None) -> np.ndarray:
    """返回 HxWx3 uint8 切线空间法线（+Z 朝外）。

    resolution 缺省取 height 的边长；v1 基线忽略该参数，保持旧行为。
    """
    height = np.clip(height.astype(np.float32), 0.0, 1.0)
    res = int(resolution) if resolution is not None else int(height.shape[0])
    # v1: 像素空间梯度。v2: 换算到 UV 空间并按参考分辨率归一化，
    # res=512 时 res/512=1，与 v1 完全相同。
    uv_compensation = 1.0 if ALGO_VERSION < 2 else float(res) / float(REFERENCE_RESOLUTION)
    dx = _convolve(height, SOBEL_X) * float(normal_scale) * 8.0 * uv_compensation
    dy = _convolve(height, SOBEL_Y) * float(normal_scale) * 8.0 * uv_compensation
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
