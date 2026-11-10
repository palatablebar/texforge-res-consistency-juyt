"""跨分辨率材质一致性验证脚本（可直接命令行运行，只依赖 numpy / Pillow）。

用途
----
对 seed 里的三个配方分别用 512 与 2048 渲染六通道，把 2048 结果按 UV 空间
（平铺感知的区域均值，等价于 mipmap 下采样）缩到 512，与直接生成的 512 逐通道
计算 MAE / RMSE / max abs（统一换算到 0~255 量纲，外包可直接看）；
同时输出 2x2 平铺后四条拼接边界的断层量（均值 + 最大，0~255 量纲）。

另外校验：
  * 同配方同 seed 同分辨率两次渲染逐像素一致（确定性 / checksum 依据）；
  * --compare 模式额外校验：512 下 v1（修复前）与 v2（修复后）逐像素一致
    （证明历史 normal_scale / AO radius 参数不需要 TA 手动调整），以及
    2048 耗时 v2 相对 v1 的倍率（约束：不得超过 2x）。

用法
----
  python3 scripts/verify_resolution_consistency.py              # 只跑修复后 v2
  python3 scripts/verify_resolution_consistency.py --legacy     # 只跑修复前 v1 基线
  python3 scripts/verify_resolution_consistency.py --compare    # 两版都跑，输出对比与验收门槛
  python3 scripts/verify_resolution_consistency.py --compare --json out.json
"""
import argparse
import copy
import json
import os
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402  (sys.path 需先就位)

from app.constants.node_registry import (  # noqa: E402
    NODE_TYPE_AO,
    NODE_TYPE_BLEND,
    NODE_TYPE_FBM,
    NODE_TYPE_HEIGHT,
    NODE_TYPE_NOISE_PERLIN,
    NODE_TYPE_NOISE_VALUE,
    NODE_TYPE_NOISE_WORLEY,
    NODE_TYPE_NORMAL,
    NODE_TYPE_WARP,
)
from app.texture import derive as derive_mod  # noqa: E402
from app.texture import normal_map as normal_mod  # noqa: E402
from app.texture.renderer import render_recipe  # noqa: E402

LOW_RES = 512
HIGH_RES = 2048
CHANNELS = ("base_color", "normal", "roughness", "metallic", "ao", "height")
# 验收门槛（0~255 色阶）：本次修复针对法线与 AO，硬门限 4 色阶（视觉无感区间）；
# 其余通道不设硬门限，但要求 v2 不得劣于 v1（height/base_color 等的残差来自
# 高频细节的面积平均与 8bit 量化，且约束 #4 不允许改动 512 输出）。
MAE_HARD_GATE = {"normal": 4.0, "ao": 4.0}
# 耗时门槛：2048 v2 相对 v1 不得慢一倍以上。
TIME_GATE_X = 2.0


def _n(node_type, params, inputs=None):
    return SimpleNamespace(
        node_type=node_type,
        params_json=params,
        input_refs_json=[{"slot": slot, "from_node_id": idx} for slot, idx in (inputs or {}).items()],
        is_disabled=False,
        id=None,
    )


def _build_nodes(spec):
    nodes = [_n(t, p, refs) for t, p, refs in spec]
    for idx, node in enumerate(nodes):
        node.id = idx
    return nodes


