"""三种噪声向量化实现 + fbm 叠加。全部 numpy，无逐像素 Python 循环。"""
import numpy as np

from app.constants.noise import NoiseType


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(int(seed) & 0xFFFFFFFF)


def _smooth(t: np.ndarray) -> np.ndarray:
    return t * t * t * (t * (t * 6 - 15) + 10)


def _coords(res: int, cells: int):
    axis = np.linspace(0.0, cells, res, endpoint=False, dtype=np.float32)
    base = np.floor(axis).astype(np.int32)
    frac = axis - base
    return base, frac


def value_noise(res: int, frequency: float, seed: int, contrast: float = 1.0) -> np.ndarray:
    """值噪声：格点随机值 + smoothstep 双线性插值，边界环绕。"""
    cells = max(1, int(round(frequency)))
    lattice = _rng(seed).random((cells + 1, cells + 1)).astype(np.float32)
    lattice[cells, :] = lattice[0, :]
    lattice[:, cells] = lattice[:, 0]
    axis = np.arange(res, dtype=np.float32) / res * cells
    base = np.floor(axis).astype(np.int32)
    frac = axis - base
    fx = _smooth(frac).astype(np.float32)
    fy = _smooth(frac).astype(np.float32)
    x0, x1 = base, base + 1
    gy = base
    row0 = lattice[gy][:, x0] * (1 - fx)[None, :] + lattice[gy][:, x1] * fx[None, :]
    row1 = lattice[gy + 1][:, x0] * (1 - fx)[None, :] + lattice[gy + 1][:, x1] * fx[None, :]
    out = row0 * (1 - fy)[:, None] + row1 * fy[:, None]
    out = (out - 0.5) * float(contrast) + 0.5
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def perlin_noise(res: int, frequency: float, seed: int, contrast: float = 1.0) -> np.ndarray:
    """柏林噪声：格点随机梯度与距离向量点积，smoothstep 插值，边界环绕。"""
    cells = max(1, int(round(frequency)))
    rng = _rng(seed)
    angles = rng.random((cells, cells)).astype(np.float32) * (2 * np.pi)
    gvec = np.stack([np.cos(angles), np.sin(angles)], axis=-1)
    axis = np.arange(res, dtype=np.float32) / res * cells
    gi = np.floor(axis).astype(np.int32)
    gf = axis - gi
    xf, yf = np.meshgrid(gf, gf)
    up = _smooth(yf)
    ux = _smooth(xf)
    out = np.zeros((res, res), dtype=np.float32)
    for dy in (0, 1):
        for dx in (0, 1):
            weight = (ux if dx == 1 else 1 - ux) * (up if dy == 1 else 1 - up)
            gx = ((gi + dx) % cells)[None, :]
            gy = ((gi + dy) % cells)[:, None]
            g = gvec[gy, gx]
            dot = g[..., 0] * (xf - dx) + g[..., 1] * (yf - dy)
            out += weight * dot
    out = out * 0.5 + 0.5
    out = (out - 0.5) * float(contrast) + 0.5
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def _worley_points(cells: int, jitter: float, seed: int) -> np.ndarray:
    rng = _rng(seed)
    pts = 0.5 + (rng.random((cells, cells, 2)).astype(np.float32) - 0.5) * float(jitter)
    return pts


def worley_noise(res: int, cells: int, seed: int, jitter: float = 0.9, contrast: float = 1.0) -> np.ndarray:
    """沃利噪声，返回 F1 距离（像素到最近特征点的距离，归一化到 0~1）。"""
    cells = max(2, int(cells))
    pts = _worley_points(cells, jitter, seed)
    axis = np.arange(res, dtype=np.float32) / res
    gx, gy = np.meshgrid(axis, axis)
    cx = np.floor(gx * cells).astype(np.int32)
    cy = np.floor(gy * cells).astype(np.int32)
    best = np.full((res, res), 4.0, dtype=np.float32)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cell_x = (cx + ox) % cells
            cell_y = (cy + oy) % cells
            px = (cx + ox + pts[cell_y, cell_x, 0]) / cells
            py = (cy + oy + pts[cell_y, cell_x, 1]) / cells
            dist = np.sqrt((gx - px) ** 2 + (gy - py) ** 2)
            np.minimum(best, dist, out=best)
    norm = np.clip(best * cells * 1.25, 0.0, 1.0)
    norm = (norm - 0.5) * float(contrast) + 0.5
    return np.clip(norm, 0.0, 1.0).astype(np.float32)


def fbm(res: int, octaves: int, persistence: float, lacunarity: float, frequency: float, seed: int,
        kind: str = "perlin", contrast: float = 1.0) -> np.ndarray:
    """4~6 个 octave 叠加。"""
    octaves = int(np.clip(octaves, 1, 8))
    total = np.zeros((res, res), dtype=np.float32)
    amplitude = 1.0
    norm = 0.0
    freq = float(frequency)
    for octave in range(octaves):
        octave_seed = (int(seed) + octave * 1013) & 0xFFFFFFFF
        if kind == "value":
            layer = value_noise(res, max(1.0, freq), octave_seed)
        elif kind == "worley":
            layer = worley_noise(res, max(2, int(round(freq))), octave_seed)
        else:
            layer = perlin_noise(res, max(1.0, freq), octave_seed)
        total += layer * amplitude
        norm += amplitude
        amplitude *= float(persistence)
        freq *= float(lacunarity)
    out = total / max(norm, 1e-6)
    out = (out - 0.5) * float(contrast) + 0.5
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def dispatch(noise_type: str, res: int, seed: int, params: dict) -> np.ndarray:
    """NoiseType 分派表：schemas/node.py 与 texture/renderer.py 共用。"""
    params = params or {}
    contrast = float(params.get("contrast", 1.0))
    if noise_type == NoiseType.VALUE.value:
        return value_noise(res, float(params.get("frequency", 6.0)), seed, contrast)
    if noise_type == NoiseType.PERLIN.value:
        return perlin_noise(res, float(params.get("frequency", 4.0)), seed, contrast)
    if noise_type == NoiseType.WORLEY.value:
        return worley_noise(res, int(params.get("cells", 10)), seed, float(params.get("jitter", 0.9)), contrast)
    if noise_type == NoiseType.FBM.value:
        return fbm(
            res,
            int(params.get("octaves", 5)),
            float(params.get("persistence", 0.5)),
            float(params.get("lacunarity", 2.0)),
            float(params.get("frequency", 4.0)),
            seed,
            str(params.get("kind", "perlin")),
            contrast,
        )
    return value_noise(res, 6.0, seed)
