"""接缝评分：比对左右边缘列与上下边缘行的像素差与梯度差，归一化成 0~100。"""
import numpy as np


def seam_score(*fields: np.ndarray) -> int:
    """fields 为若干 0~1 单通道场（高度、噪声等），返回整数 0~100。"""
    if not fields:
        return 100
    totals = []
    for field in fields:
        arr = field.astype(np.float32)
        if arr.ndim == 3:
            arr = arr.mean(axis=2)
        left, right = arr[:, 0], arr[:, -1]
        top, bottom = arr[0, :], arr[-1, :]
        # 梯度差：相邻边缘内侧像素的一阶差分
        left_g = arr[:, 1] - arr[:, 0]
        right_g = arr[:, -1] - arr[:, -2]
        top_g = arr[1, :] - arr[0, :]
        bottom_g = arr[-1, :] - arr[-2, :]
        diff = float(np.mean(np.abs(left - right))) + float(np.mean(np.abs(top - bottom)))
        grad = float(np.mean(np.abs(left_g - right_g))) + float(np.mean(np.abs(top_g - bottom_g)))
        totals.append(0.65 * diff + 0.35 * grad)
    raw = float(np.mean(totals))
    score = 100.0 - raw * 320.0
    return int(np.clip(round(score), 0, 100))
