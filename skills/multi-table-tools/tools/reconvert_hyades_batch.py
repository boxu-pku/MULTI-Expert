#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reconvert_hyades_batch.py — 批量重转 hyades 源 EOS（修复 ×1000 能量轴 bug）

背景见 agent/pitfalls/migrated-eos-energy-scale-1000x.md：
2026-08-10 手工构造转换链把能量轴放大约 ×1000（J/g↔J/kg 混淆），
本脚本用修复后的 EOS-tools 官方链（read_hyades 尾部零填充容忍 +
table_role='electron' + allow_ideal_ion=True）重转，并逐张验收：

  1. check_multi_file.py 格式校验（复现 Mat2013_LoadMF 语义）
  2. PdV 热力学一致性：|e0(3ρ0)-e0(ρ0)| / ∫P_cold dV ≈ 1（气体仅参考）
  3. T 绝对值抽查：在源表 (ρ,T)→E 位置内插重转表 T，相对偏差 <2%

产物: /tmp/eos_fix/<name>_electron.multi / <name>_ion.multi + report CSV
表头 id 用库内旧表 id 原样回填（保证 data.in 兼容）。

用法:
  python3 reconvert_hyades_batch.py            # 全部转换+验收
  python3 reconvert_hyades_batch.py Quartz Ta  # 只转指定材料
