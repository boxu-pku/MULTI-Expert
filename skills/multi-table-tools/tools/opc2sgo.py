#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
opc2sgo.py — hyades opc_*.dat (平均不透明度库) → MULTI sgo 单群表

源格式（经 Multi_BACK C++ 源码 CHYADES_Tab.h 确认）:
  行1: 标题;  行2: 表号 zbar abar rho0 数据总数
  数据(15字符定宽, 每行5个): NR, NT, rho[NR](g/cc), T[NT](keV),
    Rosseland[NT×NR](cm²/g, T行rho列, 线性值), Planck[NT×NR](同布局)
  特例: Planck 全零 → 仅 Rosseland, 用 Rosseland 代替 Planck

目标 MULTI sgo 格式 (Mat2013_LoadMF / 1D Fortran load_table_group 均可读):
  60字符头: [id][type][NR][NT],  type: Planck=" 0.70000000E+01",
  Rosseland=" 0.40000000E+01" (r94 与 1D Fortran 双兼容)
  数据: log10(rho), log10(T/eV), log10(kappa) 连续打包, 每行4值
  布局: "前 NR 个值对应第一个温度" (T 行 rho 列 —— 与源一致)

用法: python3 opc2sgo.py <opc文件> <id> <输出前缀>
  产出 <前缀>.ROSS 和 <前缀>.PLANCK
"""
import sys
import numpy as np


def read_opc(path):
    raw = open(path, "rb").read().replace(b"\r\n", b"\n").decode("ascii", "replace")
    vals = []
    for line in raw.split("\n")[2:]:
        for i in range(len(line) // 15):
            try:
                vals.append(float(line[15 * i:15 * (i + 1)]))
            except ValueError:
                pass
    vals = np.array(vals)
    NR, NT = int(vals[0]), int(vals[1])
    rho = vals[2:2 + NR]
    T = vals[2 + NR:2 + NR + NT]                       # keV
    ross = vals[2 + NR + NT: 2 + NR + NT + NR * NT]
    plan = vals[2 + NR + NT + NR * NT: 2 + NR + NT + 2 * NR * NT]
    if len(plan) < NR * NT or np.all(plan == 0.0):
        plan = ross.copy()                             # 源码规则: 无 Planck 则用 Rosseland
    return rho, T, ross, plan


def write_sgo(path, table_id, type_str, rho, T_keV, kappa):
    """写 sgo 表: log10(rho), log10(T/eV), log10(kappa)"""
    NR, NT = len(rho), len(T_keV)
    lr = np.log10(rho)
    lt = np.log10(T_keV * 1e3)                          # keV → eV
    lo = np.log10(np.clip(kappa, 1e-300, None))
    with open(path, "w") as f:
        f.write(f"{float(table_id):15.8e}{type_str}{float(NR):15.8e}{float(NT):15.8e}\n")
        vals = np.concatenate([lr, lt, lo])
        for i in range(0, len(vals), 4):
            f.write("".join(f"{v:15.8e}" for v in vals[i:i + 4]) + "\n")


def main():
    src, tid, prefix = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    rho, T, ross, plan = read_opc(src)
    write_sgo(prefix + ".ROSS", tid, " 0.40000000E+01", rho, T, ross)
    write_sgo(prefix + ".PLANCK", tid, " 0.70000000E+01", rho, T, plan)
    same = np.all(ross == plan)
    print(f"{src} -> {prefix}.ROSS/.PLANCK  NR={len(rho)} NT={len(T)}"
          f" 群边界均值表 (Planck{'=Rosseland(源缺省)' if same else '独立'})")


if __name__ == "__main__":
    main()
