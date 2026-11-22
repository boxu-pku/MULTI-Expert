#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_eos_2d1d.py — 2D 侧 EOS 重建 + 1D eeos 约定修正

背景见 agent/pitfalls/migrated-eos-energy-scale-1000x.md：
  1. ×1000 能量轴 bug 在 2D 侧（r94/mat_<X>-1.0/<X>_eos 总表）从未被修复 —— 仍病态。
  2. reconvert 把 hyades **总量**写进了 1D 电子槽（electron-slot carries raw total），
     而原始迁移走 split_ieos_table 产出 total−ion。当前 tables/<X>_eos_e = 总量（非
     total−ion），对 H/D 使 1D Te 偏低约 2×。

权威源：work/eos_rebuild_20260813/<X>_electron.multi（= /tmp/eos_fix 持久化副本，
修正尺度的 hyades 总量；含 H/D/Parylene 折叠裁断）。该文件经 reconvert_hyades_batch.py
验证（PdV≈1、T 抽查通过、Check 通过）。

本脚本对 41 张表统一处理（单一源头 → 双侧一致）：
  Phase 1（2D 总表）: <X>_electron.multi → mat_<X>-1.0/<X>_eos，marker=1.0
  Phase 2（1D 拆分）: split(2D总表) → tables/<X>_eos_e (=total−ion) + tables/<X>_eos_i (理想离子)
                     id 沿用 elem_ids(Z)，保证 data.in 兼容

用法:
  python3 rebuild_eos_2d1d.py            # 全部 41
  python3 rebuild_eos_2d1d.py Quartz Ta  # 指定
  python3 rebuild_eos_2d1d.py --dry-run  # 只打印不写
