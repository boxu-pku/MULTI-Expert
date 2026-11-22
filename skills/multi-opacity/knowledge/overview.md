---
title: MULTI 辐射输运模型总览 — 2D 单群灰体 vs 1D 多群非 LTE
skill: multi-opacity
category: overview
source_anchors:
  - r94/m2d-core-9.1/M20_Transport.r:L106-L176
  - r94/matter-3.1/Mat2013_LoadOpa.r:L22
  - r94/MULTI-IFE-2015/m150304.f95:L2865-L2870
  - MULTI-2D_材料库迁移指南.md §2
doc_ref: "MULTI-2D_材料库迁移指南.md §2, §8-2"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 辐射输运
  - 单群
  - 多群
  - 非LTE
  - 灰体
---

# MULTI 辐射输运模型总览

> **TL;DR**：2D 是**单群（灰体）扩散**——每单元一个自由程 λ(ρ,T)，多群表在 2D 没有消费者；1D 是**真多群非 LTE**——材料挂 planck/ross/eps 多群表，群结构自动从表边界并集推导。同一物理问题两程序辐射描述精度不同。

## 1. 两个程序，两种模型

| | 2D（m2d-core-9.1） | 1D（MULTI-IFE-2015） |
|---|---|---|
| 模型 | 单群（灰体）扩散 | 多群（谱分辨）扩散，非 LTE |
| 不透明度输入 | `freepath` 回调 → λ(ρ,T) [cm]，每单元 1 值 | planck/ross 多群表（mgo）或单群表（sgo）+ eps 发射率 |
| 群结构 | 无（`nphis` 是**角度**离散，非光子群！） | 自动从各表 f1/f2 边界**并集**推导 |
| Zeff | 解析/常数（zi），不读外部 Zeff 表 | Zeff sgo 表（z_id）或常数（z_id=-1 用 zi） |
| 发射率 EPS | 无接口 | 支持（eps_id=-1 退化为 LTE） |

## 2. 2D 单群模型的实际含义

- `M20_Transport`（`M20_Transport.r:L106`）调用 `freepath(hydro,mid,rho,tmed)`
  回调得 λ（`L161`），再调 `M19_Radia`（`L163-L164`）。
- `Mat2013_LoadOpa`/`Mat2013_LoadTab` 被作者禁用：
  `Mat2013_LoadOpa.r:L22` / `Mat2013_LoadTab.r:L19` —— `error("not tested software")`。
  但 `Mat2013_LoadMF` 本体的 mgo/sgo 解析分支是好的，User.r 可直接调它读表后
  自写插值回调（迁移指南 §2.1）。
- **多群表在 2D 没有消费者**（迁移指南 §2.1 结论）。
- 标准做法：各材料用解析公式 `opafun`（`Material.r` 的 `freepath_Au` 等，
  拟合自表数据或文献）。

## 3. 1D 多群模型的实际含义

- 每种材料挂六表：eeos/ieos/z/planck/ross/eps（`m150304.f95:L2865-L2870`）。
- **群结构自动推导**（`frequencies` 子程序，`m150304.f95:L3345`）：
  合并所有材料各表的 fmin/fmax 边界排序成统一网格；多材料群结构不同时取**并集**
  （群数膨胀，注意算力）；无多群表时回退 ng=2 [1, 1e6] eV（`m150304.f95:L3375-L3379`）。
- 单群（sgo）表可作灰体材料跑：`opa` 中 `fa==fb` 分支（`m150304.f95:L2285`）。

## 4. 精度差异与校核建议

迁移指南 §8-2：同一物理问题在两程序中辐射描述精度不同；建议：
1. 用 1D 多群结果离线生成 Rosseland 平均 λ(ρ,T) 回灌 2D，或
2. 两程序结果直接对比校核。

已迁移材料正是这个路线：1D 用 Thermos/CELIA 多群表跑验证算例；
2D opafun 用同一多群表的 Rosseland 平均自由程拟合式（`Material_mig.r`）。

## 5. 与其他部分的耦合

| 方向 | 关联部分 | 关系 |
|---|---|---|
| 上游 | 数据源（Thermos/CELIA/SNOP/opc） | 表文件从哪来 → `knowledge/data_sources.md` |
| 下游 2D | `Material.r`/`Material_mig.r` 的 opafun | λ 公式从哪来 → `knowledge/freepath_mechanism.md` |
| 下游 1D | `m150304.f95` 六表加载 | 输入卡写法 → multi-1d-ife skill |

## 6. 常见误解

| 误解 | 正解 |
|---|---|
| "nphis 是光子群数" | 错，是 4π 立体角方向离散（典型 2:4:4:4:4:2），见 `M20_Transport.r:L84` |
| "2D 可以直接读多群表跑" | 错，LoadOpa/LoadTab 已禁用；要解析式或自写单群插值回调 |
| "EPS 表 2D 也能用" | 错，EPS（非 LTE 发射率）仅 1D 支持（迁移指南 §8-6） |

## 7. 延伸阅读

- `knowledge/freepath_mechanism.md`、`knowledge/data_sources.md`
- `MULTI-2D_材料库迁移指南.md §2`（消费路径）、§8-2（精度差异）

## 8. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
