#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_table_hugoniot.py — 由 MULTI 1D 的 eeos+ieos 表反解主 Hugoniot 线

对无外部理论线的材料(如熔石英 Quartz), 用表本身解 Rankine-Hugoniot 能量方程:
    E(ρ1,T) − E0 = ½·(P(ρ1,T)+P0)·(1/ρ0 − 1/ρ1)
得到 (ρ1, T, P, Us, Up) 参考线。这是**自洽性参考**(验证冲击物理实现与表插值
一致性), 不是独立理论验证 —— 图注中必须标明。

表语义(split_ieos_table.read_ieos): 返回 (id, r, de, e0, p, t)
  - 比能坐标 E = e0[i] + de[j]  (Mbar·cc/g), 能量主序 p[j*NR+i]
  - 单位: ρ g/cc, E Mbar·cc/g (=1e12 erg/g), P Mbar, T K
  - 总平衡 EOS = 电子表 + 离子表 (LTE: Te=Ti=T)

用法: python3 compute_table_hugoniot.py <eeos文件> <ieos文件> <rho0> <T0_eV> <eta_max>
输出 CSV 到 stdout 重定向或 -o 指定。
"""
import sys
import numpy as np
from scipy.optimize import brentq

sys.path.insert(0, "/home/ubuntu/local/MULTI-2D.2026.3/work/eos_opacity_tools")
from split_ieos_table import read_ieos

K_EV_PER_K = 1.0 / 11604.519   # K → eV


class IEOSEval:
    """(ρ,T) → (P, E) 求值器: 先按行反演 T→de, 再按 log ρ 插值"""

    def __init__(self, path):
        _id, r, de, e0, p, t = read_ieos(path)
        self.r = np.asarray(r, dtype=float)
        self.de = np.asarray(de, dtype=float)
        self.e0 = np.asarray(e0, dtype=float)
        nr, ne = len(self.r), len(self.de)
        # 能量主序: p[j*nr+i] → 矩阵 (ne, nr)
        self.P = np.asarray(p, dtype=float).reshape(ne, nr)
        self.T = np.asarray(t, dtype=float).reshape(ne, nr)   # K
        self.nr, self.ne = nr, ne

    def row_invert(self, i, T_K):
        """第 i 行: 给定 T(K) 反演 de 并取 P。T 非单调段取首个穿越点。"""
        trow = self.T[:, i]
        # 去非单调(取累积最大, 重复点视为同平台)
        ok = trow > 0
        if ok.sum() < 2:
            return np.nan, np.nan
        de_r, t_r, p_r = self.de[ok], trow[ok], self.P[ok, i]
        if T_K < t_r[0]:
            j = 0
        elif T_K >= t_r[-1]:
            j = len(t_r) - 2
        else:
            j = int(np.searchsorted(t_r, T_K) - 1)
            j = max(0, min(j, len(t_r) - 2))
        t0, t1 = t_r[j], t_r[j + 1]
        w = 0.0 if t1 == t0 else (T_K - t0) / (t1 - t0)
        return p_r[j] + w * (p_r[j + 1] - p_r[j]), de_r[j] + w * (de_r[j + 1] - de_r[j])

    def __call__(self, rho, T_K):
        """双变量插值: 行间 log ρ 线性; 返回 (P[Mbar], E[Mbar·cc/g])"""
        r_pos = np.maximum(self.r, 1e-300)
        lr = np.log(r_pos)
        x = np.log(rho)
        if x <= lr[0]:
            i0, i1, w = 0, 1, 0.0
        elif x >= lr[-1]:
            i0, i1, w = self.nr - 2, self.nr - 1, 1.0
        else:
            i1 = int(np.searchsorted(lr, x))
            i0 = i1 - 1
            w = (x - lr[i0]) / (lr[i1] - lr[i0])
        p_a, de_a = self.row_invert(i0, T_K)
        p_b, de_b = self.row_invert(i1, T_K)
        p = p_a + w * (p_b - p_a)
        # e0 也按行插值; E = e0(ρ) + de(ρ,T)
        e0 = self.e0[i0] + w * (self.e0[i1] - self.e0[i0])
        E = e0 + de_a + w * (de_b - de_a)
        return p, E


def solve_hugoniot(eeos_file, ieos_file, rho0, T0_eV, eta_max=4.5, n_eta=60):
    """返回 dict(rho1, T_eV, P_Mbar, Us_kms, Up_kms)"""
    ele = IEOSEval(eeos_file)
    ion = IEOSEval(ieos_file)
    T0 = T0_eV / K_EV_PER_K                    # eV → K
    P0 = ele(rho0, T0)[0] + ion(rho0, T0)[0]
    E0 = ele(rho0, T0)[1] + ion(rho0, T0)[1]
    V0 = 1.0 / rho0

    def totals(rho, T_K):
        pe, ee = ele(rho, T_K)
        pi, ei = ion(rho, T_K)
        return pe + pi, ee + ei

    Tmax = ele.T.max()
    out = {k: [] for k in ("rho1", "T_eV", "P_Mbar", "Us_kms", "Up_kms")}
    for eta in np.linspace(1.005, eta_max, n_eta):
        rho1 = rho0 * eta
        V1 = 1.0 / rho1

        def f(T_K):
            P1, E1 = totals(rho1, T_K)
            return (E1 - E0) - 0.5 * (P1 + P0) * (V0 - V1)

        # T 扫描找变号区间
        Ts = np.geomspace(T0, Tmax, 400)
        fs = [f(tk) for tk in Ts]
        sol = None
        for j in range(len(Ts) - 1):
            if np.isfinite(fs[j]) and np.isfinite(fs[j + 1]) and fs[j] * fs[j + 1] < 0:
                sol = brentq(f, Ts[j], Ts[j + 1], xtol=1e-3)
                break
        if sol is None:
            continue
        P1, E1 = totals(rho1, sol)
        dP = P1 - P0                                  # Mbar
        # Us = sqrt(dP/(ρ0(1−ρ0/ρ1))); Mbar→dyn/cm2 乘 1e12; cm/s→km/s 除 1e5
        Us = np.sqrt(dP * 1e12 / (rho0 * (1.0 - rho0 / rho1))) / 1e5
        Up = Us * (1.0 - rho0 / rho1)
        out["rho1"].append(rho1)
        out["T_eV"].append(sol * K_EV_PER_K)
        out["P_Mbar"].append(P1)
        out["Us_kms"].append(Us)
        out["Up_kms"].append(Up)
    return {k: np.array(v) for k, v in out.items()}


def main():
    eeos_f, ieos_f = sys.argv[1], sys.argv[2]
    rho0 = float(sys.argv[3])
    T0_eV = float(sys.argv[4]) if len(sys.argv) > 4 else 0.1
    eta_max = float(sys.argv[5]) if len(sys.argv) > 5 else 4.5
    res = solve_hugoniot(eeos_f, ieos_f, rho0, T0_eV, eta_max)
    print("rho1_gcc,T_eV,P_Mbar,Us_kms,Up_kms")
    for i in range(len(res["rho1"])):
        print(f"{res['rho1'][i]:.6e},{res['T_eV'][i]:.6e},{res['P_Mbar'][i]:.6e},"
              f"{res['Us_kms'][i]:.6e},{res['Up_kms'][i]:.6e}")


if __name__ == "__main__":
    main()
