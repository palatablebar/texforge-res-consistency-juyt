"""渲染器：解析 RecipeNode 的 DAG，算出六通道贴图、接缝评分与材质球预览图。"""
import time
from io import BytesIO

import numpy as np
from PIL import Image

from app.constants.node_registry import (
    NODE_TYPE_AO,
    NODE_TYPE_BLEND,
    NODE_TYPE_FBM,
    NODE_TYPE_GRADIENT,
    NODE_TYPE_HEIGHT,
    NODE_TYPE_NORMAL,
    NODE_TYPE_NOISE_PERLIN,
    NODE_TYPE_NOISE_VALUE,
    NODE_TYPE_NOISE_WORLEY,
    NODE_TYPE_WARP,
    PALETTES,
)
from app.constants.noise import NoiseType
from app.texture import derive, gradient, normal_map, packer, seam
from app.texture.noise import dispatch, fbm, perlin_noise, value_noise, worley_noise
from app.texture.warp import domain_warp

NOISE_NODE_MAP = {
    NODE_TYPE_NOISE_VALUE: NoiseType.VALUE.value,
    NODE_TYPE_NOISE_PERLIN: NoiseType.PERLIN.value,
    NODE_TYPE_NOISE_WORLEY: NoiseType.WORLEY.value,
    NODE_TYPE_FBM: NoiseType.FBM.value,
}


def _norm(field: np.ndarray) -> np.ndarray:
    field = np.asarray(field, dtype=np.float32)
    lo, hi = float(field.min()), float(field.max())
    if hi - lo < 1e-6:
        return np.full(field.shape, 0.5, dtype=np.float32)
    return ((field - lo) / (hi - lo)).astype(np.float32)


def _inputs(node, nodes_by_id):
    refs = node.input_refs_json or []
    return {ref.get("slot", "a"): ref.get("from_node_id") for ref in refs if isinstance(ref, dict)}


def _eval_node(node, nodes_by_id, cache, resolution, seed):
    if node.id in cache:
        return cache[node.id]
    params = node.params_json or {}
    local_seed = (int(seed) + int(params.get("seed_offset", 0))) & 0x7FFFFFFF
    inputs = _inputs(node, nodes_by_id)
    field = None

    def upstream(slot):
        nid = inputs.get(slot)
        if not nid or nid not in nodes_by_id:
            return None
        return _eval_node(nodes_by_id[nid], nodes_by_id, cache, resolution, seed)

    if node.node_type in NOISE_NODE_MAP:
        kind = NOISE_NODE_MAP[node.node_type]
        contrast = float(params.get("contrast", 1.0))
        if kind == NoiseType.VALUE.value:
            field = value_noise(resolution, float(params.get("frequency", 6.0)), local_seed, contrast)
        elif kind == NoiseType.PERLIN.value:
            field = perlin_noise(resolution, float(params.get("frequency", 4.0)), local_seed, contrast)
        elif kind == NoiseType.WORLEY.value:
            field = worley_noise(resolution, int(params.get("cells", 10)), local_seed,
                                 float(params.get("jitter", 0.9)), contrast)
        else:
            field = fbm(resolution, int(params.get("octaves", 5)), float(params.get("persistence", 0.5)),
                        float(params.get("lacunarity", 2.0)), float(params.get("frequency", 4.0)), local_seed,
                        "perlin", contrast)
            base = upstream("a")
            if base is not None:
                gray = float(params.get("grayness", 0.5))
                field = np.clip(field * gray + base * (1 - gray), 0.0, 1.0)
    elif node.node_type == NODE_TYPE_GRADIENT:
        base = upstream("a")
        grad = gradient.gradient_field(resolution, float(params.get("angle", 0.0)), float(params.get("softness", 0.35)))
        field = grad if base is None else np.clip(grad * 0.45 + base * 0.55, 0.0, 1.0)
    elif node.node_type == NODE_TYPE_BLEND:
        a = upstream("a")
        b = upstream("b")
        if a is None and b is None:
            field = value_noise(resolution, 5.0, local_seed)
        elif a is None:
            field = b
        elif b is None:
            field = a
        else:
            from app.texture.blend import apply_blend

            field = apply_blend(a, b, str(params.get("mode", "multiply")), float(params.get("opacity", 1.0)))
    elif node.node_type == NODE_TYPE_WARP:
        base = upstream("a")
        if base is None:
            base = fbm(resolution, 4, 0.5, 2.0, 4.0, local_seed)
        field = domain_warp(base, float(params.get("strength", 0.35)), float(params.get("scale", 3.0)),
                            local_seed, int(params.get("iterations", 2)))
    elif node.node_type == NODE_TYPE_HEIGHT:
        base = upstream("a")
        if base is None:
            base = fbm(resolution, 5, 0.5, 2.0, 4.0, local_seed)
        field = _norm(base)
        field = (field - 0.5) * float(params.get("contrast", 1.25)) + 0.5
        if bool(params.get("invert", False)):
            field = 1.0 - field
        field = np.clip(field, 0.0, 1.0)
    elif node.node_type in (NODE_TYPE_NORMAL, NODE_TYPE_AO):
        base = upstream("a")
        field = base if base is not None else fbm(resolution, 4, 0.5, 2.0, 4.0, local_seed)
    else:
        base = upstream("a")
        field = base if base is not None else value_noise(resolution, 6.0, local_seed)

    field = np.clip(np.asarray(field, dtype=np.float32), 0.0, 1.0)
    cache[node.id] = field
    return field


