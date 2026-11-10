"""TextureChannel 后端唯一真源：file_paths_json 的键、打包映射、前端通道条都以此为准。"""
from enum import Enum


class TextureChannel(str, Enum):
    BASE_COLOR = "base_color"
    NORMAL = "normal"
    ROUGHNESS = "roughness"
    METALLIC = "metallic"
    AO = "ao"
    HEIGHT = "height"


CHANNEL_ORDER = [
    TextureChannel.BASE_COLOR,
    TextureChannel.NORMAL,
    TextureChannel.ROUGHNESS,
    TextureChannel.METALLIC,
    TextureChannel.AO,
    TextureChannel.HEIGHT,
]

CHANNEL_LABELS = {
    TextureChannel.BASE_COLOR: "基础色",
    TextureChannel.NORMAL: "法线",
    TextureChannel.ROUGHNESS: "粗糙度",
    TextureChannel.METALLIC: "金属度",
    TextureChannel.AO: "环境遮蔽",
    TextureChannel.HEIGHT: "高度",
}

CHANNEL_KEYS = [c.value for c in CHANNEL_ORDER]
