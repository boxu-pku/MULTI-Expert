---
title: mgo 多群不透明度 / sgo 单群与 Zeff 表 — 字节级规范与双读取器兼容
skill: multi-eos-format
category: internals
source_anchors:
  - r94/matter-3.1/Mat2013_LoadMF.r:L110-L134
  - r94/MULTI-IFE-2015/m150304.f95:L2226-L2227
  - r94/MULTI-IFE-2015/m150304.f95:L3068-L3071
  - r94/matter-3.1/Mat2013.r:L31
  - MULTI-2D_材料库迁移指南.md §1.3-§1.4
doc_ref: "MULTI-2D_材料库迁移指南.md §1.3-1.4, §2.3"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - mgo
  - sgo
  - 多群
  - 单群
  - Zeff
  - f1f2
  - type串
---

# mgo 多群不透明度 / sgo 单群与 Zeff 表

> **TL;DR**：mgo = 每个光子能群一个子表（带头二行 f1 f2 群边界），全部 log10 值；sgo = 单群平均/Zeff（无 f1f2 行）。Zeff 表的 T 网格是 log10(**keV**)。type 串双兼容写法：Planck ` 0.70000000E+01`、Rosseland ` 0.40000000E+01`、Zeff ` 0.60000000E+01`。

## 1. mgo（多群不透明度）表

每个光子能群一个子表，NG 个子表连续存放（同 id）：

```
表头:      id | "PLANCK M       "(或 ROSSELAND M / EPS M) | NR | NT
第二行:    f1 f2  —— 本群光子能量下/上界, eV (两个 15 字符字段, 独占一行)
数据:      lr[NR]    log10(密度 g/cm³)
           lt[NT]    log10(温度 eV)
           lo[NT×NR] log10(不透明度 cm²/g); T 行 ρ 列(前 NR 个值对应第一个 T)
```

- mgo 判定：`Mat2013_LoadMF.r:L110`
- f1f2 次行读取：`check_multi_file.py:L94-L97`（独立复刻）；1D 端 `m150304.f95:L3010-L3016`（itype≥6 才读 fmin/fmax）
- 群边界范围示例：CELIA 20G = 1~5000 eV；W_Planck_Fine = 69 群 1~80 keV；Thermos 多数 = 1~6000 eV（迁移指南 §4.4）
- lo 布局与 IEOS 同规则（能量/温度主序，前 NR 个值属第一个 T）

## 2. sgo（单群平均 / Zeff）表

```
表头:  id | type(见 §4 变体表) | NR | NT
数据:  lr[NR] lt[NT] lo[NT×NR]   (无 f1/f2 行, 全部 log10)
```

- sgo 判定（Planck/Rosseland/EPS/Zeff 各变体）：`Mat2013_LoadMF.r:L130-L134`
- 1D 端单群处理：无 sgo 标识符；`opa` 子程序中 `fa==fb` 即单群（任何频率命中同一分支，
  `m150304.f95:L2285`）；load_table_group 不读 f1f2 行时置 `fmin=fmax=0.0`（`m150304.f95:L3010-L3016`）
- **λ = 1/(κ·ρ)**：κ 单位 cm²/g，自由程 cm（迁移指南 §7.3）

## 3. Zeff 表的温度网格是 log10(keV)

- `Mat2013.r:L31` 注释写 "temperatures (eV)" —— **陈旧文档**。
- 1D 源码铁证（`subroutine zbr`，`m150304.f95:L2218`）：
  ```
  m150304.f95:L2226-L2227
     rlog = log10(r)
     tlog = log10(t)-3.     ← log10(T[eV])−3 = log10(T[keV])
  ```
  对比不透明度 `opa` 用 `tlog = log10(t)`（`m150304.f95:L2287`）。
- 实际文件网格 -3~+2 只有按 keV 解释才有物理意义（1 eV~100 keV）。
- EOS-tools 按 keV 处理，与实际文件一致（迁移指南 §1.4 ⚠）。
- 当前 2D 不读外部 Zeff 表，差异暂无实际影响；**1D 必须按 keV**。

## 4. type 串变体与双读取器兼容

| 表类别 | r94（LoadMF）接受 | 1D Fortran 接受 | **双兼容写法** |
|---|---|---|---|
| 单群 Planck | `PLANCK 1       `、` 0.70000000E+01`、` 7.00000000e+00` | 对应 itype 判定 | ` 0.70000000E+01` |
| 单群 Rosseland | `ROSSELAND 1    `、` 0.40000000E+01`、` 4.00000000e+00` | 同上 | ` 0.40000000E+01` |
| Zeff | ` 0.60000000E+01`、` 6.00000000e+00`（`Mat2013_LoadMF.r:L133-L134`） | ` 0.60000000E+01`、` 0.60000000e+01` | **` 0.60000000E+01`** |

> ⚠ EOS-tools 写出的 zeff 用 ` 6.00000000e+00`，**1D 会误读为 IEOS**——
> 给 1D 用需把头行第 2 字段改成 ` 0.60000000E+01`（迁移指南 §2.3-1；
> agent/pitfalls/zeff-type-string-variants.md）。

## 5. 1D 多群加载的两个行为（必须知道）

1. **遇 EOF 结束**：`m150304.f95:L3050-L3052`（`if(ind==0)return`）
2. **遇 f1==f2 退化子表误判结束**：`m150304.f95:L3068-L3071`
   （"for a single group table, return inmediatelly"）——
   Thermos 文件可能含退化子表（Ne 实例：77/78 群），
   迁移时用 `batch_migrate.py` 的 `drop_degenerate_groups()`（L71-L95）删除；
   详见 agent/pitfalls/degenerate-opacity-group.md。

## 6. 常见错误

| 错误 | 原因 | 修复 |
|---|---|---|
| 1D 加载摘要群数比源表少 | f1==f2 退化子表截断 | drop_degenerate_groups() |
| 1D 把 Zeff 表当 IEOS 读 | type 串 ` 6.00000000e+00` 1D 不认 | 改头为 ` 0.60000000E+01` |
| Zeff 插值结果离谱 | T 网格按 eV 解释（应 keV） | pitfalls/zeff-kev-not-ev.md |
| mgo 群边界行过短被拒 | f1/f2 行 <30 字符（遗留坏文件 AU_SIMPLE_PLANCK_MG） | 迁移指南 §5，勿用 |

## 7. 延伸阅读

- `knowledge/overview.md`（容器与 type 分类总表）
- `multi-opacity` skill（不透明度物理来源与选用）
- `MULTI-2D_材料库迁移指南.md §1.3-1.4、§2.3`

## 8. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
