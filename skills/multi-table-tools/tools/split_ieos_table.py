#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_ieos_table.py — 把 MULTI 总 IEOS 表拆成 电子表 + 离子表

严格复现 r94/matter-3.1/Mat2013_EleTab.r 的算法（1D MULTI-IFE 的
tables/README 中记载的 "substract ideal gas contribution of ions" 流程）：

    P_e(ρ,ΔE) = P_tot(ρ,ΔE) − ρ·cte·T_tot          (减去理想离子压强)
    ΔE_e      = ΔE − 1.5·cte·T_tot  (下限截断为 0)   (减去理想离子能量)
    cte = k_B / (A·m_u)  [erg/(g·eV)]
    再按 ΔE 方向线性插值回原 de 网格（与 C 代码逐点一致）

离子表 = 理想气体表（γ=5/3）:  T = ΔE/(1.5·cte),  P = ρ·ΔE/1.5,  E0 = 0

输入/输出文件均为标准 MULTI IEOS 格式（60 字符头, 15 字符定宽, 每行 4 值）。

用法:
  python3 split_ieos_table.py <总表> <原子量A> <电子输出> <离子输出> [电子id 离子id]

示例:
  python3 split_ieos_table.py Ti_eos 47.867 Ti_eos_e Ti_eos_i 22000304 22000305
