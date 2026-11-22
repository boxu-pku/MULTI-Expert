#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_material_functions.py — 为迁移材料生成 2D 材料函数(r94 源码)

- full/celia 批次: opafun = 该材料 Thermos/CELIA Rosseland 多群表的
  Rosseland 平均自由程最小二乘拟合 (log10 λ = a + s·log10 T + r·log10 ρ)
- eos_only 批次: opafun = * (无不透明度, 辐射输运不可用)

产物: r94/m2d-core-9.1/Material_mig.r  (随后需 x.2.library 重编译)
"""
import os
import sys
import numpy as np

sys.path.insert(0, "/home/ubuntu/local/MULTI-2D.2026.3/work/eos_opacity_tools")
from migrate_manifest import BATCH_FULL, BATCH_CELIA, BATCH_EOS_ONLY
from strict_binary_test import CStrictParser

MULTI = "/home/ubuntu/local/MULTI-2D.2026.3"
TABLES = f"{MULTI}/r94/MULTI-IFE-2015/tables"

# Material.r（R.Ramis 原生）已定义这些材料的 2D 函数（CH=CHOQG, Cu/Fe/W=MPQEOS.i301，
# 均非 ×1000 病态源）。迁移批次仅为它们补 1D 表 + 不透明度，不应在 Material_mig.r
# 重定义同名函数——否则与 Material.o 产生多重定义链接冲突（MaterialCH/Cu/Fe/W0）。
# 故生成时跳过，保留 Material.r 的版本。
SKIP_COLLISION = {"CH", "Cu", "Fe", "W"}


class OpaParser(CStrictParser):
    def load_mgo_all(self):
        tables = []
        while True:
            a = self.read_line()
            if isinstance(a, int):
                break
            assert len(a) == 60
            nr = int(float(a[30:45])); nt = int(float(a[45:60]))
            l2 = self.read_line()
            f1, f2 = float(l2[0:15]), float(l2[15:30])
            r = self.read_vector(nr); t = self.read_vector(nt)
            o = self.read_vector(nr * nt)
            tables.append((f1, f2, r, t, o))
        return tables


def planck_w(nu, T):
    x = np.clip(nu / max(T, 1e-30), 1e-10, 300)
    return nu**3 / np.expm1(x)


def dBdT_group(f1, f2, T):
    dT = max(T * 1e-3, 1e-9)
    w = ((planck_w(f2, T + dT) - planck_w(f1, T + dT))
         - (planck_w(f2, T - dT) - planck_w(f1, T - dT))) / (2 * dT)
    return max(w, 0.0)


def rosseland_fit(ross_file):
    """返回 (a, s, r, rms_dex, tmin_eV, tmax_eV, rhomin, rhomax)"""
    tabs = OpaParser(ross_file).load_mgo_all()
    lr = np.array(tabs[0][2]); lt = np.array(tabs[0][3])
    nr, nt = len(lr), len(lt)
    lam = np.full((nt, nr), np.nan)
    for it in range(nt):
        T = 10**lt[it]
        w = np.array([dBdT_group(t[0], t[1], T) for t in tabs])
        if w.sum() <= 0:
            continue
        for ir in range(nr):
            kap = np.array([10**(t[4][it * nr + ir]) for t in tabs])
            denom = (kap * w).sum()
            if denom > 0:
                lam[it, ir] = w.sum() / denom / (10**lr[ir])
    mask = np.isfinite(lam) & (lam > 0)
    if mask.sum() < 10:
        return None
    X = np.column_stack([np.ones(mask.sum()),
                         np.repeat(lt, nr)[mask.ravel()],
                         np.tile(lr, nt)[mask.ravel()]])
    y = np.log10(lam[mask])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ coef
    return (coef[0], coef[1], coef[2], res.std(),
            10**lt[0], 10**lt[-1], 10**lr[0], 10**lr[-1])


FUNC_FULL = """$==============================================================================
$$=Material{name}()
$$   mat=Material{name}()
$$   {name} (migrated from Multi_BACK, see mat_{name}-1.0)
$$   EOS: mat_{name}-1.0/{name}_eos
$$   Rosseland mfp fit from {opa_src} multigroup table:
$$   log10(lambda[cm]) = {a:.4f} + {s:.4f}*log10(T[eV]) + {r:.4f}*log10(rho[g/cm3])
$$   fit rms {rms:.2f} dex over T=[{tmin:.3g},{tmax:.3g}]eV, rho=[{rmin:.3g},{rmax:.3g}]
Material{name}()
{{
   eosfile         = getenv("MULTI"):"/r94/mat_{name}-1.0/{name}_eos";
   material        = Mat2013();
   material.ieos   = Mat2013_LoadIEOS(eosfile);
   material.ai     = {A};
   material.zi     = {Z};
   material.z2i    = {Z};
   material.ieose  = Mat2013_EleTab(material.ieos,material.ai);
   material.ieosi  = Mat2013_GasIEOS(material.ai,double(5)/double(3));
   material.opafun = 'freepath_{name}(2)';
   material.rho    = {rho0};
   return(material);
}}
local freepath_{name}(r,t)
{{
   l=10^({a:.4f})*t^{s:.4f}*r^({r:.4f});
   return(l);
}}
"""

FUNC_EOS_ONLY = """$==============================================================================
$$=Material{name}()
$$   mat=Material{name}()
$$   {name} (migrated from Multi_BACK hyades, EOS only, no opacity)
Material{name}()
{{
   eosfile         = getenv("MULTI"):"/r94/mat_{name}-1.0/{name}_eos";
   material        = Mat2013();
   material.ieos   = Mat2013_LoadIEOS(eosfile);
   material.ai     = {A};
   material.zi     = {Z};
   material.z2i    = {Z};
   material.ieose  = Mat2013_EleTab(material.ieos,material.ai);
   material.ieosi  = Mat2013_GasIEOS(material.ai,double(5)/double(3));
   material.opafun = *;
   material.rho    = {rho0};
   return(material);
}}
"""


def main():
    out = ["$" + "-" * 77,
           "$  Material_mig.r — 迁移材料的 2D 材料函数（自动生成 2026-08-10）",
           "$  由 work/eos_opacity_tools/gen_material_functions.py 生成",
           "$" + "-" * 77, ""]
    n_full = n_eos = 0
    for name, A, Z, rho0, eos, tsym in BATCH_FULL:
        if name in SKIP_COLLISION:
            print(f"跳过 {name}: Material.r 已提供（避免链接冲突）")
            continue
        ross = f"{TABLES}/{name}_Thermos.ROSSELAND"
        if not os.path.exists(ross):
            print(f"跳过 {name}: 无 {ross}")
            continue
        fit = rosseland_fit(ross)
        if fit is None:
            print(f"跳过 {name}: 拟合失败")
            continue
        a, s, r, rms, tmin, tmax, rmin, rmax = fit
        out.append(FUNC_FULL.format(name=name, A=A, Z=Z, rho0=rho0,
                                    opa_src=f"Thermos {tsym}", a=a, s=s, r=r,
                                    rms=rms, tmin=tmin, tmax=tmax,
                                    rmin=rmin, rmax=rmax))
        n_full += 1
        print(f"{name}: λ=10^{a:.2f}·T^{s:.2f}·ρ^{r:.2f} (rms {rms:.2f} dex)")
    for name, A, Z, rho0, eos, opre, zf in BATCH_CELIA:
        if name in SKIP_COLLISION:
            print(f"跳过 {name}: Material.r 已提供（避免链接冲突）")
            continue
        ross = f"{TABLES}/{name}_CELIA.ROSS"
        if not os.path.exists(ross):
            continue
        fit = rosseland_fit(ross)
        if fit is None:
            continue
        a, s, r, rms, tmin, tmax, rmin, rmax = fit
        out.append(FUNC_FULL.format(name=name, A=A, Z=Z, rho0=rho0,
                                    opa_src=f"CELIA {opre}", a=a, s=s, r=r,
                                    rms=rms, tmin=tmin, tmax=tmax,
                                    rmin=rmin, rmax=rmax))
        n_full += 1
        print(f"{name}: λ=10^{a:.2f}·T^{s:.2f}·ρ^{r:.2f} (rms {rms:.2f} dex)")
    # opc 单群表拟合(2026-08-11 补充): 有拟合的用 FUNC_FULL
    opc_fits = {}
    if os.path.exists("/tmp/opc_fits.txt"):
        for line in open("/tmp/opc_fits.txt"):
            p = line.split()
            if len(p) == 5:
                opc_fits[p[0]] = tuple(map(float, p[1:4]))
    for name, A, Z, rho0, eos in BATCH_EOS_ONLY:
        if not os.path.exists(f"{MULTI}/r94/mat_{name}-1.0/{name}_eos"):
            print(f"跳过 {name}: 无 EOS 文件")
            continue
        if name in opc_fits:
            a, s, r = opc_fits[name]
            out.append(FUNC_FULL.format(name=name, A=A, Z=Z, rho0=rho0,
                                        opa_src="hyades opc 单群平均表", a=a, s=s, r=r,
                                        rms=0.9, tmin=1, tmax=203000,
                                        rmin=1e-6, rmax=10000))
            n_full += 1
        else:
            out.append(FUNC_EOS_ONLY.format(name=name, A=A, Z=Z, rho0=rho0))
            n_eos += 1
    path = f"{MULTI}/r94/m2d-core-9.1/Material_mig.r"
    with open(path, "w") as f:
        f.write("\n".join(out))
    print(f"\n写入 {path}: {n_full} 个带不透明度拟合, {n_eos} 个仅 EOS")


if __name__ == "__main__":
    main()
