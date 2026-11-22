# 外部交接的 MULTI EOS 表：整子表 CRLF 混入（头行 61≠60）

**日期**：2026-10-28（Cawkwell2021 HMX 交接包）
**场景**：外部协作方在 Windows 生成的 MULTI 倒置 EOS 表（双子表
90000304/90000305）

## 现象

`check_multi_file.py` 报 `ValueError: 表2: 头行长度=61 != 60`；
第一子表正常。字节级检查：**第二子表全部 3134 行以 `\r\n` 结尾**
（第一子表为 `\n`），故每条定宽 60 字符记录后多一个 `\r`。

MULTI 按 60 字符定宽读头 `/ (e15.0,a,2e15.8)`，多出的 `\r` 会挤占
后续解析位置 → 读错 id/网格。

## 关键教训

**对方自检脚本可能用自己的宽松解析器（splitlines() 会自动吃掉 \r），
测不出这个问题。** 必须用本仓库的 `check_multi_file.py` 复核；它按
定宽字节读。

## 修复

    python3 - <<'PY'
    p='tables/HMX_eos'
    raw=open(p,'rb').read()
    open(p,'wb').write(raw.replace(b'\r\n',b'\n').replace(b'\r',b'\n'))
    PY
    # 再跑 check_multi_file.py 确认 2 子表、网格单调

（`work/eos_opacity_tools/fix_multi_file.sh` 亦可，但该脚本主要针对
`-1.#INF`/CRLF 混合的旧表，人工确认字节改动更稳。）

**修复后仍要做物理锚点验证**：本次锚点 P(1.88, 298K)=−0.118 GPa、
c_v 与 Hugoniot 均正常，且单层辐射驱动 Hugoniot 实跑与解析线吻合
+0.6~+2.2%，才确认表可用。
