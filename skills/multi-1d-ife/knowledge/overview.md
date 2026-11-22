---
title: MULTI-IFE-2015 程序总览 — 构成、物理模型、算例与表库
skill: multi-1d-ife
category: overview
source_anchors:
  - r94/MULTI-IFE-2015/m150304.f95:L4352
  - r94/MULTI-IFE-2015/tables/README:L14-L18
  - cases/2015CPC/RUN:L2-L8
  - MULTI-2D_梳理文档.md §4.6
doc_ref: "MULTI-2D_梳理文档.md §4.6, §6.7; MULTI-2D_材料库迁移指南.md §2.2"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - MULTI-IFE
  - m150304
  - 多群
  - 非LTE
  - 算例
---

# MULTI-IFE-2015 程序总览

> **TL;DR**：自包含 Fortran 程序 `m150304.f95`（4356 行，`gfortran` 直接编译），一维多群非 LTE 辐射流体。材料挂 eeos/ieos/z/planck/ross/eps 六表（按 id 检索），群结构自动推导。4 个官方算例 + 47 个材料验证算例。

## 1. 程序构成

- 单一文件：`r94/MULTI-IFE-2015/m150304.f95`（共 4356 行；`program multi_ife` 在 L4352）
- 编译：`gfortran m150304.f95 -o multi`（算例 RUN 脚本自动做，
  `cases/2015CPC/RUN:L4-L5`：先 `cp -s` 软链为 `multi.f95` 再编译）
- 输入：`data.in`（运行时软链为 `fort.12`，RUN:L7）
- 表库：`r94/MULTI-IFE-2015/tables/`（运行时软链 `tables`，RUN:L8）
- 输出：`output`（日志）、`fort.10`（ASCII 全量记录）、`fort.11`（ASCII 剖面）

## 2. 物理模型

- 一维（平面 igeo=1 / 柱 / 球）拉格朗日辐射流体
- **真多群**辐射输运（谱分辨扩散），**非 LTE**（挂 EPS 发射率表时；eps_id=-1 退化为 LTE）
- 双温（电子/离子分离 IEOS：eeos + ieos）
- Zeff 电离度（z 表或常数 zi）
- 驱动：激光（pulse_wkb 等块）、辐射浴（betar/itype/trad/tau）、或纯流体

自带表库 `tables/`：DT、Be20keV、Mix20keV、Al、Carbon、CPC88 等。
README 记载（`tables/README:L14-L18`）：DT 反演 EOS 表由 ConvertEOS 从单温表
"substract ideal gas contribution of ions" 得到；不透明度 20 群表**直接复制自
CELIA 的 D_20G.PLANCK/D_20G.Rosseland**（纯氘表）——与 Multi_BACK 同源。

## 3. 官方算例（`cases/2015*`，梳理文档 §6.7）

| 算例 | 物理 |
|---|---|
| **2015CPC** | 平面 Al(2 μm)+Au(0.2 μm) 靶，3×10¹⁴ W/cm²、300 ps、0.44 μm 激光（CPC 1988 经典） |
| **2015PRE** | 150 nm Al 箔，10¹⁵ W/cm²、150 fs、400 nm 超短脉冲（Ramis CPC 183 (2012) 637） |
| **2015IND** | NIF 间接驱动 Be 烧蚀层靶（Lindl 1995）；20 ns、球形、辐射温度 80→250 eV |
| **2015DIR** | 直接驱动 |

## 4. 材料验证算例（`validation_cases/<X>Check`，47 个）

为材料迁移验收设计的统一模板（材料迁移验证规范 §3）：
- 平面（igeo=1）单材料平板，厚 ~2 μm，20 单元
- 右侧 100 eV 恒定辐射浴（betar=1, itype=2, trad=100, tau=1e-9）
- texit=1.2e-9，dt=1e-11（约 121 步，秒级完成）
- 挂新迁移的 eeos/ieos/z/planck/ross 五表，eps_id=-1
- 模板算例：`validation_cases/TiCheck/`；生成器：`batch_migrate.py` 的
  `CASE_TEMPLATE`（L172-L243）与 `make_case()`（L246-L261）
- **产物永久保留**（人工验收依据），禁止 CLEAR

## 5. 与其他部分的耦合

| 方向 | 关联部分 | 关系 |
|---|---|---|
| 上游 | 表文件（格式见 multi-eos-format；来源见 multi-opacity） | 六表从哪来 |
| 下游 | `plot_1d_validation.py` 解析 fort.10 | 可视化 → multi-visualize |
| 运行 | RUN/ktag/CLEAR 机制 | → multi-case-runner |

## 6. 延伸阅读

- `knowledge/input_cards.md`、`knowledge/table_loading.md`、`knowledge/output_format.md`
- `MULTI-2D_材料库迁移指南.md §2.2`（1D 消费路径）

## 7. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
