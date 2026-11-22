#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weikang_hugoniot.py — 从 WeiKang 源数据(ρ,T,P,E 文本)直接反解主 Hugoniot 线

不解转换后表, 直接读源 txt (避免 C8H8_wk 冷区 P=0 的转换/运行问题)。
能量约定: 源表 E 列为相对能量基点的值 (eV/粒子), 初态取该表最低密度的冷态,
E1-E0 = E_listed (P0≈0); 对每个目标密度行, 在 T 网格上解
    f(T) = E(ρ1,T)·conv − ½·P(ρ1,T)·(1/ρ0 − 1/ρ1) = 0
conv: eV/粒子 → Mbar·cc/g (1e12 erg/g), conv = 1.602e-12·NA/(1000·Ā) / 1e12

用法: python3 weikang_hugoniot.py <源txt> <abar> <rho0>
输出: rho1_gcc,T_eV,P_Mbar,Us_kms,Up_kms (stdout)
"""
import sys
import numpy as np

NA = 6.02214076e23


def load_source(path):
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith("#") or not line.strip() or line[0] == "ρ":
                continue
            p = line.split()
            rows.append((float(p[0]), float(p[1]), float(p[2]), float(p[3])))
    return np.array(rows)          # rho, T[eV], P[Mbar], E[eV/粒子]


def solve(path, abar, rho0, out_path=None):
    d = load_source(path)
    conv = 1.602e-12 * NA / (abar * 1e3) / 1e12     # eV/粒子 → Mbar·cc/g
    out = []
    for rho1 in sorted(np.unique(d[:, 0])):
        if rho1 <= rho0 * 1.01:
            continue
        sub = d[d[:, 0] == rho1]
        sub = sub[np.argsort(sub[:, 1])]
        T, P, E = sub[:, 1], sub[:, 2], sub[:, 3]
        f = E * conv - 0.5 * P * (1.0 / rho0 - 1.0 / rho1)
        sgn = np.sign(f)
        cross = np.where(np.diff(sgn) > 0)[0]       # 由负到正(低压端取首个)
        if not len(cross):
            cross = np.where(np.diff(sgn) != 0)[0]
        if not len(cross):
            continue
        k = cross[0]
        w = f[k] / (f[k] - f[k + 1])
        T1 = T[k] + w * (T[k + 1] - T[k])
        P1 = P[k] + w * (P[k + 1] - P[k])
        Us = np.sqrt(P1 * 1e12 / (rho0 * (1.0 - rho0 / rho1))) / 1e5
        Up = Us * (1.0 - rho0 / rho1)
        out.append((rho1, T1, P1, Us, Up))
    lines = ["rho1_gcc,T_eV,P_Mbar,Us_kms,Up_kms"]
    for r1, t1, p1, us, up in out:
        lines.append(f"{r1:.6e},{t1:.6e},{p1:.6e},{us:.6e},{up:.6e}")
    txt = "\n".join(lines)
    if out_path:
        header = (f"# WeiKang 源数据直接反解: {path.split('/')[-1]}, "
                  f"abar={abar}, rho0={rho0}\n")
        with open(out_path, "w") as f:
            f.write(header + txt + "\n")
    else:
        print(txt)
    return out


if __name__ == "__main__":
    solve(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]),
          sys.argv[4] if len(sys.argv) > 4 else None)
