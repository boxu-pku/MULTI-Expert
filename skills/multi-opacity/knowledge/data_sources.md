---
title: 不透明度四大数据源 — Thermos / CELIA / SNOP / hyades opc 的特征与选用
skill: multi-opacity
category: reference
source_anchors:
  - Multi_BACK_材料不透明度映射表.md §A-§D
  - MULTI-2D_材料库迁移指南.md §4.4
  - r94/MULTI-IFE-2015/tables/README:L14-L18
  - work/eos_opacity_tools/migrate_opc_batch.py:L31-L43
  - MULTI-2D_材料库清单.md §三
doc_ref: "Multi_BACK_材料不透明度映射表.md（全文）; MULTI-2D_材料库迁移指南.md §4.4"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - Thermos
  - CELIA
  - SNOP
  - opc
  - hyades
  - 数据源
  - 借用规则
---

# 不透明度四大数据源

> **TL;DR**：按 Multi_BACK 原生用法选源——元素→Thermos 多群（43 元素）；D/C 系→CELIA（1/20/100 群）；Ti/Au/Be→SNOP；SiO2 族/聚合物/水/空气等→hyades opc 单群平均（含借用规则）。权威对照：`Multi_BACK_材料不透明度映射表.md`。

## 1. 数据源总览

源目录：`$MULTI_LIBS/newmulti/Multi_BACK/matter++/`。
材料索引：`material.base`（187 条记录，注释含来源说明）+ `material.user`（9 条）。

| 源 | 位置 | 类型 | 覆盖 | 群结构 |
|---|---|---|---|---|
| **Thermos** | `Thermos/mat_X/` | 多群 mgo + Zeff | 43 元素（H~U） | 多数 1~6000 eV；W 另有 Fine 版 69 群 1~80 keV |
| **CELIA** | `mat_CELIA/` | 多群 mgo + Zeff | C/D/DT/H + Be_40G | 1G/20G/100G 可选；20G=1~5000 eV |
| **SNOP** | 各 mat_*/ 下 | 多群 mgo + Zeff + EPS | Ti（LTE/NLTE 30 群）、Au、He、C、Be（opbe 40 群） | 随文件 |
| **hyades opc** | `hyades/Opacity/opc_*.dat`（36 个） | **单群平均**（Rosseland+Planck，非多群） | 30+ 材料（SiO2 族/聚合物/水/空气/金属） | 无群（(ρ,T) 网格平均值） |

另有：Au100 群（30×50 细网格）、multifs Al、`ColdOpacity/*.coldopacity`（约 90 元素
Eph–μ 文本表，冷边照相用，**不进输运**）——迁移指南 §4.4。

## 2. 选用规则（与 Multi_BACK 原生用法一致，映射表 §对照）

| 材料类别 | 选源 | 项目内文件 |
|---|---|---|
| 单质元素（H~U） | Thermos `X_Planck.dat/X_Rosseland.dat/X_Zeff.dat` | `tables/X_Thermos.PLANCK/.ROSSELAND/.ZEFF`（id=0） |
| D/DD/DT | CELIA 纯氘表（D_20G.PLANCK/.ROSS + D.ZEFF） | `tables/DD_CELIA.*`、`tables/D_CELIA.*` |
| CH | CELIA 碳表（C_20G + C.ZEFF） | `tables/CH_CELIA.*` |
| Ti | SNOP_LTE.Planck/.Ross/.ZEFF（30 群，MID309） | `tables/Ti_LTE.*` |
| SiO2 族/聚合物/Al2O3/水/空气/WC/SS/碳族/LiD/LiH/Sn/Eu | hyades opc 单群（含借用） | `tables/X_OPC.ROSS/.PLANCK`（id=opc 表号） |
| Lucite/PVA/Pt/Teflon/HE/PBX9502/Epoxy/BeO/C8H7Br/B4C | **无不透明度**（Multi_BACK 中也是 Only EOS） | — |

命名约定详见 `MULTI-2D_材料库清单.md §三`。

## 3. hyades opc 表的真实结构（经 C++ 源码确认）

已由 Multi_BACK 的 C++ 源码（`CHYADES_Tab.h`/`CHYADES_Opacity.h`）确认
（参考：`$MULTI_LIBS/newmulti/Hyades相关/HYADES格式EOS转Multi代码/`）：

```
[标题2行, NR, NT, rho网格(g/cc), T网格(keV),
 Rosseland平均(NT×NR), Planck平均(NT×NR)]     ← (ρ,T) 双网格上的平均值，非多群
```

- **Planck 块全零 = 仅 Rosseland**（读取端复制 Rosseland 代替）——`opc2sgo.py:L40-L41`
- 这正是 2D 单群输运所需形式，也可作 1D 的 sgo 表；Multi1D 原生用法即如此
  （material.base 注 "One group"；材料库清单 §四-3）
- 转换：`opc2sgo.py`（log10 化 + keV→eV + 双兼容 type 串）

## 4. 借用规则（Multi_BACK 原生映射，`migrate_opc_batch.py:L31-L43`）

| 材料 | 借用表 | 材料 | 借用表 |
|---|---|---|---|
| Glass/Quartz/Silica（SiO2 族） | opc_1022 | LiD/LiH | opc_1071（Li） |
| Diamond/Cliquid/Cphenolic/CD2（碳族） | opc_1344（C） | SS 不锈钢 | opc_1181（Fe） |
| WC | opc_1121（W） | DD/DT（多群侧） | 借纯 D 表（CELIA） |

> 借用是**数据近似**，精度敏感问题注意；清单中对应材料有标注。

## 5. 数据可靠性提醒（迁移指南 §8-1）

`Material.r:L15-L22` 头部警告（英文原文）：
"These tables are fine for numerical research, but, for scientific quantitative
research, they have to be replaced by more accurate data bases."
Multi_BACK 表来源混杂（SESAME/QEOS/SNOP/MPQEOS/WorkOp/CELIA），`material.base`
的 REM 注释有部分来源说明，**定量科研引用前请追溯**。

## 6. 已知问题文件

见 `MULTI-2D_材料库迁移指南.md §5`（AU_eosd 损坏、AU_SIMPLE_PLANCK_MG 坏、
Ti_Ross 头行 59 字符、Thermos 5 文件含 -1.#INF、空目录清单等）。
Thermos 退化子表问题见 `agent/pitfalls/degenerate-opacity-group.md`。

## 7. 延伸阅读

- `Multi_BACK_材料不透明度映射表.md`（187+9 条全量映射，权威）
- `knowledge/overview.md`、`knowledge/freepath_mechanism.md`
- `MULTI-2D_材料库清单.md §三`（项目内文件命名）

## 8. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
