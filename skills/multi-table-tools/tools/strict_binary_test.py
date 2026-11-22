# -*- coding: utf-8 -*-
"""用二进制模式严格复现 C getc() 行为: \\r 保留在行内"""
import os

class CStrictParser:
    """严格复现 Mat2013_LoadMF.r 内嵌 C 代码的 getc 行读取语义"""
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
            self.line = self.data[self.off:end]   # 不含 \n, 但保留 \r
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
            field = self.line[self.pos*15 : self.pos*15+15].decode("ascii", "replace")
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
        a = self.read_line()
        assert isinstance(a, bytes), f"head read failed: {a}"
        assert len(a) == 60, f"head line size != 60 (got {len(a)})"
        nr = int(float(a[30:45]))
        ne = int(float(a[45:60]))
        r = self.read_vector(nr)
        de = self.read_vector(ne)
        e0 = self.read_vector(nr)
        p = self.read_vector(nr * ne)
        t = self.read_vector(nr * ne)
        return dict(nr=nr, ne=ne, r=r, de=de, e0=e0, p=p, t=t)


if __name__ == "__main__":
    B = "/home/ubuntu/local/newmulti/Multi_BACK/matter++"
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
    print(f"{'文件':42s}  真实C语义(Linux MULTI)解析结果")
    print("-" * 80)
    for rel in CANDIDATES:
        path = os.path.join(B, rel)
        try:
            res = CStrictParser(path).load_ieos()
            print(f"{rel:42s}  ✓ 成功 NR={res['nr']} NE={res['ne']}")
        except Exception as e:
            print(f"{rel:42s}  ✗ {e}")
