---
title: 材料数据局限与注意事项（multi-materials-db 摘要索引）
skill: multi-materials-db
category: pitfalls
source_anchors:
  - MULTI-2D_材料库清单.md §四
  - r94/m2d-core-9.1/Material.r:L15-L22
doc_ref: "MULTI-2D_材料库清单.md §四"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 数据局限
  - 注意事项
  - 可靠性
---

# 材料数据局限与注意事项

## 1. 可靠性总警告

`r94/m2d-core-9.1/Material.r:L15-L22`（英文原文）：
"These tables are fine for numerical research, but, for scientific quantitative
research, they have to be replaced by more accurate data bases."
hyades 源为 LANL SESAME/QEOS 老库；Thermos/CELIA/SNOP 来源见 Multi_BACK material.base。
**定量科研引用前请追溯来源**（清单 §四-1；迁移指南 §8-1）。

## 2. 逐材料注意（清单 §四 摘要）

| 材料 | 注意 | 档案 |
|---|---|---|
| Diamond / Cliquid | 源 EOS 密度下限高（0.35/0.23），烧蚀算例越界；数据局限非迁移错误 | `agent/pitfalls/eos-density-range-limit.md` |
| Kr | 验证算例用气体密度 3.749e-3（固体密度会辐射坍缩越界） | `agent/pitfalls/gas-vs-solid-case-density.md` |
| Air | 初温需 ≥ 表 T 下限 | 同上 |
| Water | 已换宽表 eos_311（2026-08-11）；旧 eos_312 是窄表（T≤0.345 eV）勿再用 | 清单 §四-2 |
| Glass | 低温区（<116 eV）依赖外推 | 清单 §四-2 |
| Ne | 已删退化子表（77 群） | `agent/pitfalls/degenerate-opacity-group.md` |
| Fe/Cu/W | 1D 拆分表初始电子能量微小负偏移（官方表固有） | 清单 §四-7 |
| 借用表材料（SiO2 族/碳族/LiD/LiH/SS/WC） | 不透明度为借用近似 | `knowledge/single_group.md §3` |

## 3. 验收状态提醒

机器验收 ACCEPT ≠ 人工确认 ✅（清单 §五）。向用户汇报材料"可用"时区分两级状态；
⚠ 材料（Diamond/Cliquid）强调"待用户终审或换源"。

## 4. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