SEED_RECIPES = [
    {
        "slug": "prj-2611-terracotta",
        "name": "PRJ-2611-陶土外墙",
        "seed": 2611001,
        "nodes": _build_nodes([
            (NODE_TYPE_NOISE_VALUE, {"frequency": 7.0, "seed_offset": 0, "contrast": 1.0}, {}),
            (NODE_TYPE_FBM, {"octaves": 5, "persistence": 0.5, "lacunarity": 2.0,
                             "frequency": 3.5, "seed_offset": 11, "grayness": 0.45}, {"a": 0}),
            (NODE_TYPE_NOISE_WORLEY, {"cells": 11, "jitter": 0.9, "seed_offset": 7,
                                      "contrast": 1.1}, {"a": 1}),
            (NODE_TYPE_WARP, {"strength": 0.34, "scale": 3.0, "iterations": 2,
                              "seed_offset": 5}, {"a": 2}),
            (NODE_TYPE_HEIGHT, {"contrast": 1.25, "invert": False, "palette": "terracotta",
                                "levels": 8}, {"a": 3}),
            (NODE_TYPE_NORMAL, {"normal_scale": 1.05, "flip_y": False}, {"a": 4}),
            (NODE_TYPE_AO, {"radius": 6, "strength": 0.8}, {"a": 4}),
        ]),
    },
    {
        "slug": "prj-2611-brushed-metal",
        "name": "PRJ-2611-拉丝金属",
        "seed": 2612007,
        "nodes": _build_nodes([
            (NODE_TYPE_NOISE_PERLIN, {"frequency": 8.0, "seed_offset": 3, "contrast": 1.2}, {}),
            (NODE_TYPE_FBM, {"octaves": 4, "persistence": 0.55, "lacunarity": 2.4,
                             "frequency": 5.0, "seed_offset": 11, "grayness": 0.55}, {"a": 0}),
            (NODE_TYPE_WARP, {"strength": 0.18, "scale": 9.0, "iterations": 2,
                              "seed_offset": 5}, {"a": 1}),
            (NODE_TYPE_HEIGHT, {"contrast": 1.05, "invert": False, "palette": "metal",
                                "levels": 6}, {"a": 2}),
            (NODE_TYPE_NORMAL, {"normal_scale": 0.8, "flip_y": False}, {"a": 3}),
        ]),
    },
    {
        "slug": "prj-2611-fabric",
        "name": "PRJ-2611-织物",
        "seed": 2613043,
        "nodes": _build_nodes([
            (NODE_TYPE_NOISE_WORLEY, {"cells": 18, "jitter": 0.7, "seed_offset": 7}, {}),
            (NODE_TYPE_NOISE_VALUE, {"frequency": 32.0, "seed_offset": 0}, {}),
            (NODE_TYPE_BLEND, {"mode": "overlay", "opacity": 0.58}, {"a": 0, "b": 1}),
            (NODE_TYPE_WARP, {"strength": 0.12, "scale": 6.0, "iterations": 1,
                              "seed_offset": 5}, {"a": 2}),
            (NODE_TYPE_HEIGHT, {"contrast": 1.1, "invert": False, "palette": "fabric",
                                "levels": 7}, {"a": 3}),
            (NODE_TYPE_NORMAL, {"normal_scale": 0.9, "flip_y": False}, {"a": 4}),
        ]),
    },
]


def _set_algo(version: int) -> None:
    normal_mod.ALGO_VERSION = version
    derive_mod.ALGO_VERSION = version


def _to01(arr: np.ndarray) -> np.ndarray:
    return arr.astype(np.float32) / 255.0 if arr.dtype == np.uint8 else arr.astype(np.float32)


