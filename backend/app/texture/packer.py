"""通道打包：按 channel_mapping_json 合成 RGBA 四通道并输出 8bit PNG。"""
from io import BytesIO

import numpy as np
from PIL import Image

from app.constants.channel import CHANNEL_KEYS, TextureChannel


def load_channel_arrays(base_color: np.ndarray, normal: np.ndarray, roughness: np.ndarray,
                        metallic: np.ndarray, ao: np.ndarray, height: np.ndarray) -> dict:
    return {
        TextureChannel.BASE_COLOR.value: base_color,
        TextureChannel.NORMAL.value: normal,
        TextureChannel.ROUGHNESS.value: roughness,
        TextureChannel.METALLIC.value: metallic,
        TextureChannel.AO.value: ao,
        TextureChannel.HEIGHT.value: height,
    }


def channel_to_gray(array: np.ndarray) -> np.ndarray:
    if array.ndim == 3:
        return np.clip(array.mean(axis=2) * 255.0, 0, 255).astype(np.uint8)
    return np.clip(array.astype(np.float32) * 255.0, 0, 255).astype(np.uint8)


def pack_channels(arrays: dict, mapping: dict, output_format: str = "png") -> bytes:
    """mapping 形如 {"r": "roughness", "g": "metallic", "b": "ao", "a": "height"}；
    output_format 支持 png / tga（Pillow 输出 8bit RGBA）。"""
    reference = arrays[CHANNEL_KEYS[0]]
    h, w = reference.shape[:2]
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    slots = {"r": 0, "g": 1, "b": 2, "a": 3}
    for slot, channel in mapping.items():
        if slot not in slots:
            continue
        if channel not in arrays:
            raise KeyError(channel)
        data = channel_to_gray(arrays[channel])
        if data.shape != (h, w):
            raise ValueError("channel size mismatch")
        rgba[..., slots[slot]] = data
    buf = BytesIO()
    if output_format == "tga":
        Image.fromarray(rgba, mode="RGBA").save(buf, format="TGA")
    else:
        Image.fromarray(rgba, mode="RGBA").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def encode_channel_png(array: np.ndarray) -> bytes:
    if array.ndim == 3:
        img = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), mode="RGB")
    else:
        img = Image.fromarray(channel_to_gray(array), mode="L")
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
