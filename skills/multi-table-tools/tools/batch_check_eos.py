# -*- coding: utf-8 -*-
"""
批量检测 Multi_BACK/matter++ 下所有 IEOS 候选文件:
1. 行尾(CRLF/LF) — MULTI 的 C 解析器遇 CR 会判 "head line size != 60"
2. 用严格模拟 Mat2013_LoadMF 的解析器尝试解析
"""
import sys, os
sys.path.insert(0, "/tmp")
from verify_multi_eos import MultiStrictParser
import numpy as np

CANDIDATES = [
    "mat_Al-1.0/41_ieos", "mat_Al-1.0/42_ieos", "mat_Al-1.0/AL_eos",
    "mat_Al-1.0/AL_LV.INV.data",
    "mat_Al-1.0/Al_ELECTRONEOS_multifs-1.2.dat", "mat_Al-1.0/Al_IONEOS_multifs-1.2.dat",
    "mat_Au-1.0/AU_eos", "mat_Au-1.0/AU_eosd",
    "mat_Be-1.0/BE_eos",
    "mat_C-1.0/511_ieos", "mat_C-1.0/C_EOS", "mat_C-1.0/CH_ieos",
    "mat_CELIA/CH_ieos", "mat_CELIA/DD_ieos", "mat_CELIA/DT_ieos",
    "mat_CPC/AU.INV", "mat_CPC/BE.INV",
    "mat_DT-1.0/DT_EOS",
    "mat_Ti/422_ieos", "mat_Ti/Ti_eos",
    "Thermos/mat_U/U_IdealGas_EOS",
]

B = "/home/ubuntu/local/newmulti/Multi_BACK/matter++"

print(f"{'文件':42s} {'行尾':5s} {'头长':4s} {'NR':>4s} {'NE':>4s}  解析结果")
print("-" * 90)
for rel in CANDIDATES:
    path = os.path.join(B, rel)
    if not os.path.exists(path):
        print(f"{rel:42s} 不存在")
        continue
    with open(path, "rb") as f:
        raw = f.read(200)
    crlf = b"\r\n" in raw
    first_line = raw.split(b"\n")[0]
    # 直接解析(保留CRLF,模拟Linux下MULTI的行为)
    try:
        res = MultiStrictParser(path).load_ieos()
        status = f"直接解析成功(意外!)"
    except AssertionError as e:
        status = f"直接解析失败: {e}"
    except Exception as e:
        status = f"直接解析失败: {type(e).__name__}: {e}"
    print(f"{rel:42s} {'CRLF' if crlf else 'LF':5s} {len(first_line):4d} {'':4s} {'':4s}  {status}")

print()
print("=" * 90)
print("去掉 CR 后重试(模拟 dos2unix 转换):")
print("-" * 90)
for rel in CANDIDATES:
    path = os.path.join(B, rel)
    if not os.path.exists(path):
        continue
    with open(path, "rb") as f:
        raw = f.read()
    clean = raw.replace(b"\r\n", b"\n")
    tmp = "/tmp/_clean_eos.tmp"
    with open(tmp, "wb") as f:
        f.write(clean)
    try:
        res = MultiStrictParser(tmp).load_ieos()
        ev = 11604.519
        tmax = res["t"].max() / ev
        tmin = res["t"].min() / ev
        print(f"{rel:42s} ✓ NR={res['nr']:4d} NE={res['ne']:4d}  "
              f"rho: {res['r'].min():.2e}~{res['r'].max():.2e} g/cc, "
              f"T: {tmin:.1e}~{tmax:.1e} eV")
    except Exception as e:
        print(f"{rel:42s} ✗ {type(e).__name__}: {e}")
