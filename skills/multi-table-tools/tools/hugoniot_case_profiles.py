#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hugoniot_case_profiles.py — 单算例多时刻 ρ/v/P 剖面图 (Hugoniot 取样检验)

每个可用时刻画 密度/速度/压强 三联剖面, 标出:
  - 波前位置 (竖虚线, find_front)
  - 波后平台取样窗口 (黄色带, find_plateau)
  - 图例给出该时刻的 Us(局部拟合)/Up/P1/rho1 与 RH 动量残差
便于人工检验提取器取样是否合理。

用法: python3 hugoniot_case_profiles.py <算例目录> <rho0> [时刻数, 默认6]
产物: <算例目录>/profiles_check.png
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_hugoniot import scan_case, extract_series


def main():
    case_dir = sys.argv[1].rstrip("/")
    rho0 = float(sys.argv[2]) if len(sys.argv) > 2 else 1.05
    n_show = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    s = scan_case(case_dir, rho0)
    res = extract_series(case_dir, rho0)
    by_rec = {r["rec"]: r for r in res}
    ok = np.where(s["usable"])[0]
    idx = ok[np.linspace(0, len(ok) - 1, min(n_show, len(ok))).astype(int)]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    cmap = plt.get_cmap("viridis")
    for j, k in enumerate(idx):
        c = cmap(j / max(1, len(idx) - 1))
        t = s["times"][k] * 1e9
        x = s["XC"][k] * 1e4
        n = min(len(x), len(s["R"][k]))
        axes[0].plot(x[:n], s["R"][k][:n], ".-", ms=2.5, lw=1.0, color=c)
        nv = min(len(x), len(s["V"][k]))
        axes[1].plot(x[:nv], s["V"][k][:nv] * 1e-5, ".-", ms=2.5, lw=1.0, color=c)
        axes[2].plot(x[:n], s["PT"][k][:n] * 1e-12, ".-", ms=2.5, lw=1.0, color=c)
        xf = s["xf"][k] * 1e4
        for a in axes:
            a.axvline(xf, color=c, ls="--", lw=0.8, alpha=0.7)
        post = s["post_cells"][k]
        if post is not None:
            x0, x1 = x[post[0]], x[min(post[-1] + 1, len(x) - 1)]
            for a in axes:
                a.axvspan(x0, x1, color=c, alpha=0.15)
        if k in by_rec:
            r = by_rec[k]
            axes[2].annotate(
                f"t={t:.2f}ns  Us={r['Us']/1e5:.2f} Up={r['Up']/1e5:.2f} km/s\n"
                f"P1={r['P1']/1e12:.3f} Mbar  rho1={r['rho1']:.3f}  resid={r['resid']:+.1%}",
                xy=(0.98, 0.03 + 0.155 * j), xycoords="axes fraction",
                ha="right", va="bottom", fontsize=7.5, color=c)
    axes[0].set_ylabel(r"$\rho$ [g/cm$^3$]")
    axes[1].set_ylabel(r"$v$ [km/s]")
    axes[2].set_ylabel(r"$P$ [Mbar]")
    for a in axes:
        a.set_xlabel(r"$x$ [$\mu$m]")
        a.set_xlim(0, s["XC"][-1].max() * 1e4)
    axes[0].set_yscale("log")
    fig.suptitle(f"{os.path.basename(case_dir)}: 取样检验 (虚线=波前, 色带=平台取样窗)", y=1.02)
    fig.tight_layout()
    out = os.path.join(case_dir, "profiles_check.png")
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"{os.path.basename(case_dir)}: {len(idx)} 时刻剖面 → {out}")


if __name__ == "__main__":
    main()