"""
import sys
import numpy as np

BOLTZMANN = 1.602176565e-12   # erg/eV (2010 CODATA, 与 Mat2013_EleTab 一致)
ATOMICMASS = 1.660538921e-24  # g
EV_K = 11604.519              # K/eV (与 Mat2013_LoadIEOS 一致)
E12 = 1.0e12                  # 文件能量/压强单位 → cgs


def read_ieos(path):
    """读取单表 IEOS 文件 (15 字符定宽, 每行 4 值, 跨节连续打包)"""
    data = open(path, "rb").read().replace(b"\r\n", b"\n").decode("ascii")
    lines = data.split("\n")
    head = lines[0]
    assert len(head) == 60, f"头行长度 {len(head)} != 60"
    fid = head[0:15].strip()
    nr = int(float(head[30:45]))
    ne = int(float(head[45:60]))
    vals = []
    for line in lines[1:]:
        for i in range(len(line) // 15):
            f = line[15 * i:15 * (i + 1)].strip()
            if f == "-INF":
                vals.append(-40.0)
            elif f == "NAN":
                vals.append(0.0)
            elif f:
                vals.append(float(f))
    need = nr + ne + nr + 2 * nr * ne
    assert len(vals) >= need, f"数据值不足: {len(vals)} < {need}"
    vals = np.array(vals[:need])
    n = 0
    r = vals[n:n + nr]; n += nr
    de = vals[n:n + ne]; n += ne
    e0 = vals[n:n + nr]; n += nr
    p = vals[n:n + nr * ne]; n += nr * ne
    t = vals[n:n + nr * ne]
    return fid, r, de, e0, p, t


def write_ieos(path, fid, r, de, e0, p, t):
    """写标准 MULTI IEOS 文件 (r94/1D Fortran 均可读)"""
    nr, ne = len(r), len(de)
    with open(path, "w") as f:
        f.write(f"{float(fid):15.8e}{0.0:15.8e}{float(nr):15.8e}{float(ne):15.8e}\n")
        vals = np.concatenate([r, de, e0, p, t])
        for i in range(0, len(vals), 4):
            chunk = vals[i:i + 4]
            f.write("".join(f"{v:15.8e}" for v in chunk) + "\n")


def split_electron(r, de, p_tot, t_tot, A):
    """Mat2013_EleTab 算法复刻。输入/输出均为 cgs/eV 单位体系。
    布局: p/t 为 (ne, nr) 即 p[j*nr+i]。"""
    nr, ne = len(r), len(de)
    cte = BOLTZMANN / (ATOMICMASS * A)
    p_e_out = np.zeros(nr * ne)
    t_e_out = np.zeros(nr * ne)
    for i in range(nr):
        rho = r[i]
        tot_P = np.array([p_tot[j * nr + i] for j in range(ne)])
        tot_T = np.array([t_tot[j * nr + i] for j in range(ne)])
        P_e = tot_P - rho * cte * tot_T
        de_e = de - 1.5 * cte * tot_T
        de_e = np.maximum(de_e, 0.0)
        for j in range(ne):
            # 找第一个 de_e[k] >= de[j]
            k = ne
            for kk in range(ne):
                if de_e[kk] >= de[j]:
                    k = kk
                    break
            if k == 0:
                factor = 0.0
                kk = 0
            elif k == ne:
                kk = ne - 2
                denom = de_e[kk + 1] - de_e[kk]
                factor = (de[j] - de_e[kk]) / denom if denom != 0 else 0.0
            else:
                kk = k - 1
                denom = de_e[kk + 1] - de_e[kk]
                factor = (de[j] - de_e[kk]) / denom if denom != 0 else 0.0
            p_e_out[j * nr + i] = P_e[kk] + factor * (P_e[kk + 1] - P_e[kk])
            t_e_out[j * nr + i] = tot_T[kk] + factor * (tot_T[kk + 1] - tot_T[kk])
    return p_e_out, t_e_out


def make_ion_ideal(r, de, A, gamma=5.0 / 3.0):
    """理想气体离子 IEOS 表 (cgs/eV)"""
    nr, ne = len(r), len(de)
    cte = BOLTZMANN / (ATOMICMASS * A)
    p = np.zeros(nr * ne)
    t = np.zeros(nr * ne)
    for j in range(ne):
        for i in range(nr):
            # T = E/(cv), cv = 1/(gamma-1)*cte -> T = (gamma-1)*E/cte
            # 与 Mat2013_GasIEOS.r 一致；2026-09-06 修正乘除颠倒 bug
            # （此前写成 E/((gamma-1)*cte)，T、P 系统性偏大 2.25 倍）
            T = (gamma - 1.0) * de[j] / cte if de[j] > 0 else 0.0
            p[j * nr + i] = r[i] * cte * T
            t[j * nr + i] = T
    e0 = np.zeros(nr)
    return e0, p, t


def main():
    src, A = sys.argv[1], float(sys.argv[2])
    fe, fi = sys.argv[3], sys.argv[4]
    ide = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
    idi = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0

    fid, r, de, e0, p_f, t_f = read_ieos(src)
    nr, ne = len(r), len(de)
    print(f"源表 {src}: id={fid} NR={nr} NE={ne}")

    # 文件单位 → cgs/eV (与 Mat2013_LoadIEOS 相同)
    de_c = de * E12
    e0_c = e0 * E12
    p_c = p_f * E12
    t_c = t_f / EV_K

    # 电子表(减理想离子), 离子表(理想气体)
    p_e, t_e = split_electron(r, de_c, p_c, t_c, A)
    e0_i, p_i, t_i = make_ion_ideal(r, de_c, A)

    # cgs/eV → 文件单位
    write_ieos(fe, ide, r, de_c / E12, e0_c / E12, p_e / E12, t_e * EV_K)
    write_ieos(fi, idi, r, de_c / E12, e0_i / E12, p_i / E12, t_i * EV_K)
    print(f"电子表 → {fe} (id={int(ide)}),  离子表 → {fi} (id={int(idi)})")

    # 物理抽查: 高温端电子压强应显著大于 0, 且同点总压≈电子+离子
    j = ne - 1
    i = np.argmax(r)
    print(f"抽查 ρ={r[i]:.3g}: de_max 处 P_tot={p_c[j*nr+i]:.3e} dyn/cm², "
          f"P_e={p_e[j*nr+i]:.3e}, P_i={p_i[j*nr+i]:.3e}, "
          f"Pe+Pi={p_e[j*nr+i]+p_i[j*nr+i]:.3e}")


if __name__ == "__main__":
    main()
