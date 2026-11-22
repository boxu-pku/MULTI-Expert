#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_1d_validation.py — 材料迁移验收算例(1D MULTI-IFE)的可视化

解析 1D 程序(m150304.f95)写出的 ASCII fort.10, 生成验收用图:
  1. density_heatmap.png  —— 密度热图 rho(x,t)
  2. profiles_mid.png     —— 中间时刻的密度/温度/压强剖面

fort.10 ASCII 结构(由 write_output_record/write_vect 写出):
  行0:        n1            (第一节计数)
  随后 n1 行: 变量名 (每个元素一行, 如 'CMC     ' x20)
  随后 n1 行: 索引
  随后:       n2            (第二节计数)
  随后 n2 行: 变量名
  随后 n2 行: 索引
  随后:       每条记录 n2 个值(每行一个, e12.5), 直到 EOF
记录内变量顺序见 write_output_record: 标量24个(TIME,ISTEP,...),
  单元量13个(R,PT,TE,PE,ZI,XC,D,DENE,EA,F,TI,PI,AD),
  界面量6个(X,V,TR,S+,S-,S), 群量2个(I-,I+)。

用法:
  python3 plot_1d_validation.py <算例目录>
产物(存于算例目录内):
  density_heatmap.png, profiles_mid.png
"""
import sys
import os
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_fort10_ascii(path):
    """解析 ASCII fort.10, 返回 (times, dict_of_2d_arrays)
    dict[var] 形状为 (n_records, n_points)"""
    with open(path) as f:
        lines = f.read().split("\n")
    pos = 0

    def read_count():
        nonlocal pos
        while pos < len(lines) and lines[pos].strip() == "":
            pos += 1
        n = int(lines[pos].strip())
        pos += 1
        return n

    # 第一节(网格/群结构): count + names + indices + values, 跳过
    n1 = read_count()
    pos += n1          # names
    pos += n1          # indices
    pos += n1          # values
    # 第二节头部: 计数 + 变量名 + 索引 (首记录的值随后)
    n2 = read_count()
    names = [lines[pos + i].strip() for i in range(n2)]
    pos += n2
    pos += n2          # indices

    # 每个变量的起始位置与长度(名字连续重复)
    var_slices = {}
    i = 0
    while i < n2:
        j = i
        while j < n2 and names[j] == names[i]:
            j += 1
        var_slices[names[i]] = (i, j - i)
        i = j

    # 读记录
    import re
    vals = []
    for k in range(pos, len(lines)):
        s = lines[k].strip()
        if s == "":
            continue
        try:
            vals.append(float(s))
        except ValueError:
            # Fortran e12.5 溢出时省略 'e' (如 '-0.33689-232' = -0.33689e-232)
            m = re.match(r"^([+-]?\d+\.?\d*)([+-]\d+)$", s)
            if m:
                vals.append(float(f"{m.group(1)}e{m.group(2)}"))
            else:
                raise
    n_rec = len(vals) // n2
    data = np.array(vals[: n_rec * n2]).reshape(n_rec, n2)

    out = {}
    for var, (i0, m) in var_slices.items():
        out[var] = data[:, i0:i0 + m]
    return out


def main():
    case_dir = sys.argv[1].rstrip("/")
    fort10 = os.path.join(case_dir, "fort.10")
    d = read_fort10_ascii(fort10)

    times = d["TIME"][:, 0]            # s
    R = d["R"]                         # (nrec, n) 密度 g/cm3
    XC = d["XC"]                       # (nrec, n) 单元中心 cm
    TE = d["TE"]                       # 电子温度 eV
    TI = d["TI"]                       # 离子温度 eV
    PT = d["PT"]                       # 总压强 (cgs, dyn/cm2)
    PE = d["PE"]                       # 电子压强
    nrec = len(times)
    print(f"记录数: {nrec}, 时间: {times[0]:.3e} ~ {times[-1]:.3e} s")

    # ---------- 图1: 密度热图 (空间轴=初始靶范围) ----------
    fig, ax = plt.subplots(figsize=(8, 5.2))
    # pcolormesh 需要 (nt, nx) 网格: X=时间, Y=位置(拉格朗日随体)
    T2d = np.repeat(times[:, None], R.shape[1], axis=1) * 1e9   # ns
    X2d = XC * 1e4                                                # um
    pcm = ax.pcolormesh(T2d, X2d, R, shading="auto", cmap="viridis")
    cb = fig.colorbar(pcm, ax=ax)
    cb.set_label(r"density $\rho$  (g/cm$^3$)")
    ax.set_xlabel("time  (ns)")
    ax.set_ylabel(r"position  ($\mu$m)")
    # 空间范围取初始靶区间(首记录的界面网格)
    x0 = d["X"][0] * 1e4                                          # um
    ax.set_ylim(x0.min(), x0.max())
    ax.set_title(f"Density map (initial target range) — {os.path.basename(case_dir)}")
    fig.tight_layout()
    out1 = os.path.join(case_dir, "density_heatmap.png")
    fig.savefig(out1, dpi=150)
    plt.close(fig)

    # ---------- 图2: 中间时刻剖面 ----------
    imid = np.argmin(np.abs(times - 0.5 * times[-1]))
    tmid = times[imid]
    x = XC[imid] * 1e4   # um
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))
    axes[0].plot(x, R[imid], "b-o", ms=4)
    axes[0].set_ylabel(r"$\rho$ (g/cm$^3$)")
    axes[0].set_title("density")
    axes[1].plot(x, TE[imid], "r-o", ms=4, label="$T_e$")
    axes[1].plot(x, TI[imid], "b--s", ms=4, label="$T_i$")
    axes[1].set_ylabel("T (eV)")
    axes[1].set_title("temperature")
    axes[1].legend()
    axes[2].plot(x, PT[imid], "k-o", ms=4, label="$P_{tot}$")
    axes[2].plot(x, PE[imid], "g--s", ms=4, label="$P_e$")
    axes[2].set_ylabel("P (dyn/cm$^2$)")
    axes[2].set_title("pressure")
    axes[2].legend()
    for a in axes:
        a.set_xlabel(r"position  ($\mu$m)")
        a.grid(alpha=0.3)
    fig.suptitle(f"Profiles at t = {tmid*1e9:.3f} ns (record {imid+1}/{nrec})"
                 f" — {os.path.basename(case_dir)}")
    fig.tight_layout()
    out2 = os.path.join(case_dir, "profiles_mid.png")
    fig.savefig(out2, dpi=150)
    plt.close(fig)

    print("已生成:")
    print(" ", out1)
    print(" ", out2)


if __name__ == "__main__":
    main()
