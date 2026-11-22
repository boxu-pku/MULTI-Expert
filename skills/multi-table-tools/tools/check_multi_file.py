#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_multi_file.py — 验证一个文件能否被 MULTI-2D.2026.3 的
Mat2013_LoadMF 严格解析（IEOS / mgo / sgo 三类表均可）。

严格复现 r94/matter-3.1/Mat2013_LoadMF.r 的 C 语义:
  - 表头恰好 60 字符 = 4 个 15 字符字段 (id, type, NR, NT/NE)
  - 数据 15 字符定宽、每行最多 4 值、跨节连续打包
  - mgo 表第二行为群边界 f1,f2
  - '-INF'→-40, 'NAN'→0

用法:
  python3 check_multi_file.py <文件> [文件2 ...]
退出码: 0=全部通过, 1=有失败
"""
import sys
import os

MGO_TYPES = ["ROSSELAND M    ", "PLANCK M       ", "EPS M          "]
SGO_TYPES = ["PLANCK 1       ", " 0.70000000E+01",
             "ROSSELAND 1    ", " 0.40000000E+01",
             "EPS 1          ", " 7.00000000e+00",
             " 4.00000000e+00", " 6.00000000e+00",
             " 0.60000000E+01"]


class CStrictParser:
    """严格复现 Mat2013_LoadMF 内嵌 C 代码的 getc 行读取语义（CR 保留在行内）"""

    def __init__(self, path):
        self.data = open(path, "rb").read()
        self.off = 0
        self.pos = 4
        self.line = b""
        self.nchars = 0

    def get_line(self):
        if self.off >= len(self.data):
            return 0
        end = self.data.find(b"\n", self.off)
        if end < 0:
            self.line = self.data[self.off:]
            self.off = len(self.data)
        else:
            self.line = self.data[self.off:end]
            self.off = end + 1
        if len(self.line) >= 1024:
            return 2
        self.nchars = len(self.line)
        return 1

    def read_line(self):
        code = self.get_line()
        self.pos = 4
        return self.line if code == 1 else code

    def read_vector(self, n):
        import numpy as np
        v = np.zeros(n)
        for i in range(n):
            if self.pos == 4:
                if self.get_line() != 1:
                    raise ValueError("unexpected EOF")
                self.pos = 0
            if self.pos * 15 > self.nchars:
                raise ValueError("line too short")
            field = self.line[self.pos * 15: self.pos * 15 + 15].decode("ascii", "replace")
            f = field.strip()
            if f == "-INF":
                v[i] = -40.0
            elif f == "NAN":
                v[i] = 0.0
            else:
                v[i] = float(f)
            self.pos += 1
        return v


def check(path):
    p = CStrictParser(path)
    tables = []
    while True:
        a = p.read_line()
        if isinstance(a, int):
            break
        if len(a) != 60:
            raise ValueError(f"表{len(tables)+1}: 头行长度={len(a)} != 60")
        fid = a[0:15].decode("ascii", "replace").strip()
        ftype = a[15:30].decode("ascii", "replace")
        n3 = int(float(a[30:45]))
        n4 = int(float(a[45:60]))
        if ftype in MGO_TYPES:
            l2 = p.read_line()
            if isinstance(l2, int) or len(l2) < 30:
                raise ValueError(f"表{len(tables)+1}: mgo 群边界行过短")
            f1, f2 = float(l2[0:15]), float(l2[15:30])
            p.read_vector(n3); p.read_vector(n4); p.read_vector(n3 * n4)
            tables.append(f"mgo[{ftype.strip()}] {n3}x{n4} 群[{f1:g}~{f2:g}]eV id={fid}")
        elif ftype in SGO_TYPES:
            p.read_vector(n3); p.read_vector(n4); p.read_vector(n3 * n4)
            tables.append(f"sgo[type={ftype.strip()}] {n3}x{n4} id={fid}")
        else:
            # IEOS 分支: r[NR] de[NE] e0[NR] p[NR*NE] t[NR*NE]
            p.read_vector(n3); p.read_vector(n4); p.read_vector(n3)
            p.read_vector(n3 * n4); p.read_vector(n3 * n4)
            tables.append(f"IEOS NR={n3} NE={n4} id={fid}")
    return tables


def main():
    ok_all = True
    for path in sys.argv[1:]:
        try:
            tables = check(path)
            print(f"✓ {path}  ({len(tables)} 个子表)")
            for t in tables[:5]:
                print(f"    {t}")
            if len(tables) > 5:
                print(f"    ... 其余 {len(tables)-5} 个子表同格式")
        except Exception as e:
            ok_all = False
            print(f"✗ {path}\n    {type(e).__name__}: {e}")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