def _graph_params(nodes, node_type: str, defaults: dict) -> dict:
    for node in nodes:
        if node.node_type == node_type and not node.is_disabled:
            merged = dict(defaults)
            merged.update(node.params_json or {})
            return merged
    return dict(defaults)


def render_recipe(nodes, resolution: int, seed: int) -> dict:
    """返回六个通道数组 + seam_score + generation_ms；全部真实像素计算。"""
    started = time.perf_counter()
    active = [n for n in nodes if not n.is_disabled]
    nodes_by_id = {n.id: n for n in active}
    cache: dict[int, np.ndarray] = {}

    terminal = None
    for node in active:
        if node.node_type == NODE_TYPE_HEIGHT:
            terminal = node
            break
    if terminal is None:
        for node in active:
            if node.node_type in (NODE_TYPE_NORMAL, NODE_TYPE_AO, NODE_TYPE_WARP, NODE_TYPE_BLEND):
                terminal = node
    if terminal is None and active:
        terminal = active[-1]
    if terminal is None:
        height = fbm(resolution, 5, 0.5, 2.0, 4.0, seed)
    else:
        height = _eval_node(terminal, nodes_by_id, cache, resolution, seed)
    height = _norm(height)

    height_params = _graph_params(active, NODE_TYPE_HEIGHT, {"palette": "terracotta"})
    palette_name = str(height_params.get("palette", "terracotta"))
    palette = PALETTES.get(palette_name, PALETTES["terracotta"])

    normal_params = _graph_params(active, NODE_TYPE_NORMAL, {"normal_scale": 1.0, "flip_y": False})
    ao_params = _graph_params(active, NODE_TYPE_AO, {"radius": 6, "strength": 0.75})

    normal_rgb = normal_map.height_to_normal(
        height, float(normal_params.get("normal_scale", 1.0)),
        bool(normal_params.get("flip_y", False)), resolution=resolution
    )

    fine = value_noise(resolution, 18.0, (seed + 29) & 0x7FFFFFFF)
    mid = perlin_noise(resolution, 7.0, (seed + 61) & 0x7FFFFFFF)
    roughness = derive.derive_roughness(height, fine, base=float(palette["roughness"]))
    metallic = derive.derive_metallic(height, mid, base=float(palette["metallic"]))
    ao = derive.derive_ao(height, int(ao_params.get("radius", 6)),
                          float(ao_params.get("strength", 0.75)), resolution=resolution)

    tint = np.clip(mid * 0.55 + fine * 0.45, 0.0, 1.0)
    base_color = gradient.colorize(height, palette["from"], palette["to"], tint=tint)

    color_gray = base_color.astype(np.float32).mean(axis=2) / 255.0
    score = seam.seam_score(height, color_gray, resolution=resolution)

    generation_ms = int(round((time.perf_counter() - started) * 1000))
    return {
        "base_color": base_color,
        "normal": normal_rgb,
        "roughness": roughness,
        "metallic": metallic,
        "ao": ao,
        "height": height,
        "seam_score": score,
        "generation_ms": generation_ms,
        "palette": palette,
    }


