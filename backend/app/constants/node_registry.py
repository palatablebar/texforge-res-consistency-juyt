"""节点类型注册表：默认参数、输入槽位、分组。schemas/node.py 与前端 nodeRegistry.ts 同源镜像。"""
from app.constants.blend import BlendMode
from app.constants.channel import TextureChannel
from app.constants.noise import NoiseType

NODE_TYPE_NOISE_VALUE = "noise_value"
NODE_TYPE_NOISE_PERLIN = "noise_perlin"
NODE_TYPE_NOISE_WORLEY = "noise_worley"
NODE_TYPE_FBM = "fbm"
NODE_TYPE_GRADIENT = "gradient"
NODE_TYPE_BLEND = "blend"
NODE_TYPE_WARP = "warp"
NODE_TYPE_HEIGHT = "height"
NODE_TYPE_NORMAL = "normal"
NODE_TYPE_AO = "ao"

NODE_REGISTRY = {
    NODE_TYPE_NOISE_VALUE: {
        "label": "值噪声",
        "group": "noise",
        "noise": NoiseType.VALUE,
        "inputs": [],
        "outputs": ["out"],
        "defaults": {"frequency": 6.0, "seed_offset": 0, "contrast": 1.0},
    },
    NODE_TYPE_NOISE_PERLIN: {
        "label": "柏林噪声",
        "group": "noise",
        "noise": NoiseType.PERLIN,
        "inputs": [],
        "outputs": ["out"],
        "defaults": {"frequency": 4.0, "seed_offset": 3, "contrast": 1.0},
    },
    NODE_TYPE_NOISE_WORLEY: {
        "label": "沃利颗粒",
        "group": "noise",
        "noise": NoiseType.WORLEY,
        "inputs": [],
        "outputs": ["out"],
        "defaults": {"cells": 10, "jitter": 0.9, "seed_offset": 7, "contrast": 1.0},
    },
    NODE_TYPE_FBM: {
        "label": "分形叠加",
        "group": "noise",
        "noise": NoiseType.FBM,
        "inputs": ["a"],
        "outputs": ["out"],
        "defaults": {"octaves": 5, "persistence": 0.5, "lacunarity": 2.0, "frequency": 4.0, "seed_offset": 11, "grayness": 0.5},
    },
    NODE_TYPE_GRADIENT: {
        "label": "渐变",
        "group": "operator",
        "inputs": ["a"],
        "outputs": ["out"],
        "defaults": {"angle": 0.0, "softness": 0.35, "palette": "terracotta"},
    },
    NODE_TYPE_BLEND: {
        "label": "混合",
        "group": "blend",
        "inputs": ["a", "b"],
        "outputs": ["out"],
        "defaults": {"mode": BlendMode.MULTIPLY, "opacity": 0.65},
    },
    NODE_TYPE_WARP: {
        "label": "域扭曲",
        "group": "operator",
        "inputs": ["a"],
        "outputs": ["out"],
        "defaults": {"strength": 0.35, "scale": 3.0, "iterations": 2, "seed_offset": 5},
    },
    NODE_TYPE_HEIGHT: {
        "label": "高度",
        "group": "operator",
        "inputs": ["a"],
        "outputs": ["out"],
        "defaults": {"contrast": 1.25, "invert": False, "palette": "terracotta", "levels": 8},
    },
    NODE_TYPE_NORMAL: {
        "label": "法线",
        "group": "operator",
        "inputs": ["a"],
        "outputs": ["out"],
        "defaults": {"normal_scale": 1.0, "flip_y": False},
    },
    NODE_TYPE_AO: {
        "label": "环境遮蔽",
        "group": "operator",
        "inputs": ["a"],
        "outputs": ["out"],
        "defaults": {"radius": 6, "strength": 0.75},
    },
}

NODE_GROUPS = {
    "noise": [NODE_TYPE_NOISE_VALUE, NODE_TYPE_NOISE_PERLIN, NODE_TYPE_NOISE_WORLEY, NODE_TYPE_FBM],
    "blend": [NODE_TYPE_BLEND],
    "operator": [NODE_TYPE_GRADIENT, NODE_TYPE_WARP, NODE_TYPE_HEIGHT, NODE_TYPE_NORMAL, NODE_TYPE_AO],
}

CHANNEL_NODE_MAP = {
    TextureChannel.HEIGHT.value: NODE_TYPE_HEIGHT,
    TextureChannel.NORMAL.value: NODE_TYPE_NORMAL,
    TextureChannel.AO.value: NODE_TYPE_AO,
}

PALETTES = {
    "terracotta": {
        "name": "哑光陶土",
        "from": (150, 88, 62),
        "to": (214, 172, 138),
        "roughness": 0.72,
        "metallic": 0.02,
    },
    "metal": {
        "name": "拉丝金属",
        "from": (116, 120, 126),
        "to": (198, 203, 209),
        "roughness": 0.32,
        "metallic": 0.9,
    },
    "fabric": {
        "name": "织物",
        "from": (92, 82, 68),
        "to": (198, 188, 166),
        "roughness": 0.9,
        "metallic": 0.0,
    },
}
