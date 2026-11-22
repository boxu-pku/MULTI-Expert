#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_migrate.py — 材料批量迁移驱动（清单见 migrate_manifest.py）

对每种材料执行:
  full 批次:
    1. EOS → 2D 总 IEOS 表 (r94/mat_<X>-1.0/<X>_eos)
       - hyades 源: read_hyades_eos → EOS-tools multi writer (自适应 ΔE)
       - celia/mpqeos 源: 直接复制(去 CR)
    2. 总表 → 1D 电子/离子表 (split_ieos_table 算法) → MULTI-IFE-2015/tables/
    3. 不透明度/Zeff: Thermos(去CR+修-INF) 或 CELIA(去CR) → tables/
    4. 全部 check_multi_file 验证
    5. 生成 1D 验证算例 validation_cases/<X>Check/
  eos_only 批次: 仅步骤 1 + MODINFO/README

用法: python3 batch_migrate.py [材料名...]   (缺省 = 全部)
"""
import os
import sys
import shutil
import subprocess

sys.path.insert(0, "/home/ubuntu/local/EOS_converter_xubo/EOS-tools")
sys.path.insert(0, "/home/ubuntu/local/MULTI-2D.2026.3/work/eos_opacity_tools")

import numpy as np
import warnings
warnings.filterwarnings("ignore")

from migrate_manifest import (BATCH_FULL, BATCH_CELIA, BATCH_EOS_ONLY,
                              HYADES, CELIA, THERMOS)
import basefunctions.read_hyades as hyades_reader
from eoslib.model import EOSDataset, EOSMetadata
import eoslib.formats.multi as multi_fmt
from split_ieos_table import read_ieos, write_ieos, split_electron, make_ion_ideal, EV_K, E12
from strict_opacity_test import load_opacity_strict

MULTI = "/home/ubuntu/local/MULTI-2D.2026.3"
TABLES = f"{MULTI}/r94/MULTI-IFE-2015/tables"
CASES = f"{MULTI}/validation_cases"

LOG = []


def log(msg):
    print(msg)
    LOG.append(msg)


def dos2unix_file(src, dst, fix_inf=False):
    raw = open(src, "rb").read().replace(b"\r\n", b"\n")
    if fix_inf:
        raw = raw.replace(b"-1.#INF000e+000", b"           -INF")
    open(dst, "wb").write(raw)


def head_id(path):
    """读文件头行第1字段的 id (int)"""
    with open(path, "rb") as f:
        line = f.readline().decode("ascii", "replace")
    return int(float(line[0:15]))


def head_type(path):
    with open(path, "rb") as f:
        line = f.readline().decode("ascii", "replace")
    return line[15:30]


def drop_degenerate_groups(path):
    """删除 mgo 文件中 f1==f2 的退化子表 (1D load_table_multi 遇 fmax==fmin
    会误判多群表结束, 导致后续群被静默丢弃。2026-08-10 Ne 实例)"""
    lines = open(path).read().split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    out = []
    i = n_drop = 0
    while i < len(lines):
        head = lines[i]
        if len(head) != 60:
            out.extend(lines[i:])
            break
        nr = int(float(head[30:45])); nt = int(float(head[45:60]))
        f1f2 = lines[i + 1]
        f1, f2 = float(f1f2[0:15]), float(f1f2[15:30])
        nlines = (nr + nt + nr * nt + 3) // 4
        if f2 - f1 <= 0:
            n_drop += 1
        else:
            out.extend(lines[i: i + 2 + nlines])
        i += 2 + nlines
    if n_drop:
        open(path, "w").write("\n".join(out) + "\n")
        log(f"  (删除 {n_drop} 个退化子表 f1==f2)")


# ---------------------------------------------------------------- EOS 转换
def fix_missing_e_fields(src):
    """修复 Fortran 省略 'e' 的 3 位指数格式 (如 ' 8.33534443-110' → e-110)。
    返回修复后的临时文件路径。"""
    raw = open(src, "rb").read().replace(b"\r\n", b"\n").decode("ascii", "replace")
    out_lines = []
    fixed = 0
    for line in raw.split("\n"):
        chars = list(line)
        for i in range(len(line) // 15):
            seg = "".join(chars[15 * i:15 * (i + 1)])
            s = seg.strip()
            if not s:
                continue
            try:
                float(s)
            except ValueError:
                # 在最后一个 +/- 号前插 'e' (指数省略 e 的 Fortran 格式)
                import re
                m = re.match(r"^([+-]?\d+\.?\d*)([+-]\d+)$", s)
                if m:
                    new = f"{m.group(1)}e{m.group(2)}"
                    chars[15 * i:15 * (i + 1)] = f"{new:>15s}"
                    fixed += 1
        out_lines.append("".join(chars))
    tmp = "/tmp/_batch_conv/fixed_" + os.path.basename(src)
    os.makedirs("/tmp/_batch_conv", exist_ok=True)
    open(tmp, "w").write("\n".join(out_lines))
    if fixed:
        log(f"  (修复缺e指数字段 {fixed} 个)")
    return tmp


def convert_eos_hyades(src, dst_total):
    """hyades 文件 → MULTI 总 IEOS (经 EOS-tools RT→RE, 自适应网格)"""
    src = fix_missing_e_fields(src)
    NR, NT, rho, TkeV, P, E = hyades_reader.read_hyades_eos(src)
    rho = np.array(rho, dtype=float)
    T_ev = np.array(TkeV, dtype=float) * 1000.0
    P_mpa = np.array(P, dtype=float) * 1e-7      # dyne/cm2 → MPa (1 MPa = 1e7 dyn/cm2)
    E_jpg = np.array(E, dtype=float) / 1e4       # erg/g → J/g (1 J/g = 1e4 erg/g)
    ds = EOSDataset(rho_gcc=rho, temp_ev=T_ev,
                    ion_pressure_mpa=P_mpa, electron_pressure_mpa=P_mpa,
                    ion_energy_jpg=E_jpg, electron_energy_jpg=E_jpg,
                    mean_ionization=np.zeros((NR, NT)),
                    metadata=EOSMetadata(source_format="hyades", atom_a=1.0, atom_z=1))
    tmp_prefix = "/tmp/_batch_conv/out"
    os.makedirs("/tmp/_batch_conv", exist_ok=True)
    outs = multi_fmt.save(ds, output_prefix=tmp_prefix, energy_points=128,
                          adaptive_energy_grid=True, write_opacity=False)
    shutil.copy(outs["electron"], dst_total)


def convert_eos_copy(src, dst_total):
    dos2unix_file(src, dst_total)


def make_1d_eos(total_file, A, e_out, i_out, e_id, i_id):
    fid, r, de, e0, p_f, t_f = read_ieos(total_file)
    de_c, e0_c, p_c, t_c = de * E12, e0 * E12, p_f * E12, t_f / EV_K
    p_e, t_e = split_electron(r, de_c, p_c, t_c, A)
    e0_i, p_i, t_i = make_ion_ideal(r, de_c, A)
    write_ieos(e_out, e_id, r, de_c / E12, e0_c / E12, p_e / E12, t_e * EV_K)
    write_ieos(i_out, i_id, r, de_c / E12, e0_i / E12, p_i / E12, t_i * EV_K)


def elem_ids(Z):
    """电子/离子表 id (与 Ti 一致: int(Z)*1e6+304/305; 分数 Z 用 round(Z*100)*1e4)"""
    if abs(Z - round(Z)) < 1e-6:
        return int(round(Z)) * 1000000 + 304, int(round(Z)) * 1000000 + 305
    return int(round(Z * 100)) * 10000 + 304, int(round(Z * 100)) * 10000 + 305


# ---------------------------------------------------------------- 算例生成
CASE_TEMPLATE = """!-----------------------------------------------------------------------------+
!  {name}Check - material migration validation case (auto-generated)
!  Planar {name} slab driven by a constant 100 eV radiation bath, 1 ns.
!-----------------------------------------------------------------------------+
&parameters
   igeo        = 1,
   xmin        = 0.,
   texit       = 1.2e-9,
   nfuel       = 0,
   iright      = 0,
   ileft       = 0,
   alphal      = 0.,
   alphar      = 0.,
   betal       = 0.,
   betar       = 1.,
   itype       = 2,
   tau         = 1.e-9,
   trad        = 100.,
   iradia      = 1,
   ihydro      = 1,
   iheation    = 0,
   model       = 0,
   fheat       = 8.0,
   fei         = 2.0,
   flaser      = 26.0,
   zmin        = 0.1,
   flf         = 0.1,
   inegpre     = 0,
   nsplit      = 5,
   dtmin       = 0,
   dtmax       = 1e-11,
   dtinit      = 1e-11,
   dtrvar      = 0.9,
   dttevar     = 1e12,
   dttivar     = 1e12,
   dtbreak     = 2.,
   dtfactor    = 2.,
   nexit       = 100000,
   iwctrl      = 1,
   dt_aout     = 0.3e-9,
   ns_aout     = 1000000,
   dt_bout     = 1e-11,
   ns_bout     = 1,
   irad_left   = 1,
   irad_right  = 21,
   nreduce     = 1,
