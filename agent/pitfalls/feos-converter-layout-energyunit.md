# FEOS 转换器（feos2multi/feos2r94）布局与能量单位双 bug

**日期**：2026-08-13
**状态**：已确认（入库前已修复本库产物；上游 FEOS 项目代码未动）

## 症状

用 FEOS 项目 `$MULTI_LIBS/FEOS/FEOS/EOS-Data/feos2multi.py`、`feos2r94.py`
转换的 IEOS 表，在 MULTI 中表现出：(1) 任一 (ρ,T) 求值得到振荡的垃圾 P/T；
(2) 即使修正后 RH 能量方程无解（表观"冷曲线过刚"）。

## 根因（两个独立 bug）

1. **布局 bug**：两个转换器都按 `p_out[i*ne_out:(i+1)*ne_out]`（密度主序
   rho-major）填充 p/t 数组，而 MULTI IEOS 要求**能量主序** `p[j*NR+i]`
   （1D 源码 `eosbin`：`zt(ix-1+(iy-2)*nx)`，ix=密度索引，iy=能量索引；
   `nr≠ne` 时两者不等价）。直接后果：按能量主序读入后，同一能量行的数据
   来自不同密度行，P/T 逐点乱跳。
2. **能量单位 ×100**：转换器 docstring 与 FEOS AGENTS.md 均声称
   "MJ/kg = 1e12 erg/g"，实际 **1 MJ/kg = 1e10 erg/g**（1 J=1e7 erg，
   1 MJ/kg=1e6 J/1e3 g=1e10 erg/g）。MULTI IEOS 的 de/e0 按 `×1e12→erg/g`
   读取（1D `load_table_eos`），即单位为 1e12 erg/g = **100 MJ/kg**。
   转换器把 MJ/kg 数值直接写入 → 能量放大 100 倍 → RH 能量预算永远超支，
   表观"没有 Hugoniot 解"。

## 修复（本库已执行）

对转换产物：
1. p/t 块 reshape 成 (NR,NE) 后**转置**为 (NE,NR) 重写；
2. **de、e0 全部 ÷100**。

修复后基准对照：由表反解主 Hugoniot 与 FEOS 官方 `.hug` 对比
**P≤2.7%、Us≤1.9%**（见 `Hugoniot校验流程.md` §五）。

## 影响范围与警示

- FEOS 项目自己的 hBN/Al/H2O 转换产物（`hBN_feosele.*` 等）**带同样两个 bug**，
  未重新验证前勿在 MULTI 中使用；
- **2026-08-14 起，FEOS→MULTI 一律优先走 EOS-tools**
  （`eos_convert.py --from feos --to multi`，无此二 bug，且 192×512 细网格、
  基准对照 Us≤1.3% 优于修复版 feos2r94 的 1.9%）；
  feos2r94 仅用于 2D 单温总表（EOS-tools 不出该格式），且必须做上述两步修复；
- 若今后更新上游转换器后重转，务必重做 `check_multi_file.py` + 任取一 (ρ,T)
  点与 FEOS `SinglePoint` 对拍 + RH 基准对照。

## 相关

[[ieos-layout-order]]（能量主序 vs numpy 默认行主序的总纲）
