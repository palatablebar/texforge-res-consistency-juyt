"""由高度与噪声派生 roughness / metallic / ao（AO 用局部均值遮蔽近似）。"""
import numpy as np


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


def derive_roughness(height: np.ndarray, noise: np.ndarray, base: float = 0.7, variation: float = 0.22) -> np.ndarray:
    rough = float(base) + (0.5 - height) * float(variation) + (noise - 0.5) * float(variation) * 0.6
    return np.clip(rough, 0.02, 1.0).astype(np.float32)


def derive_metallic(height: np.ndarray, noise: np.ndarray, base: float = 0.05, variation: float = 0.12) -> np.ndarray:
    metallic = float(base) + (height - 0.5) * float(variation) + (noise - 0.5) * 0.04
    return np.clip(metallic, 0.0, 1.0).astype(np.float32)


def derive_ao(height: np.ndarray, radius: int = 6, strength: float = 0.75) -> np.ndarray:
    """局部均值遮蔽：低于邻域均值的地方变暗。"""
    local = box_mean(height, radius)
    delta = np.clip((local - height) * float(strength) * 2.2, 0.0, 1.0)
    ao = np.clip(1.0 - delta, 0.0, 1.0)
    return np.clip(ao * 0.92 + 0.08, 0.0, 1.0).astype(np.float32)


def to_gray_u8(field: np.ndarray) -> np.ndarray:
    return np.clip(field * 255.0, 0, 255).astype(np.uint8)