/
&layer
   nc          = 20,
   thick       = 2.0e-4,
   r0          = {rho0},
   te0         = 0.03,
   ti0         = 0.03,
   zonpar      = 1.0,
   material    = '{name}',
/
&material
   name        = '{name}',
   zi          = {Z},
   ai          = {A},
   eeos_id     = {e_id},
   eeos_file   = 'tables/{name}_eos_e',
   ieos_id     = {i_id},
   ieos_file   = 'tables/{name}_eos_i',
   z_id        = {z_id},
{z_file_line}   planck_id   = {p_id},
   planck_file = 'tables/{planck_file}',
   ross_id     = {r_id},
   ross_file   = 'tables/{ross_file}',
   eps_id      = -1,
/
"""


def make_case(name, A, Z, rho0, e_id, i_id, z_id, z_file, p_id, planck_file, r_id, ross_file):
    d = f"{CASES}/{name}Check"
    os.makedirs(d, exist_ok=True)
    z_file_line = f"   z_file      = 'tables/{z_file}',\n" if z_id >= 0 else ""
    with open(f"{d}/data.in", "w") as f:
        f.write(CASE_TEMPLATE.format(name=name, A=A, Z=Z, rho0=rho0,
                                     e_id=e_id, i_id=i_id, z_id=z_id,
                                     z_file_line=z_file_line,
                                     p_id=p_id, planck_file=planck_file,
                                     r_id=r_id, ross_file=ross_file))
    shutil.copy(f"{CASES}/TiCheck/RUN", f"{d}/RUN")
    shutil.copy(f"{CASES}/TiCheck/CLEAR", f"{d}/CLEAR")
    with open(f"{d}/FILELIST", "w") as f:
        f.write("FILELIST\ndata.in\nRUN\nCLEAR\n*.png\n")
    os.chmod(f"{d}/RUN", 0o755)
    os.chmod(f"{d}/CLEAR", 0o755)


def write_modinfo(moddir, name, note):
    with open(f"{moddir}/MODINFO", "w") as f:
        f.write(f"name=mat_{name}-1.0\nauthor=migration (Multi_BACK)\n"
                f"info={note}\nparent=none\ncdate=Mon Aug 10 2026\nldate=Mon Aug 10 2026\n")


# ---------------------------------------------------------------- 主流程
def migrate_full(name, A, Z, rho0, eos_src, thermos_sym):
    log(f"\n===== {name} (full) =====")
    moddir = f"{MULTI}/r94/mat_{name}-1.0"
    os.makedirs(moddir, exist_ok=True)
    total = f"{moddir}/{name}_eos"
    # 1. 总 EOS
    if eos_src.endswith(".dat") and "hyades" in eos_src:
        convert_eos_hyades(eos_src, total)
        src_kind = "hyades"
    else:
        convert_eos_copy(eos_src, total)
        src_kind = "copy"
    # 2. 拆分 1D 表
    e_id, i_id = elem_ids(Z)
    e_out, i_out = f"{TABLES}/{name}_eos_e", f"{TABLES}/{name}_eos_i"
    make_1d_eos(total, A, e_out, i_out, e_id, i_id)
    # 3. Thermos 不透明度 + Zeff
    files = {}
    for kind, suffix in [("planck", "Planck"), ("ross", "Rosseland"), ("zeff", "Zeff")]:
        src = f"{THERMOS}/mat_{thermos_sym}/{thermos_sym}_{suffix}.dat"
        dst = f"{TABLES}/{name}_Thermos.{suffix.upper() if suffix!='Zeff' else 'ZEFF'}"
        dos2unix_file(src, dst, fix_inf=True)
        if kind in ("planck", "ross"):
            drop_degenerate_groups(dst)
        files[kind] = dst
    p_id, r_id, z_id = head_id(files["planck"]), head_id(files["ross"]), head_id(files["zeff"])
    zt = head_type(files["zeff"])
    z_ok = zt in (" 0.60000000E+01", " 0.60000000e+01")
    # 4. 格式验证
    all_files = [total, e_out, i_out, files["planck"], files["ross"], files["zeff"]]
    for fp in all_files:
        load_opacity_strict(fp) if "Thermos" in fp else None
    result = subprocess.run(["python3", f"{MULTI}/work/eos_opacity_tools/check_multi_file.py"]
                            + all_files, capture_output=True, text=True)
    ok = result.returncode == 0
    log(f"  EOS源={src_kind}, ids: e={e_id} i={i_id} planck={p_id} ross={r_id} z={z_id}"
        f" ztype_ok={z_ok} 格式验证={'PASS' if ok else 'FAIL'}")
    if not ok:
        log(result.stdout[-800:])
    # 5. 算例
    make_case(name, A, Z, rho0, e_id, i_id, z_id if z_ok else -1,
              os.path.basename(files["zeff"]), p_id, os.path.basename(files["planck"]),
              r_id, os.path.basename(files["ross"]))
    write_modinfo(moddir, name, f"{name} EOS (migrated, src={src_kind}); 1D tables + Thermos opacities")
    return ok


def migrate_celia(name, A, Z, rho0, eos_src, opa_prefix, zeff_file):
    log(f"\n===== {name} (celia) =====")
    moddir = f"{MULTI}/r94/mat_{name}-1.0"
    os.makedirs(moddir, exist_ok=True)
    total = f"{moddir}/{name}_eos"
    if "hyades" in eos_src:
        convert_eos_hyades(eos_src, total)
    else:
        convert_eos_copy(eos_src, total)
    e_id, i_id = elem_ids(Z)
    e_out, i_out = f"{TABLES}/{name}_eos_e", f"{TABLES}/{name}_eos_i"
    make_1d_eos(total, A, e_out, i_out, e_id, i_id)
    p_dst = f"{TABLES}/{name}_CELIA.PLANCK"
    r_dst = f"{TABLES}/{name}_CELIA.ROSS"
    z_dst = f"{TABLES}/{name}_CELIA.ZEFF"
    dos2unix_file(f"{CELIA}/{opa_prefix}.PLANCK", p_dst)
    dos2unix_file(f"{CELIA}/{opa_prefix}.ROSS", r_dst)
    dos2unix_file(f"{CELIA}/{zeff_file}", z_dst)
    p_id, r_id, z_id = head_id(p_dst), head_id(r_dst), head_id(z_dst)
    all_files = [total, e_out, i_out, p_dst, r_dst, z_dst]
    result = subprocess.run(["python3", f"{MULTI}/work/eos_opacity_tools/check_multi_file.py"]
                            + all_files, capture_output=True, text=True)
    ok = result.returncode == 0
    log(f"  ids: e={e_id} i={i_id} planck={p_id} ross={r_id} z={z_id} 格式验证={'PASS' if ok else 'FAIL'}")
    if not ok:
        log(result.stdout[-800:])
    make_case(name, A, Z, rho0, e_id, i_id, z_id, os.path.basename(z_dst),
              p_id, os.path.basename(p_dst), r_id, os.path.basename(r_dst))
    write_modinfo(moddir, name, f"{name} EOS (migrated from CELIA); CELIA multigroup opacities")
    return ok


def migrate_eos_only(name, A, Z, rho0, eos_src):
    log(f"\n===== {name} (eos_only) =====")
    moddir = f"{MULTI}/r94/mat_{name}-1.0"
    os.makedirs(moddir, exist_ok=True)
    total = f"{moddir}/{name}_eos"
    convert_eos_hyades(eos_src, total)
    result = subprocess.run(["python3", f"{MULTI}/work/eos_opacity_tools/check_multi_file.py", total],
                            capture_output=True, text=True)
    ok = result.returncode == 0
    log(f"  格式验证={'PASS' if ok else 'FAIL'}")
    if not ok:
        log(result.stdout[-500:])
    write_modinfo(moddir, name, f"{name} EOS only (migrated from hyades); no opacity")
    return ok


def main():
    sel = sys.argv[1:]
    results = {}
    for name, A, Z, rho0, eos, tsym in BATCH_FULL:
        if sel and name not in sel:
            continue
        try:
            results[name] = migrate_full(name, A, Z, rho0, eos, tsym)
        except Exception as e:
            log(f"  !! 异常: {type(e).__name__}: {e}")
            results[name] = False
    for name, A, Z, rho0, eos, opre, zf in BATCH_CELIA:
        if sel and name not in sel:
            continue
        try:
            results[name] = migrate_celia(name, A, Z, rho0, eos, opre, zf)
        except Exception as e:
            log(f"  !! 异常: {type(e).__name__}: {e}")
            results[name] = False
    for name, A, Z, rho0, eos in BATCH_EOS_ONLY:
        if sel and name not in sel:
            continue
        try:
            results[name] = migrate_eos_only(name, A, Z, rho0, eos)
        except Exception as e:
            log(f"  !! 异常: {type(e).__name__}: {e}")
            results[name] = False
    log("\n\n===== 汇总 =====")
    npass = sum(1 for v in results.values() if v)
    for k, v in results.items():
        log(f"  {'PASS' if v else 'FAIL'}  {k}")
    log(f"通过 {npass}/{len(results)}")


if __name__ == "__main__":
    main()
