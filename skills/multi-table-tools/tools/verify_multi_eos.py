# -*- coding: utf-8 -*-
"""
交叉验证：严格复现 MULTI-2D 的 Mat2013_LoadMF 解析语义，
与 EOS-tools 的 read_multiEOS 解析结果对比。
"""
import sys, os
sys.path.insert(0, "/home/ubuntu/local/EOS_converter_xubo/EOS-tools")

import numpy as np
import basefunctions.read_multi as eostools_reader


# ============================================================
# 严格复现 MULTI r94/matter-3.1/Mat2013_LoadMF.r 的 IEOS 解析
# ============================================================
class MultiStrictParser:
    """复现 Mat2013_LoadMF 的 read_vector / read_line 语义"""

    def __init__(self, path):
        self.fd = open(path, "r")
        self.line = None
        self.nchars = 0
        self.pos = 4  # C 代码里 pos 初始为 4，表示需要读新行

    def get_line(self):
        """返回 1=成功, 0=EOF, 2=行超长(>=1024)"""
        self.line = self.fd.readline()
        if self.line == "":
            return 0
        self.line = self.line.rstrip("\n")
        if len(self.line) >= 1024:
            return 2
        self.nchars = len(self.line)
        return 1

    def read_line(self):
        code = self.get_line()
        self.pos = 4
        if code == 1:
            return self.line
        return code  # int: 0 或 2

    def read_vector(self, n):
        v = np.zeros(n)
        for i in range(n):
            if self.pos == 4:
                if self.get_line() != 1:
                    raise ValueError("unexpected EOF")
                self.pos = 0
            if self.pos * 15 > self.nchars:
                raise ValueError("line too short")
            field = self.line[self.pos * 15 : self.pos * 15 + 15]
            field = field.ljust(15)[:15]  # C 里读满15字符(不足处是旧缓冲，这里按空处理)
            f = field.strip()
            if f == "-INF":
                v[i] = -40.0
            elif f == "NAN":
                v[i] = 0.0
            else:
                v[i] = float(f)
            self.pos += 1
        return v

    def load_ieos(self):
        # --- 头部: 必须恰好 60 字符 ---
        a = self.read_line()
        assert isinstance(a, str), f"head read failed: {a}"
        assert len(a) == 60, f"head line size != 60 (got {len(a)})"
        fid = a[0:15]
        ftype = a[15:30]
        # IEOS 分支(else 分支): type 不匹配任何 opacity 类型字符串
        nr = int(float(a[30:45]))
        ne = int(float(a[45:60]))
        r = self.read_vector(nr)
        de = self.read_vector(ne)
        e0 = self.read_vector(nr)
        p = self.read_vector(nr * ne)
        t = self.read_vector(nr * ne)
        return dict(id=fid, type=ftype, nr=nr, ne=ne, r=r, de=de, e0=e0, p=p, t=t)


def compare_file(path):
    print(f"\n{'='*70}\n文件: {path}")
    strict = MultiStrictParser(path).load_ieos()

    # EOS-tools 解析
    eo = eostools_reader.read_multiEOS(path)
    NR, NE, rho, dE, E0, P, T = eo

    assert strict["nr"] == NR and strict["ne"] == NE, \
        f"网格数不一致: strict=({strict['nr']},{strict['ne']}) eostools=({NR},{NE})"

    rho_eo = np.array(rho)
    dE_eo = np.array(dE)
    E0_eo = np.array(E0)
    P_eo = np.array(P).ravel()   # (NE,NR) C序 = E行rho列
    T_eo = np.array(T).ravel()

    checks = [
        ("rho", strict["r"], rho_eo),
        ("DeltaE", strict["de"], dE_eo),
        ("E0", strict["e0"], E0_eo),
        ("P", strict["p"], P_eo),
        ("T", strict["t"], T_eo),
    ]
    allok = True
    for name, a, b in checks:
        if a.shape != b.shape:
            print(f"  {name}: 形状不一致 {a.shape} vs {b.shape}")
            allok = False
            continue
        diff = np.abs(a - b)
        rel = diff / np.maximum(np.abs(a), 1e-300)
        ok = diff.max() == 0.0
        allok &= ok
        print(f"  {name:6s}: 形状{a.shape}, 最大绝对差={diff.max():.3e}, "
              f"最大相对差={rel.max():.3e}, 完全一致={ok}")
    print(f"  ==> {'一致 ✓' if allok else '不一致 ✗'}")

    # 物理量抽查(MULTI 内部单位: cgs)
    e12 = 1e12
    ev = 11604.519
    print(f"  物理抽查: rho范围 {strict['r'].min():.3e}~{strict['r'].max():.3e} g/cc, "
          f"T范围 {strict['t'].min()/ev:.3e}~{strict['t'].max()/ev:.3e} eV, "
          f"P范围 {strict['p'].min()*e12:.3e}~{strict['p'].max()*e12:.3e} dyn/cm2")
    return allok


files = [
    "/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_DT-1.0/DT_EOS",
    "/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_Au-1.0/AU_eos",
    "/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_Al-1.0/AL_eos",
    "/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_Be-1.0/BE_eos",
    "/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_C-1.0/C_EOS",
    "/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_2019/Al_MPQEOS.i301",
    "/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_2019/CHOQG.i301",
    "/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_2019/Fe_MPQEOS.i301",
    "/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_2019/W_MPQEOS.i301",
]

results = {}
for f in files:
    if os.path.exists(f):
        try:
            results[f] = compare_file(f)
        except Exception as exc:
            print(f"\n文件: {f}\n  ==> 解析失败: {exc}")
            results[f] = False
    else:
        print(f"\n文件不存在: {f}")
        results[f] = None

print("\n" + "=" * 70)
print("汇总:")
for f, ok in results.items():
    tag = "✓" if ok else ("✗" if ok is False else "-")
    print(f"  {tag} {os.path.basename(f)}")
