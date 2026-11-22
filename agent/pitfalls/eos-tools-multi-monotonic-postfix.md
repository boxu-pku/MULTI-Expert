---
title: "EOS-tools MULTI 产物缺 P(ρ) 单调修复（低 de 列 van der Waals 凹陷，入库前须后处理）"
category: 文件格式
severity: 警告（能跑但结果错）
first_seen: 2026-08-31
last_verified: 2026-08-31
verifier: claude
status: stable
tags:
  - eos-tools
  - multi-format
  - monotonicity
  - cold-curve
  - postfix
source_anchors:
  - EOS-tools eoslib/formats/multi.py:L1354-L1440
  - MULTI-IFE-2015 m150304.f95:L2872
---

# EOS-tools MULTI 产物缺 P(ρ) 单调修复

> 触发材料：DTFEOS；关联：[[feos-converter-layout-energyunit]]（FEOS 侧同一坑 P-03）、
> [[eos-tools-feos-isotope-duplicate-z]]

## 现象

`check_multi_file.py` 通过、算例正常跑完，但固定 de 列沿 ρ 的 **P(ρ) 非单调**
（DT 实例：电子 28/96 列、离子 6/96 列，全部集中在 de≤10.6 MJ/kg 低能列）。
MULTI 加载时只把 P 钳为非负（`m150304.f95:L2872` `m%eeos%p = max(m%eeos%p,0.d0)`），
**单调性仍然破**——低能区（冷态附近）双线性查表得到非物理 P。

## 原因

EOS-tools `_build_multi_component`（`eoslib/formats/multi.py:L1354-1440`）只保证
**每条 ρ 行上能量单调**（longest monotonic segment + RT→RE 插值），不做固定 de
列沿 ρ 的单调化。FEOS TF 冷曲线在 ρ<ρ_solid 有 van der Waals 型负压凹陷
（未开软球修正时），低 de 列继承该凹陷。根因分类：**工具行为差异**——
FEOS 侧老转换器 feos2multi.py 有 `np.maximum.accumulate` 修复（FEOS 侧 P-03），
EOS-tools 没有实现这一步。

## 修复 / 预防

EOS-tools 转出的 MULTI 表**入库前**必须补 per-de 列单调化：

```python
# f(rho_i, de_j) = block[j*nr + i]；沿每列累取最大
P = p_block.reshape(ne, nr)
for j in range(ne):
    P[j] = np.maximum.accumulate(P[j])
```

现成脚本：`$MULTI_LIBS/FEOS/FEOS/EOS-Data/DT/fix_multi_monotonic.py`
（读入→修→按"全块 concatenate 后 4 值/行"契约写回，同时满足
[[multi-table-continuous-stream-format]]）。

DTFEOS 实测：修复后 0 列非单调；与源 `DT.data.txt` 交叉对拍不变
（P 中位 0.02–0.03%）；`check_multi_file.py` 仍全 ✓。

## 检验清单（EOS-tools MULTI 产物入库三步）

1. P(ρ) 单调后处理（本条）
2. 表头 ID 按房子惯例改写（EOS-tools 写 ID=1；FEOS 系材料用
   matnum×10⁴+304/305，如 DTFEOS_eos_e=52710304）
3. `check_multi_file.py` + 与源表在 T(rho,de) 处交叉对拍（绝对值，防单位错——
   L-001/L-008 教训：能量守恒查不出单位错）
