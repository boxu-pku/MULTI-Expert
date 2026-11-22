#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_opc_batch.py — 为 EOS-only 材料配 hyades opc 单群平均不透明度

按 Multi_BACK material.base 的原生映射(含借用规则):
  SiO2 族→1022, 聚合物→各自, Al2O3→1161, WC→1121(W), 碳族→1344(C),
  LiD/LiH→1071(Li), SS→1181(Fe), Water→1311, Air→1301, Sn→1401, Eu→1461

对每种材料:
  1. opc → tables/X_OPC.ROSS / X_OPC.PLANCK (sgo 单群表)
  2. check_multi_file 验证
  3. 生成 1D 验证算例 validation_cases/XCheck/
  4. 拟合 Rosseland 平均自由程(供 2D opafun), 输出到 stdout 供登记
"""
import os
import sys
import subprocess
import numpy as np

sys.path.insert(0, "/home/ubuntu/local/MULTI-2D.2026.3/work/eos_opacity_tools")
from opc2sgo import read_opc, write_sgo
from migrate_manifest import BATCH_EOS_ONLY
from batch_migrate import make_case, elem_ids

MULTI = "/home/ubuntu/local/MULTI-2D.2026.3"
TABLES = f"{MULTI}/r94/MULTI-IFE-2015/tables"
OPC = "/home/ubuntu/local/newmulti/Multi_BACK/matter++/hyades/Opacity"

# name → (opc表号, 借用说明)
OPC_MAP = {
    "Glass": (1022, "SiO2族"), "Quartz": (1022, "SiO2族"), "Silica": (1022, "SiO2族"),
    "PE": (1031, ""), "PS": (1032, ""), "PU": (1033, ""),
    "Parylene": (1035, ""), "Mylar": (1036, ""),
    "Al2O3": (1161, ""),
    "WC": (1121, "借W表"),
    "CD2": (1344, "借C表"), "Diamond": (1344, "借C表"),
    "Cliquid": (1344, "借C表"), "Cphenolic": (1344, "借C表"),
    "LiD": (1071, "借Li表"), "LiH": (1071, "借Li表"),
    "SS": (1181, "借Fe表"),
    "Water": (1311, ""), "Air": (1301, ""),
    "Sn": (1401, ""), "Eu": (1461, ""),
}


def fit_freepath(rho, T_keV, ross):
    """对 Rosseland 平均表拟合 log10 λ = a + s·log10 T + r·log10 ρ (λ=1/(κρ))"""
    NR, NT = len(rho), len(T_keV)
    LR, LT = np.meshgrid(np.log10(rho), np.log10(T_keV * 1e3))  # (NT,NR)
    lam = 1.0 / (ross.reshape(NT, NR) * rho[None, :])
    mask = np.isfinite(lam) & (lam > 0)
    X = np.column_stack([np.ones(mask.sum()), LT[mask], LR[mask]])
    y = np.log10(lam[mask])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ coef
    return coef[0], coef[1], coef[2], res.std()


def main():
    manifest = {m[0]: m for m in BATCH_EOS_ONLY}
    results = {}
    fits = {}
    for name, (opcno, borrow) in OPC_MAP.items():
        A, Z, rho0 = manifest[name][1], manifest[name][2], manifest[name][3]
        src = f"{OPC}/opc_{opcno}.dat"
        rho, T, ross, plan = read_opc(src)
        r_out, p_out = f"{TABLES}/{name}_OPC.ROSS", f"{TABLES}/{name}_OPC.PLANCK"
        write_sgo(r_out, opcno, " 0.40000000E+01", rho, T, ross)
        write_sgo(p_out, opcno, " 0.70000000E+01", rho, T, plan)
        res = subprocess.run(["python3", f"{MULTI}/work/eos_opacity_tools/check_multi_file.py",
                              r_out, p_out], capture_output=True, text=True)
        ok = res.returncode == 0
        e_id, i_id = elem_ids(Z)
        make_case(name, A, Z, rho0, e_id, i_id, -1, None, opcno, f"{name}_OPC.PLANCK",
                  opcno, f"{name}_OPC.ROSS")
        a, s, r, rms = fit_freepath(rho, T, ross)
        fits[name] = (a, s, r, rms)
        print(f"{name:10s} opc_{opcno} ({borrow:6s}) 格式={'PASS' if ok else 'FAIL'} "
              f"拟合: λ=10^{a:.2f}·T^{s:.2f}·ρ^{r:.2f} rms={rms:.2f}")
        results[name] = ok
    npass = sum(results.values())
    print(f"\n通过 {npass}/{len(results)}")
    # 输出拟合参数(供 Material_mig.r)
    with open("/tmp/opc_fits.txt", "w") as f:
        for name, (a, s, r, rms) in fits.items():
            f.write(f"{name} {a:.4f} {s:.4f} {r:.4f} {rms:.3f}\n")


if __name__ == "__main__":
    main()
