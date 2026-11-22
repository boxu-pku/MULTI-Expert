#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_hugoniot.py — 从 1D 算例 fort.10 提取 Hugoniot 状态点

方法(适用于辐射浴/激光驱动产生的向左传播的准定常冲击波):
  1. 每条记录: 波前 = 密度从波前态抬升 1.1*rho0 的最左位置(线性插值到亚单元)
  2. 波前轨迹 x_f(t) → Us(t): **局部滑动窗口线性拟合**, 斜率即当地冲击波速度
     (冲击波向左传播, 斜率为负, Us = -dx_f/dt > 0)。
     不是全程多项式: 衰减波全程用单一多项式会把局部速度平均掉。
  3. 同时刻波后状态: **自适应平台取样** —— 从波前向后扫描压强剖面,
     连续 3 单元相对变化 <0.5% 处为平台起点, 取其后 4 单元平均
     (辐射前驱使石英类材料过渡区宽达 ~14 单元, 固定偏移会取到过渡区内;
     Al 的过渡区 ~4 单元, 平台检测自动退化为 i_f+2 附近)
  4. 波前态: 波前前方 i_f-30..i_f-10 单元中位数 → rho0, P0, v0
  5. Rankine-Hugoniot 动量自洽: P1-P0 ≈ rho0·Us·(Up1-Up0)

可用性门禁(物理判据, 替代旧版固定 10%~55% 时间窗):
  A. 波前态纯净: 0.99 <= rho_pre/rho0 <= 1.01 且 |v_pre| <= V_PRE_MAX
     —— 自由界面稀疏波(预热膨胀)到达后波前态失真, 自动剔除近界面时段
  B. 冲击波仍在前进: 局部轨迹斜率 < 0
     —— 稀疏波追上冲击波后阈值位置倒退, 斜率翻正, 剔除
  C. 取样窗口不越界: i_f-30 >= 0
  D. 冲击已成形: rho_post >= 1.05*rho0 (剔除驱动建立期初始瞬态)
  E. RH 动量残差 |resid| < 25% (最终安全网)