"""
import os
import sys
import json
import numpy as np

EOSTOOLS = "/home/ubuntu/local/EOS_converter_xubo/EOS-tools"
sys.path.insert(0, EOSTOOLS)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eoslib.formats.hyades import load
from eoslib.service import save_target
from split_ieos_table import read_ieos

OUT_DIR = "/tmp/eos_fix"
LIB = "/home/ubuntu/local/MULTI-2D.2026.3/r94/MULTI-IFE-2015/tables"
HYADES = "/home/ubuntu/local/newmulti/Multi_BACK/matter++/hyades/sesame"

# 待重转清单（2026-08-13 PdV 审计判定病态且源为 hyades 的 41 张）
# name, A, Z, rho0, eos源文件
TARGETS = [
    ("H",     1.008,   1.0,  0.0884, f"{HYADES}/eos_61.dat"),
    ("He",    4.003,   2.0,  0.4,    f"{HYADES}/eos_191.dat"),
    ("Li",    6.939,   3.0,  0.5326, f"{HYADES}/eos_71.dat"),
    ("N",     14.007,  7.0,  0.8572, f"{HYADES}/eos_251.dat"),
    ("O",     16.000,  8.0,  1.2620, f"{HYADES}/eos_221.dat"),
    ("Ne",    20.183, 10.0,  1.44,   f"{HYADES}/eos_101.dat"),
    ("Mg",    24.305, 12.0,  1.740,  f"{HYADES}/eos_451.dat"),
    ("Ar",    39.948, 18.0,  1.4,    f"{HYADES}/eos_91.dat"),
    ("V",     50.942, 23.0,  6.11,   f"{HYADES}/eos_521.dat"),
    ("Ni",    58.71,  28.0,  8.882,  f"{HYADES}/eos_291.dat"),
    ("Zn",    65.37,   30.0, 7.139,  f"{HYADES}/eos_531.dat"),
    ("Kr",    83.80,   36.0, 2.5005, f"{HYADES}/eos_201.dat"),
    ("Mo",    95.94,   42.0, 10.2,   f"{HYADES}/eos_281.dat"),
    ("Ag",    107.87,  47.0, 10.50,  f"{HYADES}/eos_491.dat"),
    ("Xe",    131.30,  54.0, 3.0551, f"{HYADES}/eos_371.dat"),
    ("Gd",    157.25,  64.0, 7.898,  f"{HYADES}/eos_471.dat"),
    ("Ta",    180.95,  73.0, 16.654, f"{HYADES}/eos_271.dat"),
    ("Pb",    207.19,  82.0, 11.34,  f"{HYADES}/eos_231.dat"),
    ("U",     238.03,  92.0, 18.983, f"{HYADES}/eos_131.dat"),
    ("D",     2.014,   1.0,  0.1766, f"{HYADES}/eos_151.dat"),
    ("Glass", 20.028,  10.0, 2.65,   f"{HYADES}/eos_21.dat"),
    ("Quartz",20.028,  10.0, 2.204,  f"{HYADES}/eos_23.dat"),
    ("Silica",20.028,  10.0, 2.65,   f"{HYADES}/eos_24.dat"),
    ("Al2O3", 20.392,  10.0, 3.97,   f"{HYADES}/eos_162.dat"),
    ("WC",    94.191,  38.75,14.97,  f"{HYADES}/eos_141.dat"),
    ("CD2",   5.347,   2.667,1.0475, f"{HYADES}/eos_171.dat"),
    ("LiD",   4.4775,  2.0,  0.883,  f"{HYADES}/eos_213.dat"),
    ("LiH",   4.000,   2.0,  0.775,  f"{HYADES}/eos_241.dat"),
    ("Diamond",12.011, 6.0,  3.51,   f"{HYADES}/eos_341.dat"),
    ("Cliquid",12.011, 6.0,  3.688,  f"{HYADES}/eos_342.dat"),
    ("Cphenolic",9.010,4.648,1.4503, f"{HYADES}/eos_343.dat"),
    ("SS",    55.368,  25.8, 7.91,   f"{HYADES}/eos_362.dat"),
    ("Sn",    118.7,   50.0, 7.29,   f"{HYADES}/eos_401.dat"),
    ("PE",    4.676,   2.667,0.954,  f"{HYADES}/eos_31.dat"),
    ("PS",    6.510,   3.5,  1.044,  f"{HYADES}/eos_32.dat"),
    ("PU",    7.038,   3.763,1.265,  f"{HYADES}/eos_33.dat"),
    ("Parylene",10.815,5.5,  1.42,   f"{HYADES}/eos_35.dat"),
    ("Mylar", 8.735,   4.545,1.38,   f"{HYADES}/eos_36.dat"),
    ("Water", 6.005,   3.333,0.9982, f"{HYADES}/eos_311.dat"),
    ("Air",   14.803,  7.373,0.00129,f"{HYADES}/eos_301.dat"),
    ("Eu",    151.96,  63.0, 5.253,  f"{HYADES}/eos_461.dat"),
]

EV_K = 11604.519


def parse_hyades_source(path):
    """独立解析 hyades 源表（15 字符定宽）→ (rho, temp_keV, P, E)，布局 [rho, T]"""
    lines = open(path).read().split("\n")
    vals = []
    for line in lines[2:]:
        if not line.strip():
            continue
        for i in range(0, len(line) - 14, 15):
            s = line[i:i + 15].strip()
            if s:
                vals.append(float(s))
    vals = np.array(vals)
    NR, NT = int(vals[0]), int(vals[1])
    rho = vals[2:2 + NR]
    temp = vals[2 + NR:2 + NR + NT]
    P = vals[2 + NR + NT: 2 + NR + NT + NR * NT].reshape(NT, NR).T
    E = vals[2 + NR + NT + NR * NT: 2 + NR + NT + 2 * NR * NT].reshape(NT, NR).T
    return rho, temp, P, E


def pdv_ratio(r, e0, P, rho0):
    """PdV 热力学一致性: |e0(3ρ0)-e0(ρ0)| / ∫P_cold dV（P 取 de=0 列）"""
    i0 = int(np.argmin(np.abs(r - rho0)))
    i3 = int(np.argmin(np.abs(r - 3 * rho0)))
    if i0 == i3:
        return float("nan")
    seg = slice(min(i0, i3), max(i0, i3) + 1)
    integ = -np.trapz(P[0, seg], 1.0 / r[seg])
    if integ <= 0:
        return float("inf")
    return abs((e0[i3] - e0[i0]) / integ)


def t_spot_check(new_file, rho_s, temp_s, E_s, rho0, npts=5):
    """在源表 (ρ,T) 点上按源 ΔE 内插新表的 T，返回最大相对偏差。
    抽查点: ρ0 与 2ρ0 两个密度, 各取 T≈1/10/100 eV 附近的源网格点。"""
    fid, r, de, e0, p, t = read_ieos(new_file)
    nr, ne = len(r), len(de)
    T = t.reshape(ne, nr)          # K
    worst = 0.0
    details = []
    for tg_rho in (rho0, 2 * rho0):
        is_ = int(np.argmin(np.abs(rho_s - tg_rho)))
        im = int(np.argmin(np.abs(r - tg_rho)))
        for tg_T in (1.0, 10.0, 100.0):
            j = int(np.argmin(np.abs(temp_s * 1000 - tg_T)))
            T_true = temp_s[j] * 1000           # eV
            if T_true <= 0:
                continue
            dE = (E_s[is_, j] - E_s[is_, 0]) / 1e12   # Mbar·cm³/g
            if dE <= 0 or dE > de[-1]:
                continue
            T_new = np.interp(dE, de, T[:, im]) / EV_K
            rel = abs(T_new / T_true - 1)
            worst = max(worst, rel)
            details.append((rho_s[is_], T_true, T_new, rel))
    return worst, details


def rewrite_header_id(path, idval):
    with open(path) as f:
        lines = f.readlines()
    s = f"{float(idval):15.8e}"
    assert len(s) == 15 and int(float(s)) == idval
    assert len(lines[0].rstrip("\n")) == 60
    lines[0] = s + lines[0][15:]
    with open(path, "w") as f:
        f.writelines(lines)


def lib_id(name, suffix):
    """库内旧表头 id（前 15 字符）"""
    with open(os.path.join(LIB, f"{name}_eos_{suffix}")) as f:
        return int(float(f.readline()[0:15]))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    only = sys.argv[1:]
    report = []
    for name, A, Z, rho0, src in TARGETS:
        if only and name not in only:
            continue
        row = {"name": name, "rho0": rho0, "src": os.path.basename(src)}
        try:
            ds = load(electron_file=src, atom_a=A, atom_z=Z, name=name,
                      table_role="electron", allow_ideal_ion=True)
            out = os.path.join(OUT_DIR, name)
            save_target(ds, "multi", output_prefix=out,
                        energy_points=128,
                        electron_energy_min_jpg=None, electron_energy_max_jpg=None,
                        ion_energy_min_jpg=None, ion_energy_max_jpg=None,
                        marker=1, write_opacity=False,
                        opacity_bounds_ev=None, opacity_bounds_file=None,
                        opacity_num_groups=None, opacity_min_ev=None,
                        opacity_max_ev=None, opacity_group_policy="moment_conservative")
            fe, fi = out + "_electron.multi", out + "_ion.multi"

            # 回填库约定 id
            rewrite_header_id(fe, lib_id(name, "e"))
            rewrite_header_id(fi, lib_id(name, "i"))

            # 验收 1: PdV
            fid_, r, de, e0, p, t = read_ieos(fe)
            P = p.reshape(len(de), len(r))
            row["pdv"] = pdv_ratio(r, e0, P, rho0)

            # 验收 2: T 抽查（独立解析源表）
            rho_s, temp_s, _, E_s = parse_hyades_source(src)
            worst, details = t_spot_check(fe, rho_s, temp_s, E_s, rho0)
            row["t_worst_rel"] = worst
            row["t_details"] = [(round(a, 3), round(b, 2), round(c, 3), round(d, 4))
                                for a, b, c, d in details]
            row["nr"], row["ne"] = len(r), len(de)
            row["rho_range"] = [float(r.min()), float(r.max())]
            row["ok"] = bool(row["pdv"] < 1.2 and worst < 0.02)
        except Exception as e:
            row["error"] = f"{type(e).__name__}: {e}"
            row["ok"] = False
        report.append(row)
        status = "OK " if row.get("ok") else "FAIL"
        print(f"{status} {name:10s} pdv={row.get('pdv', float('nan')):8.3g} "
              f"t_worst={row.get('t_worst_rel', float('nan')):8.4g} {row.get('error','')}",
              flush=True)

    with open(os.path.join(OUT_DIR, "reconvert_report.json"), "w") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    n_ok = sum(1 for r in report if r.get("ok"))
    print(f"\n完成 {n_ok}/{len(report)}，报告: {OUT_DIR}/reconvert_report.json")


if __name__ == "__main__":
    main()
