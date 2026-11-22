# -*- coding: utf-8 -*-
"""
严格复现 Mat2013_LoadMF 的 mgo/sgo 分支(二进制、C getc 语义), 批量检测不透明度文件。
"""
import os, sys
sys.path.insert(0, "/tmp")
from strict_binary_test import CStrictParser

MGO_TYPES = ["ROSSELAND M    ", "PLANCK M       ", "EPS M          "]
SGO_TYPES = ["PLANCK 1       ", " 0.70000000E+01",
             "ROSSELAND 1    ", " 0.40000000E+01",
             "EPS 1          ", " 7.00000000e+00",
             " 4.00000000e+00", " 6.00000000e+00",
             " 0.60000000E+01"]

def load_opacity_strict(path):
    """复现 load_subsection 的 mgo/sgo 分支; 返回 (class, type, NR, NT, n_tables)"""
    p = CStrictParser(path)
    tables = 0
    kinds = []
    while True:
        a = p.read_line()
        if isinstance(a, int):
            break  # EOF
        if len(a) != 60:
            raise ValueError(f"head line size != 60 (got {len(a)}) @table{tables+1}")
        fid = a[0:15].decode("ascii", "replace")
        ftype = a[15:30].decode("ascii", "replace")
        if ftype in MGO_TYPES:
            nr = int(float(a[30:45])); nt = int(float(a[45:60]))
            l2 = p.read_line()
            if isinstance(l2, int) or len(l2) < 30:
                raise ValueError("bad 2nd line of multigroup opacity")
            f1 = float(l2[0:15]); f2 = float(l2[15:30])
            r = p.read_vector(nr); t = p.read_vector(nt); o = p.read_vector(nr * nt)
            kinds.append(("mgo", ftype.strip(), nr, nt, f1, f2))
        elif ftype in SGO_TYPES:
            nr = int(float(a[30:45])); nt = int(float(a[45:60]))
            r = p.read_vector(nr); t = p.read_vector(nt); o = p.read_vector(nr * nt)
            kinds.append(("sgo", ftype.strip(), nr, nt, None, None))
        else:
            raise ValueError(f"unknown table type: '{ftype}'")
        tables += 1
    return kinds


if __name__ == "__main__":
    B = "/home/ubuntu/local/newmulti/Multi_BACK/matter++"
    FILES = [
        # (路径, 说明)
        ("Thermos/mat_Au/Au_Rosseland.dat", "Thermos Au Rosseland"),
        ("Thermos/mat_Au/Au_Planck.dat", "Thermos Au Planck"),
        ("Thermos/mat_Au/Au_Zeff.dat", "Thermos Au Zeff"),
        ("Thermos/mat_W/W_Planck_Fine.dat", "Thermos W Planck 细网格"),
        ("mat_CELIA/C_20G.PLANCK", "CELIA C 20群"),
        ("mat_CELIA/C_100G.PLANCK", "CELIA C 100群"),
        ("mat_CELIA/DT" , None),  # 占位忽略
        ("mat_CELIA/D_20G.ROSS", "CELIA D 20群 Ross"),
        ("mat_CELIA/C.ZEFF", "CELIA C Zeff"),
        ("mat_Ti/SNOP_LTE.PLANCK", "Ti SNOP LTE 20群"),
        ("mat_Ti/SNOP_NLTE.EPS", "Ti SNOP NLTE EPS"),
        ("mat_Ti/SNOP_NLTE.ZEFF", "Ti SNOP NLTE ZEFF"),
        ("mat_Ti/Ti_Planck", "Ti_Planck"),
        ("mat_Au-1.0/SNOP.PLANCK", "Au SNOP"),
        ("mat_Au-1.0/SNOP.EPS", "Au SNOP EPS"),
        ("mat_Au-1.0/Au100PLANCK", "Au 100群"),
        ("mat_Au-1.0/AU_WorkOp_Ross", "Au WorkOp Ross (sgo)"),
        ("mat_Au-1.0/AU_SIMPLE_PLANCK_MG", "Au SIMPLE_MG"),
        ("mat_He/SNOP.ROSS", "He SNOP Ross"),
        ("mat_Be-1.0/Be_40G.PLANCK", "Be 40群"),
        ("mat_Be-1.0/opbe.Planck", "opbe.Planck"),
        ("mat_Be-1.0/BE_PLANCKx03", "BE_PLANCKx03"),
        ("mat_C-1.0/C_20GSNOP.PLANCK", "C 20G SNOP"),
        ("mat_C-1.0/C.ZEFF", "C Zeff"),
        ("mat_C-1.0/C_SIMPLE_PLANCK", "C SIMPLE (sgo)"),
        ("mat_CPC/AU_WorkOp_Ross", "CPC AU_WorkOp"),
        ("C_SNOPMPQeos/SNOP.PLANCK", "C SNOPMPQeos"),
        ("mat_Al-1.0/1041_PLANCK", "Al 1041"),
        ("mat_Al-1.0/Al_PLANCK_multifs-1.2.dat", "Al multifs"),
        ("mat_Al-1.0/AL_SIMPLE_PLANCK", "Al SIMPLE"),
        # MULTI-2D.2026.3 自带参考
        ("/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_Au-1.0/AU_op03p", "2026.3 AU_op03p"),
        ("/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_Au-1.0/AU_op03z", "2026.3 AU_op03z"),
    ]
    print(f"{'文件':44s} {'行尾':4s}  严格解析结果")
    print("-" * 100)
    for rel, desc in FILES:
        path = rel if rel.startswith("/") else os.path.join(B, rel)
        if not os.path.exists(path):
            continue
        raw = open(path, "rb").read()
        crlf = b"\r\n" in raw[:400]
        # 原始解析
        try:
            kinds = load_opacity_strict(path)
            ng = len(kinds)
            k0 = kinds[0]
            res = f"✓ {k0[0]} '{k0[1]}' NR={k0[2]} NT={k0[3]} 子表数={ng}"
            if k0[0] == "mgo":
                res += f" 群边界[{k0[4]:g}~{kinds[-1][5]:g}]eV"
        except Exception as e:
            res = f"✗ {e}"
        print(f"{os.path.basename(path):44s} {'CRLF' if crlf else 'LF':4s}  {res}")