输出 dict 列表 + scan_case() 供溯源图复用完整轨迹。
用法: python3 extract_hugoniot.py <算例目录> [rho0]
"""
import os
import sys
import numpy as np

sys.path.insert(0, "/home/ubuntu/local/MULTI-2D.2026.3/work/eos_opacity_tools")
from plot_1d_validation import read_fort10_ascii

# ---- 可调参数 ----
PRE_LO, PRE_HI = 30, 10      # 波前态取样: 波前前方 30..10 单元 (中位数)
POST_N = 4                   # 波后平台取样单元数
PLAT_TOL = 5e-3              # 平台判据: 相邻单元 P 相对变化
PLAT_PERSIST = 3             # 平台判据: 连续满足单元数
PLAT_SCAN = 60               # 平台搜索最大单元数(覆盖辐射加宽的过渡区)
FALLBACK_LO, FALLBACK_HI = 2, 6   # 平台未找到时回退: i_f+2..i_f+5
FIT_W = 12                   # Us 局部拟合半径(记录数): ±12 条 ≈ ±0.5 ns
RHO_TOL = 0.01               # 波前态密度容差 ±1% (纯净区实测 2.7000±0.0001)
V_PRE_MAX = 5e3              # 波前态速度容差 0.05 km/s (预热膨胀远超此值)
RH_MAX = 0.25                # RH 动量残差上限
RHO_POST_MIN = 1.05          # 波后密度下限(×rho0): 剔除冲击未成形的初始瞬态
HEAD_SKIP = 0.05             # 采样时跳过可用窗口头部 5% (驱动建立期)


def find_front(x, rho, rho0_eff):
    """波前 = 密度超 1.1*rho0_eff 的最左位置, 线性插值到亚单元精度"""
    thresh = rho0_eff * 1.1
    above = np.where(rho > thresh)[0]
    if len(above) == 0:
        return None, None
    i0 = above[0]
    if i0 == 0:
        return x[0], 0
    x1, x2 = x[i0 - 1], x[i0]
    r1, r2 = rho[i0 - 1], rho[i0]
    frac = (thresh - r1) / (r2 - r1) if r2 != r1 else 0.5
    return x1 + frac * (x2 - x1), i0


def find_plateau(P, i_f, ncell):
    """波后平台起点: 从 i_f+1 起向后扫描, 连续 PLAT_PERSIST 个相邻单元
    P 相对变化 < PLAT_TOL 的位置; 找不到返回 None(调用方回退固定窗口)。
    辐射前驱会把过渡区加宽(石英 ~14 单元), 固定偏移会取进过渡区。"""
    run = 0
    for i in range(i_f + 1, min(i_f + PLAT_SCAN, ncell - 1)):
        p0, p1 = P[i], P[i + 1]
        if p0 > 0 and abs(p1 - p0) / p0 < PLAT_TOL:
            run += 1
            if run >= PLAT_PERSIST:
                return i - PLAT_PERSIST + 1
        else:
            run = 0
    return None


def scan_case(case_dir, rho0):
    """全记录扫描: 波前轨迹/波前态/波后态/局部Us/门禁掩码, 供提取与溯源图共用"""
    d = read_fort10_ascii(os.path.join(case_dir, "fort.10"))
    times = d["TIME"][:, 0]
    R, XC, V, PT = d["R"], d["XC"], d["V"], d["PT"]
    nrec, ncell = R.shape

    xf = np.full(nrec, np.nan)
    i_f = np.full(nrec, -1, dtype=int)
    rho_pre = np.full(nrec, np.nan)
    v_pre = np.full(nrec, np.nan)
    P_pre = np.full(nrec, np.nan)
    rho_post = np.full(nrec, np.nan)
    v_post = np.full(nrec, np.nan)
    P_post = np.full(nrec, np.nan)
    pre_cells = [None] * nrec
    post_cells = [None] * nrec

    for k in range(nrec):
        xfk, ifk = find_front(XC[k], R[k], rho0)
        if xfk is None:
            continue
        xf[k], i_f[k] = xfk, ifk
        pre = np.arange(max(0, ifk - PRE_LO), max(0, ifk - PRE_HI))
        # 波后: 自适应平台取样, 回退固定窗口
        ip = find_plateau(PT[k], ifk, ncell)
        if ip is not None:
            post = np.arange(ip, min(ip + POST_N, ncell))
        else:
            post = np.arange(ifk + FALLBACK_LO, min(ifk + FALLBACK_HI, ncell))
        if len(pre) >= 3:
            rho_pre[k] = float(np.median(R[k][pre]))
            v_pre[k] = float(np.median(V[k][pre]))
            P_pre[k] = float(np.median(PT[k][pre]))
            pre_cells[k] = pre
        if len(post) >= 2:
            rho_post[k] = float(np.mean(R[k][post]))
            # V 在界面上(n+1): 取波后单元右界面对应的速度
            v_post[k] = float(np.mean(V[k][post + 1]))
            P_post[k] = float(np.mean(PT[k][post]))
            post_cells[k] = post

    # Us(t): 局部滑动窗口线性拟合 x_f(t), 斜率 = dx_f/dt (向左为负)
    Us = np.full(nrec, np.nan)
    fit_r2 = np.full(nrec, np.nan)
    fit_win = [None] * nrec
    valid = np.isfinite(xf)
    for k in range(nrec):
        lo = max(0, k - FIT_W)
        hi = min(nrec, k + FIT_W + 1)
        w = np.arange(lo, hi)
        w = w[valid[w]]
        if len(w) < 6:
            continue
        coef = np.polyfit(times[w], xf[w], 1)
        slope = coef[0]
        Us[k] = -slope                      # 向左传播 → 斜率负 → Us 取正
        yhat = np.polyval(coef, times[w])
        ss_res = float(np.sum((xf[w] - yhat) ** 2))
        ss_tot = float(np.sum((xf[w] - np.mean(xf[w])) ** 2))
        fit_r2[k] = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
        fit_win[k] = (int(w[0]), int(w[-1]), float(coef[0]), float(coef[1]))

    # 门禁掩码
    gateA = (np.abs(rho_pre / rho0 - 1.0) <= RHO_TOL) & (np.abs(v_pre) <= V_PRE_MAX)
    gateB = np.isfinite(Us) & (Us > 0)
    gateC = (i_f - PRE_LO) >= 0
    gateD = np.isfinite(rho_post) & (rho_post >= RHO_POST_MIN * rho0)
    usable = gateA & gateB & gateC & gateD

    return dict(times=times, XC=XC, R=R, V=V, PT=PT,
                xf=xf, i_f=i_f, Us=Us, fit_r2=fit_r2, fit_win=fit_win,
                rho_pre=rho_pre, v_pre=v_pre, P_pre=P_pre,
                rho_post=rho_post, v_post=v_post, P_post=P_post,
                pre_cells=pre_cells, post_cells=post_cells,
                gateA=gateA, gateB=gateB, gateC=gateC, gateD=gateD, usable=usable)


def extract_series(case_dir, rho0, n_points=24):
    """按门禁筛选后均匀采样 n_points 个 Hugoniot 点"""
    s = scan_case(case_dir, rho0)
    times = s["times"]
    ok = np.where(s["usable"])[0]
    if len(ok) < 10:
        raise RuntimeError(f"可用记录太少: {len(ok)}")
    # 跳过窗口头部(驱动建立期), 其余均匀采样
    ok = ok[int(len(ok) * HEAD_SKIP):]
    idx = ok[np.linspace(0, len(ok) - 1, min(n_points, len(ok))).astype(int)]
    results = []
    for k in idx:
        Us = s["Us"][k]
        Upm = abs(s["v_post"][k] - s["v_pre"][k])
        if Us <= 0 or Upm <= 0:
            continue
        P1, P0 = s["P_post"][k], s["P_pre"][k]
        rho1, rho0_t = s["rho_post"][k], s["rho_pre"][k]
        rh_mom = rho0_t * Us * Upm               # dyn/cm2
        resid = ((P1 - P0) - rh_mom) / rh_mom if rh_mom else np.nan
        if not np.isfinite(resid) or abs(resid) >= RH_MAX:
            continue                             # 门禁 E: RH 动量自洽
        results.append(dict(t=times[k], Us=Us, Up=Upm, P1=P1, rho1=rho1,
                            rho0=rho0_t, P0=P0, v0=s["v_pre"][k], resid=resid,
                            rec=int(k), i_front=int(s["i_f"][k]),
                            pre_cells=s["pre_cells"][k].tolist(),
                            post_cells=s["post_cells"][k].tolist(),
                            fit_win=s["fit_win"][k], fit_r2=float(s["fit_r2"][k])))
    return results


def main():
    case_dir = sys.argv[1]
    rho0 = float(sys.argv[2]) if len(sys.argv) > 2 else 2.7
    s = scan_case(case_dir, rho0)
    n_all = np.isfinite(s["xf"]).sum()
    n_use = s["usable"].sum()
    fin = np.isfinite(s["xf"])
    print(f"{os.path.basename(case_dir)}: 总记录 {n_all}, 过门禁 {n_use} "
          f"(剔除: A波前态不纯净 {(fin & ~s['gateA']).sum()}, "
          f"B斜率翻正 {(fin & ~s['gateB']).sum()}, "
          f"C窗口越界 {(fin & ~s['gateC']).sum()}, "
          f"D冲击未成形 {(fin & ~s['gateD']).sum()})")
    res = extract_series(case_dir, rho0)
    print(f"{'t[ns]':>7s} {'Us[km/s]':>9s} {'Up[km/s]':>9s} {'P1[Mbar]':>9s} "
          f"{'rho1':>7s} {'rho0':>6s} {'R2':>6s} {'RH残差':>8s}")
    for r in res:
        print(f"{r['t']*1e9:7.2f} {r['Us']/1e5:9.3f} {r['Up']/1e5:9.3f} "
              f"{r['P1']/1e12:9.3f} {r['rho1']:7.3f} {r['rho0']:6.3f} "
              f"{r['fit_r2']:6.4f} {r['resid']:+8.1%}")


if __name__ == "__main__":
    main()
