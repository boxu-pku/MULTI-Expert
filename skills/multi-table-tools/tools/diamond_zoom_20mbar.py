#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diamond <20 Mbar 局部 Hugoniot 核验图 (Us-Up / P-rho), PRL 风格.
数据源: hugoniot_summary/plot_data/ 下的模拟点/表自洽线/Romero 2007 理论线.
"""
import sys, os
sys.path.insert(0, "/home/ubuntu/local/MULTI-2D.2026.3/work/eos_opacity_tools")
sys.path.insert(0, "/home/ubuntu/local/IM_tool/IM_tool/im_app/core")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plot_style as ps

PMAX = 20.0
LINE_COLORS = [ps.PRL_COLORS["blue"], ps.PRL_COLORS["red"], ps.PRL_COLORS["green"]]
SUM = "/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/Diamond/hugoniot_summary"
PD = os.path.join(SUM, "plot_data")

import csv as _csv
_rows = list(_csv.DictReader(
    [l for l in open(os.path.join(PD, "multi_points_Diamond.csv"))
     if not l.startswith("#")]))
pts = {k: np.array([float(r[k].replace("+", "")) for r in _rows])
       for k in _rows[0] if k != "case"}
def rd(name, ncol=4):
    return np.genfromtxt(os.path.join(PD, name), delimiter=",", skip_header=2)
selfh = rd("self_hugoniot_Diamond.csv")   # rho1,T,P,Us,Up
rom_s = rd("theory_Diamond_Romero_2007,_DFT_solid.csv")   # Up,Us,P,rho
rom_l = rd("theory_Diamond_Romero_2007,_DFT_liquid.csv")

p_hi = pts["P_Mbar"] <= PMAX
hi = p_hi & (np.abs(pts["RH_resid"]) <= 0.01)
med = p_hi & (np.abs(pts["RH_resid"]) > 0.01) & (np.abs(pts["RH_resid"]) <= 0.10)
low = p_hi & (np.abs(pts["RH_resid"]) > 0.10)   # 门禁内(≤25%)但置信低, 灰色小点

lines = [
    ("Diamond table (self-consistency, ρ0=3.51)", selfh, "0.4", "--", 1.5, 2),
    ("Diamond (Romero 2007, DFT solid)", rom_s, LINE_COLORS[0], "-", 1.5, 1),
    ("Diamond (Romero 2007, DFT liquid)", rom_l, LINE_COLORS[1], "-", 1.5, 1),
]
for plane in ("UsUp", "Prho"):
    fig, ax = plt.subplots(figsize=(6.0, 6.0))
    for label, arr, c, ls, lw, z in lines:
        if arr.ndim != 2 or arr.size == 0:
            continue
        if arr.shape[1] == 5:      # self line: rho1,T,P,Us,Up
            up, us, p, rho = arr[:, 4], arr[:, 3], arr[:, 2], arr[:, 0]
        else:                       # theory: Up,Us,P,rho
            up, us, p, rho = arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3]
        m = (p <= PMAX * 1.15) & np.isfinite(p)
        if plane == "Prho" and np.isnan(p).all():
            continue
        x, y = (up[m], us[m]) if plane == "UsUp" else (rho[m], p[m])
        ax.plot(x, y, color=c, lw=lw, ls=ls, label=label, zorder=z)
    for msk, fmt, lab, z in (
            (low, dict(ms=5, mfc="none", mec="0.55", mew=1.0),
             "MULTI-1D (RH resid 10-25%, low conf)", 4),
            (med, dict(ms=6, mfc="white", mec="black", mew=1.4),
             "MULTI-1D (RH resid 1-10%)", 5),
            (hi, dict(ms=7, mfc="black", mec="black", mew=1.2),
             "MULTI-1D (RH resid <=1%)", 6)):
        if msk.sum() == 0:
            continue
        xx = pts["Up_kms"][msk] if plane == "UsUp" else pts["rho1_gcc"][msk]
        yy = pts["Us_kms"][msk] if plane == "UsUp" else pts["P_Mbar"][msk]
        ax.plot(xx, yy, "o", ls="None", label=lab, zorder=z, **fmt)
    if plane == "UsUp":
        view = hi | med
        xmax = pts["Up_kms"][view].max() * 1.1
        ymax = pts["Us_kms"][view].max() * 1.1
        ps.apply_prl_style(fig, ax, xlabel=ps.LABEL_UP, ylabel=ps.LABEL_US,
                           xlim=(0, xmax), ylim=(0, ymax))
    else:
        ps.apply_prl_style(fig, ax, xlabel=ps.LABEL_RHO, ylabel=ps.LABEL_P,
                           xlim=(3.51 * 0.98, max(pts["rho1_gcc"][view].max(), 8.4)),
                           ylim=(0, PMAX))
    ax.legend(loc="best", fontsize=ps.LEGEND_FONTSIZE * 0.8)
    png = os.path.join(SUM, f"Diamond_hugoniot_{plane}_lt20Mbar.png")
    ps.save_prl_figure(fig, png)
    plt.close(fig)
    print("图:", png)

# <20 Mbar 段定量: dUs vs 表自洽线 (分置信层)
up, us = pts["Up_kms"][p_hi], pts["Us_kms"][p_hi]
o = np.argsort(selfh[:, 4]); lu, lus = selfh[:, 4], selfh[:, 3]
m = (up >= lu.min()) & (up <= lu.max())
ui = np.interp(up[m], lu[o], lus[o])
dd = (us[m] - ui) / ui * 100
res = np.abs(pts["RH_resid"])[p_hi][m]
print(f"<20Mbar 过门禁点 {int(m.sum())}:")
for lab, msk in (("RH<=1%", res <= 0.01), ("1-10%", (res > 0.01) & (res <= 0.10)),
                 ("10-25%", res > 0.10), ("all", np.ones_like(res, bool))):
    if msk.sum():
        print(f"  {lab:8s} n={msk.sum():3d}  dUs med {np.median(dd[msk]):+.2f}%  "
              f"max|{np.abs(dd[msk]).max():.2f}|%")
