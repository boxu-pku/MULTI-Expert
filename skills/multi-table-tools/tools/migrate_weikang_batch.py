#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_weikang_batch.py — WeiKang 材料的拆分/算例/注释批量处理
(转换好的 r94/mat_X-1.0/X_eos 总表 → 1D 拆分表 + 验证算例)
"""
import os
import sys
import subprocess

sys.path.insert(0, "/home/ubuntu/local/MULTI-2D.2026.3/work/eos_opacity_tools")
from batch_migrate import make_1d_eos, make_case

MULTI = "/home/ubuntu/local/MULTI-2D.2026.3"
TABLES = f"{MULTI}/r94/MULTI-IFE-2015/tables"
CELIA = "/home/ubuntu/local/newmulti/Multi_BACK/matter++/mat_CELIA"

# name: (A_avg 每原子式量, Z_avg 每原子平均, rho0, 不透明度配置, 来源注释)
# 不透明度: ('thermos', 前缀) / ('celia20', None) / ('opc', 文件前缀) / ('ife', (文件,id,id)) / None
MATS = {
    "H_wk":   (1.008, 1.0, 0.0884, ("thermos", "H"), "刘兴博士论文附录A.1(北大), FPMD, rho0.002-1000, T1-5000eV"),
    "C_wk":   (12.011, 6.0, 3.51, ("celia20", None), "刘兴附录A.2, DFT(G/D构型), rho1.8-100, T0.09-1393eV"),
    "C8H8_wk": (6.51, 3.5, 1.05, ("opc", "PS"), "刘兴附录A.3, E基点-1052.64eV/CH, rho1.05-12.6"),
    "C9H10_wk": (6.22, 3.37, 1.0667, None, "刘兴附录A.4, 聚α-甲基苯乙烯, E基点-9489.74eV/C9H10"),
    "CH2_wk": (4.676, 2.667, 0.954, ("opc", "PE"), "刘兴附录A.5, 聚乙烯, E基点-1068.84eV/CH2; 收编multi格式半成品(已修头/CRLF并核对源表)"),
    "Fe_wk":  (55.845, 26.0, 7.874, ("thermos", "Fe"), "刘兴附录A.6, 仅压缩态rho11.8-66.7,T1-10000eV; 收编半成品(已核对)"),
    "Be_wk":  (9.012, 4.0, 1.845, ("ife", None), "高畅表4.1, ext-FPMD, 仅19点稀疏"),
    "Si_wk":  (28.085, 14.0, 2.329, ("thermos", "Si"), "高畅表4.2 PBE泛函, rho2.33-18.6,T1e4K-1.29e8K"),
    "BN_wk":  (12.41, 6.0, 3.487, None, "杨雨桐附录A.1, 氮化硼, E Ry/BN, P KBar, 6rho×11T"),
    "Pb_wk":  (207.2, 82.0, 11.34, ("thermos", "Pb"), "杨雨桐附录A.2, 仅压缩态rho28-74"),
    "LiF_wk": (12.97, 6.0, 2.635, None, "张肖涵表A.1+A.2拼接(E平移对齐1908.3eV/LiF), rho0.527-15.8,T0.009-10000eV"),
    "SiO2wk12": (20.03, 10.0, 2.648, ("opc", "Quartz"), "张肖涵表A.3, Si12价电子赝势, T0.5-50eV(低温段)"),
    "SiO2wk14": (20.03, 10.0, 2.648, ("opc", "Quartz"), "张肖涵表A.4, Si14价电子赝势, T20-5000eV(高温段)"),
}


def main():
    # C_wk 的 CELIA C_20G 不透明度复制一份
    for suffix in ["PLANCK", "ROSS", "ZEFF"]:
        src = f"{CELIA}/C_20G.{suffix}" if suffix != "ZEFF" else f"{CELIA}/C.ZEFF"
        dst = f"{TABLES}/C_wk_CELIA.{suffix}"
        raw = open(src, "rb").read().replace(b"\r\n", b"\n")
        open(dst, "wb").write(raw)

    for name, (A, Z, rho0, opa, note) in MATS.items():
        total = f"{MULTI}/r94/mat_{name}-1.0/{name}_eos"
        e_id = int(round(Z)) * 1000000 + 304 if abs(Z - round(Z)) > 1e-6 else int(Z) * 1000000 + 304
        e_id, i_id = e_id, e_id + 1
        # 分数 Z 的 id 约定(与 batch_migrate.elem_ids 一致)
        if abs(Z - round(Z)) > 1e-6:
            e_id = int(round(Z * 100)) * 10000 + 304
            i_id = e_id + 1
        e_out, i_out = f"{TABLES}/{name}_eos_e", f"{TABLES}/{name}_eos_i"
        make_1d_eos(total, A, e_out, i_out, e_id, i_id)

        # 不透明度与算例
        if opa is None:
            print(f"{name}: 拆分完成 (无不透明度, EOS-only)")
            continue
        if opa[0] == "thermos":
            sym = opa[1]
            p_file, p_id = f"{name}_Thermos.PLANCK", 0
            r_file, r_id = f"{name}_Thermos.ROSSELAND", 0
            z_file, z_id = f"{name}_Thermos.ZEFF", 0
            # 直接引用已有全套表(复制命名以清晰)
            for s_new, s_old in [(p_file, f"{sym}_Thermos.PLANCK"),
                                 (r_file, f"{sym}_Thermos.ROSSELAND"),
                                 (z_file, f"{sym}_Thermos.ZEFF")]:
                src = f"{TABLES}/{s_old}"
                if os.path.exists(src):
                    import shutil
                    shutil.copy(src, f"{TABLES}/{s_new}")
        elif opa[0] == "celia20":
            p_file, p_id = "C_wk_CELIA.PLANCK", 10003000
            r_file, r_id = "C_wk_CELIA.ROSS", 10004000
            z_file, z_id = "C_wk_CELIA.ZEFF", 1
        elif opa[0] == "opc":
            base = opa[1]
            p_file, r_file = f"{base}_OPC.PLANCK", f"{base}_OPC.ROSS"
            import re
            head = open(f"{TABLES}/{p_file}", "rb").readline().decode()
            p_id = r_id = int(float(head[0:15]))
            z_file, z_id = None, -1
        elif opa[0] == "ife":
            p_file, p_id = "Be20keV.PLANCK", 20143000
            r_file, r_id = "Be20keV.ROSS", 20144000
            z_file, z_id = None, -1
        make_case(name, A, Z, rho0, e_id, i_id, z_id, z_file, p_id, p_file, r_id, r_file)
        print(f"{name}: 拆分+算例完成 (e_id={e_id}, opa={opa[0]})")

        # MODINFO / README 注释
        moddir = f"{MULTI}/r94/mat_{name}-1.0"
        with open(f"{moddir}/MODINFO", "w") as f:
            f.write(f"name=mat_{name}-1.0\nauthor=migration (WeiKang theses extraction)\n"
                    f"info={note}\nparent=none\ncdate=Tue Aug 11 2026\nldate=Tue Aug 11 2026\n")
        with open(f"{moddir}/README", "w") as f:
            f.write(f"mat_{name}-1.0\n{'='*40}\n来源: {note}\n"
                    f"提取自: /home/ubuntu/local/newmulti/weikang状态方程表_汇总/\n"
                    f"转换: work/eos_opacity_tools/weikang2multi.py (2026-08-11)\n"
                    f"注意: 与库内已有同名材料为不同数据源, 本模块为独立 MID, 未覆盖任何已有材料。\n")


if __name__ == "__main__":
    main()