"""
import os
import sys
import glob
import shutil
import datetime
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from split_ieos_table import (read_ieos, write_ieos, split_electron,
                              make_ion_ideal, EV_K, E12, BOLTZMANN, ATOMICMASS)

MULTI = "/home/ubuntu/local/MULTI-2D.2026.3"
SRC_DIR = f"{MULTI}/work/eos_rebuild_20260813"
TABLES = f"{MULTI}/r94/MULTI-IFE-2015/tables"
BAK_1D = f"{TABLES}/_bak_totalconv_20260813"
DATE_TAG = "20260813"

# 41 病态材料（与 reconvert_hyades_batch.py::TARGETS 同源）
# name, A, Z, rho0
TARGETS = [
    ("H", 1.008, 1.0, 0.0884), ("He", 4.003, 2.0, 0.4),
    ("Li", 6.939, 3.0, 0.5326), ("N", 14.007, 7.0, 0.8572),
    ("O", 16.000, 8.0, 1.2620), ("Ne", 20.183, 10.0, 1.44),
    ("Mg", 24.305, 12.0, 1.740), ("Ar", 39.948, 18.0, 1.4),
    ("V", 50.942, 23.0, 6.11), ("Ni", 58.71, 28.0, 8.882),
    ("Zn", 65.37, 30.0, 7.139), ("Kr", 83.80, 36.0, 2.5005),
    ("Mo", 95.94, 42.0, 10.2), ("Ag", 107.87, 47.0, 10.50),
    ("Xe", 131.30, 54.0, 3.0551), ("Gd", 157.25, 64.0, 7.898),
    ("Ta", 180.95, 73.0, 16.654), ("Pb", 207.19, 82.0, 11.34),
    ("U", 238.03, 92.0, 18.983), ("D", 2.014, 1.0, 0.1766),
    ("Glass", 20.028, 10.0, 2.65), ("Quartz", 20.028, 10.0, 2.204),
    ("Silica", 20.028, 10.0, 2.65), ("Al2O3", 20.392, 10.0, 3.97),
    ("WC", 94.191, 38.75, 14.97), ("CD2", 5.347, 2.667, 1.0475),
    ("LiD", 4.4775, 2.0, 0.883), ("LiH", 4.000, 2.0, 0.775),
    ("Diamond", 12.011, 6.0, 3.51), ("Cliquid", 12.011, 6.0, 3.688),
    ("Cphenolic", 9.010, 4.648, 1.4503), ("SS", 55.368, 25.8, 7.91),
    ("Sn", 118.7, 50.0, 7.29), ("PE", 4.676, 2.667, 0.954),
    ("PS", 6.510, 3.5, 1.044), ("PU", 7.038, 3.763, 1.265),
    ("Parylene", 10.815, 5.5, 1.42), ("Mylar", 8.735, 4.545, 1.38),
    ("Water", 6.005, 3.333, 0.9982), ("Air", 14.803, 7.373, 0.00129),
    ("Eu", 151.96, 63.0, 5.253),
]


def elem_ids(Z):
    """电子/离子表 id（与 batch_migrate 一致：整数 Z→Z*1e6+304/305；分数 Z→round(Z*100)*1e4）"""
    if abs(Z - round(Z)) < 1e-6:
        return int(round(Z)) * 1000000 + 304, int(round(Z)) * 1000000 + 305
    return int(round(Z * 100)) * 10000 + 304, int(round(Z * 100)) * 10000 + 305


def pdv_ratio(r, e0, P, rho0):
    """PdV 热力学一致性: |e0(3ρ0)-e0(ρ0)| / ∫P_cold dV"""
    i0 = int(np.argmin(np.abs(r - rho0)))
    i3 = int(np.argmin(np.abs(r - 3 * rho0)))
    if i0 == i3:
        return float("nan")
    seg = slice(min(i0, i3), max(i0, i3) + 1)
    integ = -np.trapz(P[0, seg], 1.0 / r[seg])
    if integ <= 0 or not np.isfinite(integ):
        return float("nan")
    return abs((e0[i3] - e0[i0]) / integ)


def rewrite_marker(path, marker):
    """改写 IEOS 文件头行前 15 字符（marker/id），保持长度 60"""
    with open(path) as f:
        lines = f.readlines()
    assert len(lines[0].rstrip("\n")) == 60, f"头行非 60 字符: {path}"
    s = f"{float(marker):15.8e}"
    assert len(s) == 15
    lines[0] = s + lines[0][15:]
    with open(path, "w") as f:
        f.writelines(lines)


def find_total_eos(name):
    """定位 mat_<name>-1.0 下的总 EOS 文件（标准名 <name>_eos，回退到 *_eos glob）"""
    matdir = f"{MULTI}/r94/mat_{name}-1.0"
    cand = f"{matdir}/{name}_eos"
    if os.path.isfile(cand):
        return cand
    hits = [p for p in glob.glob(f"{matdir}/*_eos") if os.path.isfile(p)]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        # 容错：部分目录可能用大写或别名
        hits = [p for p in glob.glob(f"{matdir}/*")
                if os.path.isfile(p) and not os.path.basename(p).endswith(("MODINFO", "README", "FILELIST", "LOCK"))]
        if len(hits) == 1:
            return hits[0]
    raise FileNotFoundError(f"无法定位 {name} 的总 EOS 文件于 {matdir}")


def check_multi(path):
    """跑 check_multi_file.py，返回 (ok, tail)"""
    import subprocess
    r = subprocess.run(["python3", f"{HERE}/check_multi_file.py", path],
                       capture_output=True, text=True)
    return r.returncode == 0, (r.stdout[-400:] + r.stderr[-200:])


def process(name, A, Z, rho0, dry):
    row = {"name": name}
    total_src = f"{SRC_DIR}/{name}_electron.multi"
    if not os.path.isfile(total_src):
        raise FileNotFoundError(f"权威源缺失: {total_src}")

    e_id, i_id = elem_ids(Z)
    total_dst = find_total_eos(name)
    e_out = f"{TABLES}/{name}_eos_e"
    i_out = f"{TABLES}/{name}_eos_i"

    # ---------- Phase 1: 2D 总表 ----------
    bak2d = os.path.join(os.path.dirname(total_dst), "_bak_x1000")
    if not dry:
        os.makedirs(bak2d, exist_ok=True)
        if not os.path.exists(f"{bak2d}/{name}_eos"):
            shutil.copy2(total_dst, f"{bak2d}/{name}_eos")
        shutil.copy2(total_src, total_dst)
        rewrite_marker(total_dst, 1.0)
    row["2d_total"] = total_dst

    # 读总表（用于 Phase 2 拆分）
    fid, r, de, e0, p_f, t_f = read_ieos(total_dst)
    nr, ne = len(r), len(de)
    row["nr"], row["ne"] = nr, ne
    row["rho_range"] = [float(r.min()), float(r.max())]

    # ---------- Phase 2: 1D 拆分（e = total−ion, i = 理想离子）----------
    if not dry:
        os.makedirs(BAK_1D, exist_ok=True)
        for old in (e_out, i_out):
            if os.path.exists(old) and not os.path.exists(f"{BAK_1D}/{os.path.basename(old)}"):
                shutil.copy2(old, f"{BAK_1D}/{os.path.basename(old)}")

    de_c, e0_c = de * E12, e0 * E12
    p_c, t_c = p_f * E12, t_f / EV_K
    p_e, t_e = split_electron(r, de_c, p_c, t_c, A)
    e0_i, p_i, t_i = make_ion_ideal(r, de_c, A)
    if not dry:
        write_ieos(e_out, e_id, r, de_c / E12, e0_c / E12, p_e / E12, t_e * EV_K)
        write_ieos(i_out, i_id, r, de_c / E12, e0_i / E12, p_i / E12, t_i * EV_K)

    # ---------- 验证 ----------
    if not dry:
        ok2d, msg2d = check_multi(total_dst)
        oke, msge = check_multi(e_out)
        oki, msgi = check_multi(i_out)
    else:
        ok2d = oke = oki = True
        msg2d = msge = msgi = ""
    P_e = p_e.reshape(ne, nr)
    row["pdv_e"] = pdv_ratio(r, e0_c / E12, P_e / E12, rho0)  # e0 文件单位
    # 注：pdv_ratio 内部对 P 取 de=0 列；电子表冷压 ≈ 总冷压（离子冷压≈0）
    row["check_2d"] = ok2d
    row["check_e"] = oke
    row["check_i"] = oki
    row["ok"] = bool(ok2d and oke and oki)
    row["ids"] = {"e": e_id, "i": i_id}
    if not (ok2d and oke and oki):
        row["msg"] = (msg2d + msge + msgi)[-300:]
    return row


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    sel = args
    rows = []
    for name, A, Z, rho0 in TARGETS:
        if sel and name not in sel:
            continue
        try:
            row = process(name, A, Z, rho0, dry)
            st = "OK " if row["ok"] else "FAIL"
            print(f"{st} {name:11s} NR={row.get('nr')} NE={row.get('ne')} "
                  f"pdv_e={row.get('pdv_e', float('nan')):6.3g} "
                  f"chk[2d/e/i]={row['check_2d']}/{row['check_e']}/{row['check_i']}"
                  + (f"  {row.get('msg','')[-120:]}" if not row["ok"] else ""),
                  flush=True)
        except Exception as e:
            print(f"ERR  {name:11s} {type(e).__name__}: {e}", flush=True)
            rows.append({"name": name, "ok": False, "error": str(e)})
            continue
        rows.append(row)

    import json
    rep = f"{SRC_DIR}/rebuild_2d1d_report.json"
    if not dry:
        with open(rep, "w") as f:
            json.dump(rows, f, indent=1, ensure_ascii=False)
    nok = sum(1 for r in rows if r.get("ok"))
    print(f"\n{'[DRY] ' if dry else ''}完成 {nok}/{len(rows)}，报告: {rep}")


if __name__ == "__main__":
    main()
