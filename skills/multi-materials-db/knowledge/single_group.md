---
title: 单群 opc 材料明细（21 种，hyades opc 平均表，含借用规则与 ⚠ 标记）
skill: multi-materials-db
category: reference
source_anchors:
  - MULTI-2D_材料库清单.md §1.2
  - work/eos_opacity_tools/migrate_opc_batch.py:L31-L43
  - Multi_BACK_材料不透明度映射表.md §B
doc_ref: "MULTI-2D_材料库清单.md §1.2, §四-3"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 单群
  - opc
  - 借用
  - Diamond
  - Cliquid
---

# 单群 opc 材料明细（21 种）

> **TL;DR**：hyades opc 平均不透明度（(ρ,T) 网格 Rosseland+Planck 平均，非多群）按 Multi_BACK 原生映射（含借用规则）转换为 sgo 单群表（`tables/X_OPC.ROSS/.PLANCK`），2D/1D 灰体均可用，1D 已验证。

## 1. 明细表（清单 §1.2）

| 材料 | EOS 网格 | opc 源 | 材料 | EOS 网格 | opc 源 |
|---|---|---|---|---|---|
| Glass 玻璃 | 43×256 | 1022 | CD2 氘代聚乙烯 | 65×128 | 1344（借C） |
| Quartz 石英 | 75×128 | 1022 | Diamond 金刚石 ⚠ | 93×128 | 1344（借C） |
| Silica 石英砂 | 73×128 | 1022 | Cliquid 液态碳 ⚠ | 48×128 | 1344（借C） |
| PE 聚乙烯 | 65×128 | 1031 | Cphenolic 酚醛 | 56×128 | 1344（借C） |
| PS 聚苯乙烯 | 73×128 | 1032 | LiD 氘化锂 | 94×128 | 1071（借Li） |
| PU 聚氨酯 | 101×512 | 1033 | LiH 氢化锂 | 42×512 | 1071（借Li） |
| Parylene | 71×512 | 1035 | SS 不锈钢 | 73×128 | 1181（借Fe） |
| Mylar | 73×128 | 1036 | Water 水 | 80×128 | 1311 |
| Al2O3 氧化铝 | 68×128 | 1161 | Air 空气 | 21×128 | 1301 |
| WC 碳化钨 | 100×128 | 1121（借W） | Sn 锡 | 68×128 | 1401 |
| Eu 铕 | 70×128 | 1461 | | | |

1D 表文件：`tables/X_OPC.ROSS/.PLANCK`（sgo 格式，id=opc 表号；opc2sgo.py 转换）。
2D opafun：opc 平均 Rosseland 表拟合式（`Material_mig.r`，注释含系数与误差）。
验证算例：对应 `validation_cases/<X>Check/`（机器验收 ACCEPT 18 + CAVEAT 3，2026-08-11）。

## 2. ⚠ 标记材料（清单 §1.2 注）

| 材料 | 现象 | 根因 | 处置建议 |
|---|---|---|---|
| **Diamond** | 能量误差 1.17e-4 超阈值（标准 <1e-6） | 源 EOS 表密度下限 0.35 g/cc 过高，烧蚀稀薄区越界 | 非烧蚀/ρ 不低于下限的算例可用；或换更宽 EOS 源；见 `agent/pitfalls/eos-density-range-limit.md` |
| **Cliquid** | 0.58 ns 处崩溃 | 同上（0.23 g/cc） | 同上 |
| ~~Water~~（已解决） | 曾用窄表 eos_312 | 2026-08-11 换宽表 eos_311（ρ 2e-6~400，T≤15 keV）后复验通过 2.4e-9 | 已修复（清单 §四-2） |

## 3. 借用规则提醒

借用是**数据近似**（Multi_BACK 原生策略，material.base 的 MID 映射；
`migrate_opc_batch.py:L31-L43`）：
- SiO2 族（Glass/Quartz/Silica）共用 opc_1022
- 碳族（CD2/Diamond/Cliquid/Cphenolic）借 opc_1344（C）
- LiD/LiH 借 opc_1071（Li）；SS 借 opc_1181（Fe）；WC 借 opc_1121（W）

精度敏感问题（如 Diamond 与 C 的辐射行为差异）需评估借用影响。

## 4. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
