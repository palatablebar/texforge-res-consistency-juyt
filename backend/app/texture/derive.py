"""由高度与噪声派生 roughness / metallic / ao（AO 用局部均值遮蔽近似）。

分辨率一致性（v2）
------------------
AO 的 radius 在 v1 是像素半径：radius=6 在 512 上覆盖 12/512≈2.3% 的 UV 宽度，
到 2048 上只剩 0.6%，遮蔽几乎消失。v2 把 radius 解释为「参考分辨率 512 下的
像素半径」，按 res/512 缩放实际盒半径，UV 覆盖范围保持不变。res=512 时
换算结果与原值相同，输出与 v1 逐位一致，历史配方无需改参数。
"""
import numpy as np

from app.texture.normal_map import GENERATION_ALGO_VERSION, REFERENCE_RESOLUTION

# 模块级开关，仅供 scripts/verify_resolution_consistency.py --legacy 复现 v1 基线。
ALGO_VERSION = GENERATION_ALGO_VERSION


def box_mean(field: np.ndarray, radius: int) -> np.ndarray:
    """积分图实现 O(1) 盒式均值，边界环绕。"""
    radius = max(1, int(radius))
    padded = np.pad(field.astype(np.float32), radius, mode="wrap")
    integral = padded.cumsum(0).cumsum(1)
    integral = np.pad(integral, ((1, 0), (1, 0)), mode="constant")
    h, w = field.shape
    size = 2 * radius + 1
    total = (
        integral[size : size + h, size : size + w]
        - integral[0:h, size : size + w]
        - integral[size : size + h, 0:w]
        + integral[0:h, 0:w]
    )
    return (total / (size * size)).astype(np.float32)


def uv_radius_to_pixels(radius: int, resolution: int) -> int:
    """把「参考分辨率下的像素半径」换算成当前分辨率的像素半径。

    v1 直接返回原半径（像素语义）；v2 按 UV 比例缩放并四舍五入，
    res=512 时结果与 v1 相同。
    """
    radius = max(1, int(radius))
    if ALGO_VERSION < 2:
        return radius
    scaled = radius * float(resolution) / float(REFERENCE_RESOLUTION)
    return max(1, int(round(scaled)))


def derive_roughness(height: np.ndarray, noise: np.ndarray, base: float = 0.7, variation: float = 0.22) -> np.ndarray:
    rough = float(base) + (0.5 - height) * float(variation) + (noise - 0.5) * float(variation) * 0.6
    return np.clip(rough, 0.02, 1.0).astype(np.float32)


def derive_metallic(height: np.ndarray, noise: np.ndarray, base: float = 0.05, variation: float = 0.12) -> np.ndarray:
    metallic = float(base) + (height - 0.5) * float(variation) + (noise - 0.5) * 0.04
    return np.clip(metallic, 0.0, 1.0).astype(np.float32)


def derive_ao(height: np.ndarray, radius: int = 6, strength: float = 0.75,
              resolution: int | None = None) -> np.ndarray:
    """局部均值遮蔽：低于邻域均值的地方变暗。"""
    res = int(resolution) if resolution is not None else int(height.shape[0])
    pixel_radius = uv_radius_to_pixels(radius, res)
    local = box_mean(height, pixel_radius)
    delta = np.clip((local - height) * float(strength) * 2.2, 0.0, 1.0)
    ao = np.clip(1.0 - delta, 0.0, 1.0)
    return np.clip(ao * 0.92 + 0.08, 0.0, 1.0).astype(np.float32)


def to_gray_u8(field: np.ndarray) -> np.ndarray:
    return np.clip(field * 255.0, 0, 255).astype(np.uint8)