def downscale_tiled(arr: np.ndarray, factor: int) -> np.ndarray:
    """平铺感知的区域均值下采样（wrap 语义，等价于先做 box mip 再取 LOD）。

    高分辨率贴图在引擎里按同一 UV 采样，低通 + 面积平均才是和直接出 512
    可比的对照；普通中心对齐 resize 会在平铺边缘引入半像素错位。
    """
    arr = _to01(arr)
    h, w = arr.shape[:2]
    if h % factor or w % factor:
        raise ValueError(f"分辨率 {w}x{h} 不能被缩放因子 {factor} 整除")
    if arr.ndim == 3:
        out = arr.reshape(h // factor, factor, w // factor, factor, arr.shape[2])
        return out.mean(axis=(1, 3), dtype=np.float32)
    out = arr.reshape(h // factor, factor, w // factor, factor)
    return out.mean(axis=(1, 3), dtype=np.float32)


def channel_errors(low: np.ndarray, high_ds: np.ndarray) -> dict:
    """两图统一到 0~255 量纲后算 MAE / RMSE / max abs；彩色通道按通道平均。"""
    diff = (_to01(low) - _to01(high_ds)) * 255.0
    if diff.ndim == 3:
        diff = diff.mean(axis=2)
    return {
        "mae_8bit": round(float(np.mean(np.abs(diff))), 3),
        "rmse_8bit": round(float(np.sqrt(np.mean(diff ** 2))), 3),
        "max_abs_8bit": round(float(np.max(np.abs(diff))), 3),
    }


def tile_seam_jump(arr: np.ndarray) -> dict:
    """2x2 平铺后四条拼接边界的断层量（0~255 量纲）。

    拼缝两侧本来就是同一对边缘列/行，完全连续时差值为 0；同时给出边界
    梯度差，检测缝两侧斜率突变。
    """
    a = _to01(arr)
    if a.ndim == 3:
        a = a.mean(axis=2)
    a = a * 255.0
    v = np.abs(a[:, -1] - a[:, 0])
    h = np.abs(a[-1, :] - a[0, :])
    vg = np.abs((a[:, -1] - a[:, -2]) - (a[:, 1] - a[:, 0]))
    hg = np.abs((a[-1, :] - a[-2, :]) - (a[1, :] - a[0, :]))
    return {
        "edge_mean_8bit": round(float((v.mean() + h.mean()) / 2.0), 3),
        "edge_max_8bit": round(float(max(v.max(), h.max())), 3),
        "gradient_mean_8bit": round(float((vg.mean() + hg.mean()) / 2.0), 3),
        "gradient_max_8bit": round(float(max(vg.max(), hg.max())), 3),
    }


def _render(nodes, resolution, seed):
    started = time.perf_counter()
    result = render_recipe(copy.deepcopy(nodes), resolution, seed)
    elapsed_ms = int(round((time.perf_counter() - started) * 1000))
    return result, elapsed_ms


def _as_u8(arr: np.ndarray) -> np.ndarray:
    return arr if arr.dtype == np.uint8 else np.round(arr * 255.0).astype(np.uint8)


def run_version(algo_version: int) -> dict:
    _set_algo(algo_version)
    report = {"algo_version": algo_version, "low_res": LOW_RES, "high_res": HIGH_RES, "recipes": []}
    factor = HIGH_RES // LOW_RES

    for spec in SEED_RECIPES:
        nodes, seed = spec["nodes"], spec["seed"]
        low, low_ms = _render(nodes, LOW_RES, seed)
        high, high_ms = _render(nodes, HIGH_RES, seed)
        low_re, _ = _render(nodes, LOW_RES, seed)  # 确定性复算

        recipe_report = {
            "slug": spec["slug"],
            "name": spec["name"],
            "seed": seed,
            "render_ms": {"res512": low_ms, "res2048": high_ms},
            "seam_score": {"res512": low["seam_score"], "res2048": high["seam_score"]},
            "determinism_pixel_identical": bool(
                all(np.array_equal(_as_u8(low_re[ch]), _as_u8(low[ch])) for ch in CHANNELS)
            ),
            "raw": {"low": low, "high": high},
            "channels": {},
        }
        for ch in CHANNELS:
            high_ds = downscale_tiled(high[ch], factor)
            recipe_report["channels"][ch] = {
                "cross_resolution_error": channel_errors(low[ch], high_ds),
                "tile_seam_512": tile_seam_jump(low[ch]),
                "tile_seam_2048": tile_seam_jump(high[ch]),
            }
        report["recipes"].append(recipe_report)
    return report


def print_report(report: dict) -> None:
    ver = report["algo_version"]
    print("=" * 100)
    print(f"生成算法版本: v{ver}（"
          f"{'修复前基线：法线按像素求导 / AO 半径按像素 / seam 梯度按像素' if ver == 1 else '修复后：全部按 UV 空间补偿'}）")
    print(f"对照方式: {report['high_res']} 平铺区域均值下采样到 {report['low_res']}，误差量纲均为 0~255 色阶")
    for recipe in report["recipes"]:
        print("-" * 100)
        print(f"配方 {recipe['slug']}  {recipe['name']}  seed={recipe['seed']}")
        rms = recipe["render_ms"]
        print(f"  耗时: 512={rms['res512']}ms  2048={rms['res2048']}ms"
              f"（2048/512 倍率仅反映像素总量 {round(rms['res2048'] / max(rms['res512'], 1), 1)}x，非验收门槛）")
        print(f"  seam_score: 512={recipe['seam_score']['res512']}  2048={recipe['seam_score']['res2048']}  "
              f"同参同 seed 逐像素一致: {'是' if recipe['determinism_pixel_identical'] else '否'}")
        print(f"  {'通道':<10}{'MAE':>9}{'RMSE':>9}{'maxAbs':>9}"
              f"{' | 512缝均值':>13}{'512缝最大':>11}{'2048缝均值':>13}{'2048缝最大':>11}")
        for ch in CHANNELS:
            stat = recipe["channels"][ch]
            err, s512, s2048 = stat["cross_resolution_error"], stat["tile_seam_512"], stat["tile_seam_2048"]
            print(f"  {ch:<10}{err['mae_8bit']:>9.3f}{err['rmse_8bit']:>9.3f}{err['max_abs_8bit']:>9.3f}"
                  f"{s512['edge_mean_8bit']:>13.3f}{s512['edge_max_8bit']:>11.3f}"
                  f"{s2048['edge_mean_8bit']:>13.3f}{s2048['edge_max_8bit']:>11.3f}")
    print("=" * 100)


def print_comparison(v1: dict, v2: dict) -> None:
    print("\n" + "#" * 100)
    print("验收对比（v1 修复前 → v2 修复后）")
    print("#" * 100)
    all_pass = True
    for r1, r2 in zip(v1["recipes"], v2["recipes"]):
        print(f"\n■ {r1['slug']}  seed={r1['seed']}")
        # 门槛 1：512 下 v1/v2 逐像素一致（历史配方观感不变）
        same_512 = all(np.array_equal(_as_u8(r1["raw"]["low"][ch]), _as_u8(r2["raw"]["low"][ch]))
                       for ch in CHANNELS)
        print(f"  [门槛] 512 下 v1/v2 六通道逐像素一致（TA 无需改配方）: {'通过 ✔' if same_512 else '失败 ✘'}")
        all_pass &= same_512
        # 门槛 2：跨分辨率 MAE；法线/AO 过硬门限，其余通道不劣于 v1
        print(f"  {'通道':<10}{'v1 MAE':>10}{'v2 MAE':>10}{'降幅':>9}  门槛")
        for ch in CHANNELS:
            e1 = r1["channels"][ch]["cross_resolution_error"]["mae_8bit"]
            e2 = r2["channels"][ch]["cross_resolution_error"]["mae_8bit"]
            drop = (e1 - e2) / e1 * 100.0 if e1 > 1e-9 else 0.0
            hard_gate = MAE_HARD_GATE.get(ch)
            gate_text = f"MAE<{hard_gate:g}" if hard_gate is not None else "不劣于v1"
            ok = (e2 < hard_gate) if hard_gate is not None else (e2 <= e1 + 1e-9)
            all_pass &= ok
            print(f"  {ch:<10}{e1:>10.3f}{e2:>10.3f}{drop:>8.1f}%  {gate_text} {'通过 ✔' if ok else '未达门限 ✘'}")
        # 门槛 3：seam_score 不得变差
        seam_ok = (r2["seam_score"]["res512"] >= r1["seam_score"]["res512"]
                   and r2["seam_score"]["res2048"] >= r1["seam_score"]["res2048"])
        print(f"  [门槛] seam_score 不变差: v1={r1['seam_score']} v2={r2['seam_score']} "
              f"{'通过 ✔' if seam_ok else '失败 ✘'}")
        all_pass &= seam_ok
        # 门槛 4：2048 耗时 v2/v1 < 2x
        ratio = r2["render_ms"]["res2048"] / max(r1["render_ms"]["res2048"], 1)
        time_ok = ratio < TIME_GATE_X
        print(f"  [门槛] 2048 耗时: v1={r1['render_ms']['res2048']}ms v2={r2['render_ms']['res2048']}ms "
              f"倍率={ratio:.2f}x（<{TIME_GATE_X:.0f}x）{'通过 ✔' if time_ok else '失败 ✘'}")
        all_pass &= time_ok
        # 确定性
        det_ok = r2["determinism_pixel_identical"]
        print(f"  [门槛] v2 同配方同 seed 同分辨率逐像素一致: {'通过 ✔' if det_ok else '失败 ✘'}")
        all_pass &= det_ok
    print("\n" + ("全部验收门槛通过 ✔" if all_pass else "存在未通过项，请检查上面标记 ✘ 的行"))
    print("#" * 100)


def _strip_raw(report: dict) -> dict:
    clean = copy.deepcopy(report)
    for recipe in clean["recipes"]:
        recipe.pop("raw", None)
    return clean


def main() -> int:
    parser = argparse.ArgumentParser(description="跨分辨率材质一致性验证")
    parser.add_argument("--legacy", action="store_true", help="只使用修复前 v1 实现跑基线数字")
    parser.add_argument("--compare", action="store_true", help="v1/v2 都跑并输出验收对比（耗时约翻倍）")
    parser.add_argument("--json", dest="json_path", default=None, help="把完整报告写入 JSON 文件")
    args = parser.parse_args()

    if args.compare:
        v1 = run_version(1)
        v2 = run_version(normal_mod.GENERATION_ALGO_VERSION)
        print_report(v1)
        print_report(v2)
        print_comparison(v1, v2)
        payload = {"v1": _strip_raw(v1), "v2": _strip_raw(v2)}
    else:
        report = run_version(1 if args.legacy else normal_mod.GENERATION_ALGO_VERSION)
        print_report(report)
        payload = _strip_raw(report)

    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print(f"机器可读报告已写入: {args.json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
