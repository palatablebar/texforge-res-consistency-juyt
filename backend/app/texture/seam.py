"""接缝评分：比对左右边缘列与上下边缘行的像素差与梯度差，归一化成 0~100。

分辨率一致性（v2）
------------------
梯度差是相邻像素的一阶差分，本身按像素尺度计量：同一道缝在 2048 下的
像素梯度只有 512 的 1/4，梯度项会随分辨率升高而虚高 seam_score。v2 对
梯度项乘以 res/512，把它归一到参考分辨率的尺度；res=512 时系数为 1，
分数与 v1 完全一致。边缘值差（diff）是同一对边缘像素的直接差值，
与分辨率无关，不做缩放。
"""
import numpy as np

from app.texture.normal_map import REFERENCE_RESOLUTION


def seam_score(*fields: np.ndarray, resolution: int | None = None) -> int:
    """fields 为若干 0~1 单通道场（高度、噪声等），返回整数 0~100。"""
    if not fields:
        return 100
    res = int(resolution) if resolution is not None else int(fields[0].shape[0])
    grad_scale = float(res) / float(REFERENCE_RESOLUTION)
    totals = []
    for field in fields:
        arr = field.astype(np.float32)
        if arr.ndim == 3:
            arr = arr.mean(axis=2)
        left, right = arr[:, 0], arr[:, -1]
        top, bottom = arr[0, :], arr[-1, :]
        # 梯度差：相邻边缘内侧像素的一阶差分（归一到参考分辨率尺度）
        left_g = (arr[:, 1] - arr[:, 0]) * grad_scale
        right_g = (arr[:, -1] - arr[:, -2]) * grad_scale
        top_g = (arr[1, :] - arr[0, :]) * grad_scale
        bottom_g = (arr[-1, :] - arr[-2, :]) * grad_scale
        diff = float(np.mean(np.abs(left - right))) + float(np.mean(np.abs(top - bottom)))
        grad = float(np.mean(np.abs(left_g - right_g))) + float(np.mean(np.abs(top_g - bottom_g)))
        totals.append(0.65 * diff + 0.35 * grad)
    raw = float(np.mean(totals))
    score = 100.0 - raw * 320.0
    return int(np.clip(round(score), 0, 100))
