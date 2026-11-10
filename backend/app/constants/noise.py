"""NoiseType 后端唯一真源，被 schemas/node.py 的 Literal 与 texture/noise.py 分派表引用。"""
from enum import Enum


class NoiseType(str, Enum):
    VALUE = "value"
    PERLIN = "perlin"
    WORLEY = "worley"
    FBM = "fbm"


NOISE_LABELS = {
    NoiseType.VALUE: "值噪声",
    NoiseType.PERLIN: "柏林噪声",
    NoiseType.WORLEY: "沃利噪声",
    NoiseType.FBM: "分形叠加",
}

NOISE_DEFAULTS = {
    NoiseType.VALUE: {"frequency": 6.0, "seed_offset": 0},
    NoiseType.PERLIN: {"frequency": 4.0, "seed_offset": 3},
    NoiseType.WORLEY: {"cells": 10, "jitter": 0.9, "seed_offset": 7},
    NoiseType.FBM: {"octaves": 5, "persistence": 0.5, "lacunarity": 2.0, "frequency": 4.0, "seed_offset": 11},
}
