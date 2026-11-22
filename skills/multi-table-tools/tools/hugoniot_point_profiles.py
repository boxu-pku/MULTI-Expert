#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hugoniot_point_profiles.py — 为每个 Hugoniot 采样点生成溯源剖面图

对汇总图上的每一个点, 画出该时刻的 rho/v/P 剖面 + 波前轨迹诊断:
  面板1-3: rho / v / P 剖面, 标注波前(绿虚线)、波前态取样(蓝)、波后取样(红)
  面板4: 波前轨迹 x_f(t) 全程 —— 绿色=过门禁时段, 灰色=被剔除时段,
         红色线段=本点 Us 的局部线性拟合窗口, 斜率即 Us
  标题给出提取值与波前态 Te(检验预热是否污染)

用法: python3 hugoniot_point_profiles.py <算例目录> <rho0>
产物: <算例目录>/hugoniot_points/point_XX_tYYns.png (每个采信点一张)
"""
import os
import sys
import numpy as np

sys.path.insert(0, "/home/ubuntu/local/MULTI-2D.2026.3/work/eos_opacity_tools")
from plot_1d_validation import read_fort10_ascii
from extract_hugoniot import extract_series, scan_case

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    case_dir = sys.argv[1].rstrip("/")
    rho0 = float(sys.argv[2]) if len(sys.argv) > 2 else 2.7
    res = extract_series(case_dir, rho0)
    s = scan_case(case_dir, rho0)
    d = read_fort10_ascii(os.path.join(case_dir, "fort.10"))
    TE = d["TE"]
    XC, R, V, PT = s["XC"], s["R"], s["V"], s["PT"]
    XIF = d["X"]                    # 界面坐标 (n+1), V 定义在界面上
    times, xf, usable = s["times"], s["xf"], s["usable"]

    outdir = os.path.join(case_dir, "hugoniot_points")
    os.makedirs(outdir, exist_ok=True)
    tag = os.path.basename(case_dir)

    # 位置坐标固定为初始靶范围(与密度热图约定一致), 不随时刻/波前位置变化
    x_lo, x_hi = XC[0].min() * 1e4, XC[0].max() * 1e4

    for j, r in enumerate(res):
        k = r["rec"]
        x = XC[k] * 1e4
        xv = XIF[k] * 1e4           # 界面坐标(用于 v)
        fig, axes = plt.subplots(1, 4, figsize=(17.5, 4.0))
        for ax, xx, var, unit, lab in [
                (axes[0], x, R[k], "g/cm$^3$", r"$\rho$"),
                (axes[1], xv, V[k] / 1e5, "km/s", "v"),
                (axes[2], x, PT[k] / 1e12, "Mbar", "P")]:
            ax.plot(xx, var, "k-", lw=1.2)
            pre = r["pre_cells"]
            ax.axvspan(x[pre[0]], x[pre[-1]], color="royalblue", alpha=0.25,
                       label="pre-shock sample")
            post = r["post_cells"]
            ax.axvspan(x[post[0]], x[post[-1]], color="red", alpha=0.25,
                       label="post-shock sample")
            xf_now = x[r["i_front"]]
            ax.axvline(xf_now, color="green", ls="--", lw=1.2, label="shock front")
            # 固定为初始坐标范围
            ax.set_xlim(x_lo, x_hi)
            ax.set_ylabel(f"{lab} ({unit})")
            ax.set_xlabel(r"position ($\mu$m)")
            ax.grid(alpha=0.3)
        axes[0].legend(fontsize=8, loc="best")

        # ---- 面板4: 波前轨迹 + 局部拟合 ----
        ax = axes[3]
        fin = np.isfinite(xf)
        # 被剔除时段(灰)与可用时段(绿)分段绘制
        ax.plot(times[fin & ~usable] * 1e9, xf[fin & ~usable] * 1e4, ".",
                ms=3, color="0.75", label="excluded (gates A-D)")
        ax.plot(times[fin & usable] * 1e9, xf[fin & usable] * 1e4, ".",
                ms=3, color="green", label="usable")
        # 本点的局部拟合窗口
        w0, w1, slope, intercept = r["fit_win"]
        tw = times[w0:w1 + 1] * 1e9
        ax.plot(tw, (slope * times[w0:w1 + 1] + intercept) * 1e4, "r-", lw=1.8,
                label=f"local fit → Us={r['Us']/1e5:.3f} km/s")
        ax.plot(r["t"] * 1e9, xf[k] * 1e4, "ro", ms=7, mfc="none", mew=1.5)
        ax.axvline(r["t"] * 1e9, color="red", ls=":", lw=0.8)
        # 纵轴同样固定为初始靶范围: 后期网格飞散到负坐标, 无关
        ax.set_ylim(x_lo, x_hi)
        ax.set_xlabel("t (ns)")
        ax.set_ylabel(r"front position $x_f$ ($\mu$m)")
        ax.set_title(f"front trajectory (fit $R^2$={r['fit_r2']:.4f})", fontsize=10)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="best")

        # 波前态预热温度(检验预热污染)
        te_pre = float(np.median(TE[k][r["pre_cells"]]))
        fig.suptitle(
            f"{tag} point #{j+1} @ t={r['t']*1e9:.2f} ns (record {k+1}):  "
            f"Us={r['Us']/1e5:.3f} km/s, Up={r['Up']/1e5:.3f} km/s, "
            f"P1={r['P1']/1e12:.3f} Mbar, rho1={r['rho1']:.3f} g/cc, "
            f"Te_pre={te_pre:.3f} eV, RH resid={r['resid']:+.1%}")
        fig.tight_layout()
        out = os.path.join(outdir, f"point_{j+1:02d}_t{r['t']*1e9:.2f}ns.png")
        fig.savefig(out, dpi=130)
        plt.close(fig)
    print(f"{tag}: {len(res)} 张溯源图 → {outdir}")


if __name__ == "__main__":
    main()
