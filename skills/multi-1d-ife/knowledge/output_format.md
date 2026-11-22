---
title: 1D 输出详解 — fort.10 / fort.11 结构与 output 能量收支判读
skill: multi-1d-ife
category: internals
source_anchors:
  - r94/MULTI-IFE-2015/m150304.f95:L368-L389
  - r94/MULTI-IFE-2015/m150304.f95:L3451-L3625
  - r94/MULTI-IFE-2015/m150304.f95:L3424-L3446
  - r94/MULTI-IFE-2015/m150304.f95:L4197-L4267
  - work/eos_opacity_tools/plot_1d_validation.py:L10-L21
doc_ref: "材料迁移验证规范.md §B, §E"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - fort.10
  - fort.11
  - output
  - 能量收支
  - error
  - radinr
---

# 1D 输出详解

> **TL;DR**：`output` = 日志（表加载摘要 + 步进 + 能量收支 + "normal program termination"）；`fort.10` = ASCII 全量记录（热图数据源）；`fort.11` = ASCII 剖面表。能量相对误差 <1e-6 为验收线。

## 1. 三个输出文件

| 文件 | 打开 | 内容 | 频率控制 |
|---|---|---|---|
| `output` | stdout | 表加载摘要、步进日志、能量收支、终止标志 | 每步 |
| `fort.10` | `m150304.f95:L368`（formatted） | 全变量时间序列（ASCII） | `ns_bout`/`dt_bout`（`L381-L383`） |
| `fort.11` | `L369`（formatted） | i, x, v, rho, te, depo 剖面表 | `ns_aout`/`dt_aout`（`L386-L389`） |

⚠ IFE-2015 的 fort.10 是 **ASCII**，与 MULTI1Dvisual2.2 要的**二进制**不兼容
——`agent/pitfalls/fort10-ascii-vs-binary.md`。

## 2. fort.10（ASCII）结构

由 `write_output_record`（`L3451`）+ `write_vect`（`L3587`）写出：

```
行0:        n1            (第一节计数, write 语句 L3515/L3568 的 '(i6)')
随后 n1 行: 变量名         (write_vect L3606, '(a)')
随后 n1 行: 索引           (L3609/L3611, '(i6)')
随后 n1 行: 值             (第一节, 网格/群结构, 含 FREI 群边界 L3514)
随后:       n2            (第二节计数)
随后 n2 行: 变量名
随后 n2 行: 索引
随后:       每条记录 n2 个值(每行一个, '(e12.5)' L3615/L3620/L3625), 直到 EOF
```

记录内变量（`L3534-L3567`）：
- 标量 24 个：TIME, ISTEP, ..., DERAD（`L3534`, e%derad）, ..., ENRG4（`L3539`, e%radinr）, ...
- 单元量 13 个：**R**（密度）, **PT**（总压）, **TE**（电子温度）, **PE**（电子压强）,
  **ZI**（电离度）, **XC**（单元中心）, D, DENE, EA, F, **TI**（离子温度）, PI, AD
  （`L3547-L3559`）
- 界面量 6 个：**X**（界面位置 `L3560`）, V, **TR**（辐射温度 `L3562`）, S+, S-, S
- 群量 2 个：I-, I+（`L3563-L3567`）

解析注意：`(e12.5)` 定宽，3 位指数时**省略 e**（`-0.33689-232`）——
读取端用正则插 e（`plot_1d_validation.py:L82-L86`；agent/pitfalls/missing-e-exponent.md）。
现成解析器：`plot_1d_validation.py:read_fort10_ascii`（L36-L94）。

## 3. output 能量收支判读（验收标准 §B）

终止标志：`print *,'normal program termination'`（`L3820`，print_tail L3817）。

能量收支（`print_energies` L4197，`finish` L2528 → L2534 调用）：

| 输出行 | 含义 | 锚点 | 验收判据（材料迁移验证规范 §B） |
|---|---|---|---|
| `error` | 能量收支相对误差 = abs(epos-eneg)/((epos+eneg)/2) | `L4224` 计算、`L4267` 输出 | **绝对值 < 1e-6**（B2） |
| `radinr` | 右边界辐射输入累计 | `L4259`；累计 `L1395` | 辐射驱动算例 > 0（B5） |
| `derad` | 热辐射沉积净值（=radinl+radinr−radoutl−radoutr） | `L4251`；`L1402` | > 0（B5） |
| 表加载摘要 | 各表 id、NR/NE/NT、**ng 群数** | — | 群数与源表一致（B3） |
| 步进日志最后一行 time | 实际到达时间 | — | = texit（B4） |
| `ERROR`/`STOP`/`premature eof` | 异常 | — | 不得出现（B6） |

> ⚠ 能量守恒查不出单位错误（单位错的表自洽）——必须另与源表做绝对值对照，
> 见 agent/pitfalls/pressure-unit-confusion.md。

## 4. fort.11

`ascii_output`（`L3424`）：表头 `write(11,'(a4,1x,5a14)') 'i','x','v','rho','te','depo'`（`L3439`），
数据 `(i4,1x,5e14.6)`（`L3442`）。轻量剖面速查用。

## 5. 常见错误

| 错误 | 原因 | 修复 |
|---|---|---|
| fort.10 解析失败（float 异常） | e12.5 省略 e | 正则插 e（plot_1d_validation 已内置） |
| 热图断带/记录数 <50 | ns_bout 太大 | ns_bout=1 或 dt_bout ≤ texit/100（验证规范 §E1） |
| 能量误差超 1e-6 | 表越界/物理崩坏 | 查表覆盖（pitfalls/eos-density-range-limit） |

## 6. 延伸阅读

- `multi-visualize/knowledge/`（fort.10 可视化）
- `材料迁移验证规范.md §B/§E`（验收标准）

## 7. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
