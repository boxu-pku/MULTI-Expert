---
title: MULTI 可视化路径总览（1D 脚本 / 2D GUI / MULTI1Dvisual2.2 限制）
skill: multi-visualize
category: overview
source_anchors:
  - work/eos_opacity_tools/plot_1d_validation.py:L1-L26
  - 材料迁移验证规范.md §E
  - MULTI-2D_梳理文档.md §9
doc_ref: "材料迁移验证规范.md §E; MULTI-2D_梳理文档.md §9"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 可视化
  - 总览
  - 路径
---

# MULTI 可视化路径总览

> **TL;DR**：1D（IFE-2015）→ `plot_1d_validation.py`（fort.10 ASCII → 热图+剖面）；2D → R94 GUI 的 mpp22（读二进制快照）；MULTI1Dvisual2.2 只适用 Windows Multi1D 二进制 fort.10，与 IFE-2015 **不兼容**。

## 1. 三条路径按场景选

| 场景 | 路径 | 产物 |
|---|---|---|
| 1D 算例（2015*、XCheck）结果 | `plot_1d_validation.py <算例目录>` | density_heatmap.png + profiles_mid.png |
| 2D 算例（M2D_*）结果 | `./R94` → Manager2015 选 case → Table 选时间/变量 → mpp22 | 云图/矢量图（GUI） |
| Windows Multi1D 二进制 fort.10 | `$MULTI_APP/MULTI1Dvisual2.2` | GUI 交互 |

## 2. 关键区分：两种 fort.10

| | IFE-2015（本项目） | Windows Multi1D |
|---|---|---|
| 格式 | **ASCII**（`m150304.f95:L368` formatted） | **二进制** |
| 工具 | plot_1d_validation.py | MULTI1Dvisual2.2 |

混用后果：GUI 读不出记录。替代：用脚本出图；非要 GUI 需另行 ASCII→二进制转换（未实现）。
详见 `agent/pitfalls/fort10-ascii-vs-binary.md`。

## 3. 1D 可解析的变量（fort.10 记录内）

- 标量：TIME, ISTEP, ..., DERAD, ENRG4(radinr), ...（24 个）
- 单元量（13）：**R**（密度 g/cc）、**PT**（总压 dyn/cm²）、**TE**/**TI**（电子/离子温度 eV）、
  **PE**（电子压强）、**ZI**（电离度）、**XC**（单元中心 cm）、D、DENE、EA、F、PI、AD
- 界面量（6）：**X**、V、**TR**（辐射温度）、S+、S-、S
- 群量（2）：I-、I+

变量命名参照 MULTI1Dvisual2.2 的 `legacy/scanFile.py`（验证规范 §E 说明）。
写出侧锚点：`m150304.f95:L3547-L3567`。

## 4. 2D 可视化变量（写在快照 `.d` 文件里）

rho、T/Te/Ti、P/Pe/Pi、TR、v、ne、depo/D/V、ct（三角形类型）；
自定义变量用 `m2d_write` 注册（梳理文档 §9-4）。详见 `knowledge/gui_2d.md`。

## 5. 延伸阅读

- `knowledge/plot_1d.md`、`knowledge/gui_2d.md`
- `multi-1d-ife/knowledge/output_format.md`（fort.10 结构）

## 6. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