def make_preview_png(base_color: np.ndarray, normal_rgb: np.ndarray, roughness: np.ndarray,
                     metallic: np.ndarray, ao: np.ndarray, size: int = 512) -> bytes:
    """用 numpy 做一次真实球体着色，产出材质球预览图（RGBA，圆外透明）。"""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    px = (xx + 0.5) / size * 2.0 - 1.0
    py = (yy + 0.5) / size * 2.0 - 1.0
    r2 = px * px + py * py
    inside = r2 <= 1.0
    nz = np.sqrt(np.clip(1.0 - r2, 0.0, 1.0))
    sphere_n = np.stack([px, -py, nz], axis=-1)

    u = np.clip((np.arctan2(sphere_n[..., 0], sphere_n[..., 2]) / (2 * np.pi) + 0.5), 0.0, 0.999)
    v = np.clip((np.arccos(np.clip(sphere_n[..., 1], -1.0, 1.0)) / np.pi), 0.0, 0.999)
    tex_h, tex_w = base_color.shape[:2]
    ix = (u * (tex_w - 1)).astype(np.int32)
    iy = (v * (tex_h - 1)).astype(np.int32)

    albedo = base_color[iy, ix].astype(np.float32) / 255.0
    nt = normal_rgb[iy, ix].astype(np.float32) / 255.0 - 0.5
    rough = roughness[iy, ix].astype(np.float32)
    metal = metallic[iy, ix].astype(np.float32)
    occ = ao[iy, ix].astype(np.float32)

    n = sphere_n + np.stack([nt[..., 0] * 0.9, nt[..., 1] * 0.9, np.zeros_like(nt[..., 0])], axis=-1)
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-6)

    light = np.array([-0.45, 0.55, 0.75], dtype=np.float32)
    light /= np.linalg.norm(light)
    lambert = np.clip((n * light[None, None, :]).sum(axis=-1), 0.0, 1.0)
    half = light + np.array([0.0, 0.0, 1.0], dtype=np.float32)
    half /= np.linalg.norm(half)
    spec_power = 8.0 + (1.0 - rough) * 120.0
    spec = np.power(np.clip((n * half[None, None, :]).sum(axis=-1), 0.0, 1.0), spec_power)
    spec *= (0.25 + 0.75 * (1.0 - rough))

    ambient = 0.32 * occ
    diffuse = albedo * (ambient[..., None] + lambert[..., None] * (0.85 * (1.0 - metal[..., None] * 0.55)))
    spec_color = spec[..., None] * ((1.0 - metal[..., None]) * 0.55 + metal[..., None] * albedo)
    color = np.clip(diffuse + spec_color, 0.0, 1.0)
    color = np.clip(color ** (1.0 / 1.15), 0.0, 1.0) * 255.0

    alpha = np.clip((1.0 - np.sqrt(np.clip(r2, 0.0, 4.0))) * size * 0.16, 0.0, 1.0)
    alpha = np.where(inside, alpha, 0.0)
    rgba = np.zeros((size, size, 4), dtype=np.uint8)
    rgba[..., :3] = np.clip(color, 0, 255).astype(np.uint8)
    rgba[..., 3] = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    buf = BytesIO()
    Image.fromarray(rgba, mode="RGBA").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def encode_channels(result: dict) -> dict[str, bytes]:
    return {
        "base_color": packer.encode_channel_png(result["base_color"]),
        "normal": packer.encode_channel_png(result["normal"]),
        "roughness": packer.encode_channel_png(result["roughness"]),
        "metallic": packer.encode_channel_png(result["metallic"]),
        "ao": packer.encode_channel_png(result["ao"]),
        "height": packer.encode_channel_png(result["height"]),
    }
