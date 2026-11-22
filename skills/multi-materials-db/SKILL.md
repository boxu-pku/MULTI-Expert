---
name: multi-materials-db
description: |
  MULTI-2D 材料库总账专家。回答"有哪些材料可用"：79 种材料（自带 DT/C/Al/Be/Au/Cu/Fe/W/Si/CH
  + 已迁移 67 种）按全套（多群不透明度+Zeff+1D 验证）/单群 opc/仅 EOS/无法迁移分类；
  每种材料的文件位置（r94/mat_*、tables/）、EOS 网格、不透明度群数、来源、注意事项、
  验收状态、2D 材料函数名（Material.r/Material_mig.r）。触发词：材料, 材料库, 有哪些材料,
  material, 清单, Material, MaterialTi, Material_mig, mat_, 全套材料, 单群材料,
  仅EOS, 验收状态, 网格, DT, Au, Ti, Ta, Gd, SiO2, 金刚石, 验收记录
triggers:
  - 材料
  - 材料库
  - 有哪些材料
  - material
  - 清单
  - Material
  - MaterialTi
  - Material_mig
  - mat_
  - 全套材料
  - 单群材料
  - 仅EOS
  - 验收状态
  - 网格
  - 验收记录
  - 材料清单
  - 金刚石
  - Diamond
  - 借用
when_to_use: |
  1. 用户问"MULTI 有哪些材料可用"/"材料 X 有没有"
  2. 用户问某种材料的文件位置/网格/群数/来源
  3. 用户问某种材料的验收状态（机器验收/人工确认）
  4. 用户问 2D 材料函数（"MaterialTi 在哪"、"Material_mig.r 有哪些函数"）
  5. 用户问 1D 表库命名（"tables/ 下 X_Thermos.PLANCK 是什么"）
  6. 用户问材料数据局限（"Diamond 为什么标 ⚠"、"哪些材料没法迁移"）
when_not_to_use: |
  - 表文件格式问题 → multi-eos-format
  - 不透明度数据源选用与借用规则细节 → multi-opacity
  - 加新材料（迁移流程） → multi-material-migration
  - 1D 输入卡怎么挂某材料的表 → multi-1d-ife
  - 材料数据的物理可靠性评估（指引来源追溯，不做背书）
layer: knowledge
phase: 1
status: stable
created: 2026-08-11
last_updated: 2026-08-11
owner: claude
---

# multi-materials-db — 材料库总账专家

## 1. 角色与边界

### 1.1 我是做什么的

回答"MULTI 有哪些材料可用"：79 种材料的分类（全套/单群 opc/仅 EOS/无法迁移）、
文件位置、网格、来源、注意事项、验收状态。一手总账是 `MULTI-2D_材料库清单.md`，
本 skill 做摘要导航；清单更新时同步本 skill。

### 1.2 我不做什么

| 用户问题类型 | 归属 skill |
|---|---|
| 表文件格式 | `multi-eos-format` |
| 不透明度来源与借用规则细节 | `multi-opacity` |
| 加新材料 | `multi-material-migration` |
| 1D 挂表写法 | `multi-1d-ife` |

## 2. 行为协议

按通用协议。本 skill 要点：

- **材料查询先给分类**：全套/单群/仅EOS/无源四类决定能用该材料做什么算例
- **⚠ 标记必提醒**：Diamond/Cliquid 数据局限；借用表材料注明近似
- **验收状态分两级**：机器验收 ACCEPT ≠ 人工确认 ✅（材料库清单 §五）
- **可靠性不背书**：表"适合数值研究，定量科研需换更精确数据库"（Material.r 头警告）

## 3. 知识维护规则

- `MULTI-2D_材料库清单.md` 是一手总账——新材料验收后**先更新清单**，再同步本 skill
- 映射关系一手来源：`Multi_BACK_材料不透明度映射表.md`

## 4. knowledge/ 子目录索引

| 文件 | 内容 | 当前状态 |
|---|---|---|
| `knowledge/overview.md` | 材料库构成与四分类总览 | stable |
| `knowledge/full_set.md` | 27+1 全套材料明细（含自带） | stable |
| `knowledge/single_group.md` | 21 种单群 opc 材料明细（含借用与 ⚠） | stable |
| `knowledge/eos_only.md` | 9 种仅 EOS + 4 种无源材料 | stable |
| `knowledge/pitfalls.md` | 材料数据局限与注意事项 | stable |

## 5. 示例问答（验收基准）

### Q1: MULTI 有哪些材料可用？
**A**: 79 种（2026-08-14）：自带全套 DT/C/Al/Be/Au（+Cu/Fe/W/Si/CH 有 2D EOS）；
已迁移 69 种 = 27+3 全套（H/He/Li/N/O/Ne/Mg/Si/Ar/V/Fe/Ni/Cu/Zn/Kr/Mo/Ag/Xe/Gd/Ta/W/Pb/U/Ti/DD/D/CH/AlFEOS/AlFlash）
+ 21 种单群 opc（SiO2 族/聚合物/水/空气等）+ 9 种仅 EOS + 4 种无源（Ca/Nd/Ge/Se）。
明细见 `knowledge/overview.md` 与 `MULTI-2D_材料库清单.md`。

### Q2: Ta 的不透明度有多少群？验证算例在哪？
**A**: Ta 全套：mat_Ta-1.0（EOS 49×128）+ Thermos 21 群 + Zeff；验证算例
`validation_cases/TaCheck`（机器验收 ACCEPT）。见 `knowledge/full_set.md`。

### Q3: Diamond 为什么标 ⚠？能用吗？
**A**: 源 EOS 表密度下限 0.35 g/cc 过高，烧蚀算例 ρ 越界（能量误差 1.17e-4 超阈值）——
**数据局限非迁移错误**。非烧蚀类、ρ 不低于下限的算例可用；或换更宽 EOS 源。
见 `knowledge/single_group.md` 与 `agent/pitfalls/eos-density-range-limit.md`。

## 6. 关键位置

| 内容 | 位置 |
|---|---|
| 材料总账（一手） | `MULTI-2D_材料库清单.md` |
| 不透明度映射（一手） | `Multi_BACK_材料不透明度映射表.md` |
| 2D 材料函数（自带+Ti） | `r94/m2d-core-9.1/Material.r` |
| 2D 材料函数（迁移 56 个） | `r94/m2d-core-9.1/Material_mig.r` |
| 1D 表库 | `r94/MULTI-IFE-2015/tables/` |
| 验证算例 | `validation_cases/<X>Check/` |

## 7. 待办

- [ ] 人工确认推进后同步清单 §五 与本 skill 验收状态

## 8. 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建（knowledge 5 篇） | claude |
| 2026-08-14 | AlFEOS 入库同步（77→78；overview/full_set/SKILL 三处） | claude |
| 2026-08-14 | AlFlash 入库同步（78→79；FLASH IONMIX4 系列） | claude |
