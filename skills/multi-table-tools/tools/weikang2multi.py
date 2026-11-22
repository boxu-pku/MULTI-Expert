#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weikang2multi.py — WeiKang 论文提取 EOS (.txt) → MULTI 总 IEOS 表

源格式: 首行列头, # 注释, 空格对齐, 每行一个 (rho,T) 点的 P/E。
各文件的列序/单位差异由 CONFIG 描述。

转换链: (rho,T,P,E) → EOSDataset(electron=总量, ion=理想气体)
        → EOS-tools multi writer (自适应 ΔE) → 总 IEOS
单位约定见各 config 注释。能量零点任意值无碍 (IEOS 有 E0(rho) 基准)。

用法: python3 weikang2multi.py <config名> [输出文件]
"""
import os
import sys
import numpy as np

sys.path.insert(0, "/home/ubuntu/local/EOS_converter_xubo/EOS-tools")
import warnings
warnings.filterwarnings("ignore")
from eoslib.model import EOSDataset, EOSMetadata
import eoslib.formats.multi as multi_fmt

SRC = "/home/ubuntu/local/newmulti/weikang状态方程表_汇总/状态方程"
EV_PER_RY = 13.6057
EV_PER_HA = 27.2114
K_PER_EV = 11604.519
NA_EV_TO_JPG = 96485.33   # 1 eV/粒子 → J/g 的换算(再除 A): E*96485.33/A
                          # 精确: 1.602176565e-19/1.660538921e-24/1000

# 每文件配置: cols=(rho列, T列, P列, E列), p_unit(P→MPa 乘子), t_unit(T→eV 乘子或 'K'),
#            e_unit(E→eV/粒子 乘子), A(每粒子式量), skip_cols(前置非数值列数)
CONFIG = {
    "H_wk":    dict(file="刘兴_A1_氢_H.txt", cols=(1, 2, 3, 4), p_unit=1e5, t_unit=1.0,
                    e_unit=1.0, A=1.008, skip=1),          # P Mbar
    "C_wk":    dict(file="刘兴_A2_碳_C.txt", cols=(1, 2, 3, 4), p_unit=1e5, t_unit=1.0,
                    e_unit=1.0, A=12.011, skip=1),         # 首列 G/D 构型
    "C8H8_wk": dict(file="刘兴_A3_聚苯乙烯_C8H8.txt", cols=(0, 1, 2, 3), p_unit=1e5, t_unit=1.0,
                    e_unit=1.0, A=13.019, skip=0),         # E per CH 单元
    "C9H10_wk": dict(file="刘兴_A4_聚α-甲基苯乙烯_C9H10.txt", cols=(0, 1, 2, 3), p_unit=1e5, t_unit=1.0,
                    e_unit=1.0, A=118.179, skip=0),        # E per C9H10
    "CH2_wk":  dict(file="刘兴_A5_聚乙烯_CH2.txt", cols=(0, 1, 2, 3), p_unit=1e5, t_unit=1.0,
                    e_unit=1.0, A=14.027, skip=0),
    "Fe_wk":   dict(file="刘兴_A6_铁_Fe.txt", cols=(0, 1, 2, 3), p_unit=1e5, t_unit=1.0,
                    e_unit=1.0, A=55.845, skip=0),
    "Be_wk":   dict(file="高畅_表4.1_铍_Be.txt", cols=(0, 1, 2, 3), p_unit=1e5, t_unit=1.0,
                    e_unit=1.0, A=9.012, skip=0),
    "Si_wk":   dict(file="高畅_表4.2_硅_Si.txt", cols=(0, 1, 3, 2), p_unit=1e3, t_unit="K",
                    e_unit=EV_PER_HA, A=28.085, skip=0),   # PBE: E=第2列(Ha), P=第3列(GPa)
    "BN_wk":   dict(file="杨雨桐_A1_氮化硼_BN.txt", cols=(0, 1, 3, 2), p_unit=100.0, t_unit=1.0,
                    e_unit=EV_PER_RY, A=24.817, skip=0),   # E Ry/BN, P KBar
    "Pb_wk":   dict(file="杨雨桐_A2_铅_Pb.txt", cols=(0, 1, 3, 2), p_unit=100.0, t_unit=1.0,
                    e_unit=EV_PER_RY, A=207.2, skip=0),
    "LiF1_wk": dict(file="张肖涵_表A.1_LiF_32原子.txt", cols=(1, 0, 3, 2), p_unit=1e3, t_unit="K",
                    e_unit=1.0, A=25.94, skip=0),          # T 在首列(K), E eV/LiF, P GPa
    "LiF2_wk": dict(file="张肖涵_表A.2_LiF_8原子.txt", cols=(1, 0, 3, 2), p_unit=1e3, t_unit="K",
                    e_unit=1.0, A=25.94, skip=0),
    "SiO2wk12": dict(file="张肖涵_表A.3_SiO2_Si12价电子.txt", cols=(1, 0, 3, 2), p_unit=1e3, t_unit="K",
                    e_unit=1.0, A=60.08, skip=0),
    "SiO2wk14": dict(file="张肖涵_表A.4_SiO2_Si14价电子.txt", cols=(1, 0, 3, 2), p_unit=1e3, t_unit="K",
                    e_unit=1.0, A=60.08, skip=0),
}


def load_txt(cfg, min_points=3):
    """读 txt → 每密度一段 (T,P,E) 按 T 排序; 返回 rho_list, rows(rho→(T,P,E) arrays)
    min_points: 丢弃数据点少于此数的密度行(无法构成网格行)"""
    path = os.path.join(SRC, cfg["file"])
    rc, tc, pc, ec = cfg["cols"]
    data = {}
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split()
        skip = cfg["skip"]
        shift = 0
        if skip:
            # 构型字母列(G/D等)只在部分行出现: 有字母→列为 cols; 无字母→列整体前移1
            if parts[0][0].isalpha():
                pass                      # 有字母: 按 skip 跳过, cols 不变
            else:
                try:
                    float(parts[0])
                    shift = -1            # 无字母: 所有列索引 -1, 不跳列
                    skip = 0
                except ValueError:
                    pass
        try:
            vals = [float(x) for x in parts[skip:]]
        except ValueError:
            continue
        if "NaN" in parts or any(v != v for v in vals):
            continue
        if len(vals) <= max(rc, tc, pc, ec) + shift - skip:
            continue
        rho = vals[rc + shift - skip]
        T = vals[tc + shift - skip]
        P = vals[pc + shift - skip]
        E = vals[ec + shift - skip]
        data.setdefault(rho, []).append((T, P, E))
    # 丢弃稀疏密度行
    data = {r: v for r, v in data.items() if len(v) >= min_points}
    rhos = sorted(data.keys())
    rows = {}
    for r in rhos:
        arr = np.array(sorted(data[r]))
        rows[r] = (arr[:, 0], arr[:, 1], arr[:, 2])
    return rhos, rows


def to_eostools_grid(cfg, rhos, rows, t_min_ev=None, n_t=100):
    """把分块数据插值到公共 (rho × T) 网格 (log T)"""
    t_all = np.concatenate([rows[r][0] for r in rhos])
    if cfg["t_unit"] == "K":
        t_all = t_all / K_PER_EV
    t0 = t_min_ev if t_min_ev else max(t_all.min(), 1e-3)
    t1 = t_all.max()
    Tgrid = np.geomspace(t0, t1, n_t)
    Pg = np.zeros((len(rhos), n_t))
    Eg = np.zeros((len(rhos), n_t))
    for i, r in enumerate(rhos):
        T, P, E = rows[r]
        if cfg["t_unit"] == "K":
            T = T / K_PER_EV
        P_mpa = P * cfg["p_unit"]
        E_jpg = E * cfg["e_unit"] * NA_EV_TO_JPG / cfg["A"]
        # log-log 插值 (P,E 可能含负值 → 用线性; T 单调)
        Pg[i] = np.interp(Tgrid, T, P_mpa, left=np.nan, right=np.nan)
        Eg[i] = np.interp(Tgrid, T, E_jpg, left=np.nan, right=np.nan)
    # 裁掉全 NaN 的 T 列
    good = ~np.all(np.isnan(Pg), axis=0)
    Tgrid, Pg, Eg = Tgrid[good], Pg[:, good], Eg[:, good]
    # 行内 NaN (该密度无此温区数据) → 用最近值填充边界
    for i in range(len(rhos)):
        m = ~np.isnan(Pg[i])
        if m.sum() < 2:
            continue
        Pg[i] = np.interp(Tgrid, Tgrid[m], Pg[i][m])
        Eg[i] = np.interp(Tgrid, Tgrid[m], Eg[i][m])
    return Tgrid, Pg, Eg


def convert(name, out_path):
    cfg = CONFIG[name]
    rhos, rows = load_txt(cfg)
    Tgrid, Pg, Eg = to_eostools_grid(cfg, rhos, rows)
    rho_arr = np.array(rhos, dtype=float)
    ds = EOSDataset(rho_gcc=rho_arr, temp_ev=Tgrid,
                    ion_pressure_mpa=Pg, electron_pressure_mpa=Pg,
                    ion_energy_jpg=Eg, electron_energy_jpg=Eg,
                    mean_ionization=np.zeros((len(rhos), len(Tgrid))),
                    metadata=EOSMetadata(source_format="weikang-txt",
                                         atom_a=cfg["A"], atom_z=1))
    tmp = "/tmp/_wk_conv/out"
    os.makedirs("/tmp/_wk_conv", exist_ok=True)
    outs = multi_fmt.save(ds, output_prefix=tmp, energy_points=128,
                          adaptive_energy_grid=True, write_opacity=False)
    import shutil
    shutil.copy(outs["electron"], out_path)
    print(f"{name}: {cfg['file']} → {out_path}")
    print(f"  rho {rho_arr.min():.4g}~{rho_arr.max():.4g} g/cc ({len(rhos)}点), "
          f"T {Tgrid.min():.3g}~{Tgrid.max():.3g} eV ({len(Tgrid)}点)")


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
