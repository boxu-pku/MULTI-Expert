#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_cwk_corrected.py — 用修正后的刘兴碳数据重建 C_wk 表（2026-08-25）

背景: 原 C_wk 表 (weikang2multi.py, 2026-08-11) 用了论文 A.2 坏 P 列 (=E/100),
且 ρ 网格只剩 7 档 (D 支 3/3.51/5 全丢)。本脚本从 work/liuxing/EOS_carbon_corrected.csv
(232 点, Sheet1 正确 P, 见 analysis/liuxing_a2/unit_verification.md) 重建:
  1. 全部 21 个源 ρ 档; T 网 geomspace(数据min, 1393.16, 100)
  2. 组装: 每列 T 内 np.interp (含跨 0.86-4.31 eV 构型桥接);
     列数据范围外的格点按行向 log ρ 从有数据列插值填充 (冷角/高温尾物理平滑,
     优于原版"最近值常数延伸")
  3. 复用原管线后段: EOS-tools multi writer → make_1d_eos 拆分 (库内统一语义)
单位: P_Mbar→MPa ×1e5; E_eV/C→J/g ×96485.33/12.011
"""
import os, sys, csv
import numpy as np

MULTI = "/home/ubuntu/local/MULTI-2D.2026.3"
sys.path.insert(0, "/home/ubuntu/local/EOS_converter_xubo/EOS-tools")
sys.path.insert(0, f"{MULTI}/work/eos_opacity_tools")
import warnings; warnings.filterwarnings("ignore")
from eoslib.model import EOSDataset, EOSMetadata
import eoslib.formats.multi as multi_fmt
from batch_migrate import make_1d_eos

SRC = f"{MULTI}/work/liuxing/EOS_carbon_corrected.csv"
BACKUP = f"{MULTI}/work/cwk_rebuild_20260825"
TABLES = f"{MULTI}/r94/MULTI-IFE-2015/tables"
A = 12.011
NA_EV_TO_JPG = 96485.33

# ---- 1. 读修正源, 按 ρ 分列 ----
rows = []
for ln in open(SRC, encoding="utf-8"):
    if ln.startswith("#"):
        continue
    p = ln.strip().split(",")
    if p and p[0] != "cfg":
        rows.append((float(p[1]), float(p[2]), float(p[3]), float(p[4])))
cols = {}
for r, t, p_, e in rows:
    lst = cols.setdefault(r, [])
    if any(abs(t - x[0]) < 1e-6 for x in lst):   # D/0.002 同 (ρ,T) 重复行取均值
        lst[:] = [((x[0]+t)/2, (x[1]+p_)/2, (x[2]+e)/2) if abs(t-x[0])<1e-6 else x for x in lst]
    else:
        lst.append((t, p_, e))
rhos = np.array(sorted(cols))
print(f"源: {len(rows)} 点, {len(rhos)} 个 ρ 档: {rhos}")
tmin = min(min(x[0] for x in cols[r]) for r in rhos)
tmax = max(max(x[0] for x in cols[r]) for r in rhos)
Tg = np.geomspace(tmin, tmax, 160)
nr, nt = len(rhos), len(Tg)

# ---- 2. 组装: 源列内插值 + 无数据处借库内 Diamond 表 (同材料 hyades 源,
#      角落行为已被 Diamond 系算例证明运行时稳定; 2026-08-25 手工填充六连败后定版) ----
from compute_table_hugoniot import IEOSEval
_dE = IEOSEval(f"{MULTI}/r94/MULTI-IFE-2015/tables/Diamond_eos_e")
_dI = IEOSEval(f"{MULTI}/r94/MULTI-IFE-2015/tables/Diamond_eos_i")
def diamond(rho, T_ev):
    TK = T_ev * 11604.519
    pe, ee = _dE(rho, TK); pi, ei = _dI(rho, TK)
    return (pe + pi), (ee + ei) * 12.4524         # P Mbar, E eV/C
Tg = np.geomspace(0.0257, 1393.16, 160)          # 底取 Diamond 同款 298K
rhos_src = np.array(sorted(cols))
# ρ 网格: Diamond 93 档(≤100) ∪ 源 ρ 档 — 匹配已验证表的密度分辨率
_drho = sorted(set(round(float(x), 4) for x in _dE.r if x <= 100))
rhos = np.array(sorted(set(_drho) | set(round(float(x), 4) for x in rhos_src)))
nr, nt = len(rhos), len(Tg)
P = np.full((nr, nt), np.nan); E = np.full((nr, nt), np.nan)
for i, r in enumerate(rhos):
    if r not in cols:
        continue
    arr = np.array(sorted(cols[r]))
    T, Pv, Ev = arr[:, 0], arr[:, 1], arr[:, 2]
    m = (Tg >= T[0]) & (Tg <= T[-1])
    P[i, m] = np.interp(Tg[m], T, Pv)
    E[i, m] = np.interp(Tg[m], T, Ev)
# 无数据格点: 借 Diamond; 能量零点按列加常数偏移 (列最近数据端对齐)
for i, r in enumerate(rhos):
    m = np.isnan(P[i])
    if not m.any():
        continue
    if r in cols:
        arr = np.array(sorted(cols[r]))
        t_seam = arr[0, 0] if abs(Tg[m].mean() - arr[0, 0]) < abs(Tg[m].mean() - arr[-1, 0]) else arr[-1, 0]
        dE0 = np.interp(t_seam, arr[:, 0], arr[:, 2]) - diamond(r, t_seam)[1]
    else:
        dE0 = 0.0
    for j in np.where(m)[0]:
        pD, eD = diamond(r, Tg[j])
        P[i, j] = pD
        E[i, j] = eD + dE0
assert np.isfinite(P).all() and np.isfinite(E).all()

# ---- 3. EOS-tools 写总表 + 拆分 (复用原管线) ----
ds = EOSDataset(rho_gcc=rhos, temp_ev=Tg,
                ion_pressure_mpa=P * 1e5, electron_pressure_mpa=P * 1e5,
                ion_energy_jpg=E * NA_EV_TO_JPG / A, electron_energy_jpg=E * NA_EV_TO_JPG / A,
                mean_ionization=np.zeros((nr, nt)),
                metadata=EOSMetadata(source_format="liuxing-sheet1-corrected",
                                     atom_a=A, atom_z=1))
tmp = f"{BACKUP}/tmp"; os.makedirs(tmp, exist_ok=True)
outs = multi_fmt.save(ds, output_prefix=f"{tmp}/out", energy_points=128,
                      adaptive_energy_grid=True, write_opacity=False)
total = f"{BACKUP}/C_wk_eos_total"
import shutil; shutil.copy(outs["electron"], total)
os.makedirs(f"{MULTI}/r94/mat_C_wk-1.0", exist_ok=True)
shutil.copy(total, f"{MULTI}/r94/mat_C_wk-1.0/C_wk_eos")

# 备份旧表 → 替换
os.makedirs(f"{BACKUP}/backup_old", exist_ok=True)
for f in ["C_wk_eos_e", "C_wk_eos_i"]:
    dst = f"{TABLES}/{f}"
    if os.path.exists(dst):
        shutil.copy(dst, f"{BACKUP}/backup_old/{f}_broken_20260811")
make_1d_eos(total, A, f"{TABLES}/C_wk_eos_e", f"{TABLES}/C_wk_eos_i", 6000304, 6000305)
# ---- 4. 电子表保序后处理: P_e(de) 逐列累积最大 (递减段压平;
#      递减使隐式辐射-电子解多根 → 边界单元密度极限环, 2026-08-25) ----
from split_ieos_table import read_ieos, write_ieos
_e = f"{TABLES}/C_wk_eos_e"
fid, r2, de2, e02, pe, te = read_ieos(_e)
ne2, nr2 = len(de2), len(r2)
PE = np.array(pe).reshape(ne2, nr2)
nfix = sum(1 for i in range(nr2) if not np.all(np.diff(PE[:, i]) >= -1e-9))
PE = np.maximum.accumulate(PE, axis=0)
write_ieos(_e, fid, r2, de2, e02, PE.ravel(), te)
print(f"电子表保序: 修正 {nfix}/{nr2} 列")
print("rebuilt tables/C_wk_eos_e + _eos_i (旧表备份 work/cwk_rebuild_20260825/backup_old/)")
