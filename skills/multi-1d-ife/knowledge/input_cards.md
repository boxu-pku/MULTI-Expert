---
title: data.in 输入卡详解 — parameters / layer / material / pulse_wkb 四块
skill: multi-1d-ife
category: reference
source_anchors:
  - r94/MULTI-IFE-2015/m150304.f95:L2643-L2707
  - r94/MULTI-IFE-2015/m150304.f95:L2730-L2790
  - r94/MULTI-IFE-2015/m150304.f95:L2564-L2576
  - r94/MULTI-IFE-2015/m150304.f95:L2806-L2838
  - validation_cases/TiCheck/data.in:L12-L86
doc_ref: "材料迁移验证规范.md §3; validation_cases/TiCheck/data.in"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - data.in
  - namelist
  - parameters
  - layer
  - material
  - pulse_wkb
---

# data.in 输入卡详解

> **TL;DR**：data.in（运行时=fort.12）由 Fortran namelist 块组成：`&parameters`（总控）、`&layer`（每层网格/材料，可多个）、`&material`（每种材料六表，可多个）、`&pulse_wkb`（激光，可选）。程序按名字切块读入。

## 1. 读卡机制

- `namelistblock(name,number,icode)`（`m150304.f95:L2806`）：把 fort.12 中第 number 个
  `&name` 块抄到临时文件 `block`，再 `read(3,namelist)`（如 `L2665`）
- 块识别：`locblock`（`L2838`）找 `&name` 起始
- 主调用顺序（`init`，`L2505-L2512`）：read_parameters → read_laser_*（wkb/3d/maxwell）
  → read_pulse → read_material_definitions → read_material_data → read_layer_definition
- **多 layer / 多 material 块按出现顺序编号**（`namelistblock('layer',l%nl+1,...)` `L2784`）

## 2. &parameters 块（总控）

namelist 声明 `L2652-L2657`；赋值 `L2667-L2707`。常用卡（以验证算例为基准，
`validation_cases/TiCheck/data.in:L12-L59`）：

| 卡 | 含义 | 典型值 | 锚点 |
|---|---|---|---|
| `igeo` | 几何：1=平面 / 2=柱 / 3=球 | 1 | data.in:L14；声明 L179 |
| `texit` | 模拟终止时间 (s) | 1.2e-9 | L16；L228 |
| `dtinit`/`dtmax` | 初始/最大时间步 | 1e-11 | L42；L239-L240 |
| `iradia` / `ihydro` | 辐射 / 流体开关（1 开 0 关） | 1, 1 | L29-L30；L189 |
| `inegpre` | 负压力处理（表冷区外推负值时截断） | 0 | L38；L191；迁移指南 §8-5 |
| `zmin` | 电离度下限 | 0.1 | L36；L204 |
| **辐射浴** `betar` | 右边界辐射浴开关（1 开） | 1 | L24；L207-L208 |
| `itype` | 浴时间波形（2=恒定） | 2 | L25；L209 |
| `trad` | 浴辐射温度 (eV) | 100 | L27；L213 |
| `tau` | 浴特征时间 (s) | 1e-9 | L26；L212 |
| `betal`/`alphal`/`alphar` | 左浴/两侧流体边界 | 0 | L207-L208 |
| **输出** `ns_bout` | fort.10 每 ns_bout 步记 1 次 | 1（热图分辨率要求） | L55；L231；输出控制 L381-L383 |
| `dt_bout` | fort.10 按时间间隔记录 | 1e-11 | L54；L230 |
| `ns_aout`/`dt_aout` | fort.11 同理 | — | L230-L231；L386-L389 |
| `nfuel`/`nexit` 等 | 燃料标记/最大步数 | 0/100000 | — |
| `fheat`/`fei`/`flaser`/`flf` | 物理常数因子 | 8.0/2.0/26.0/0.1 | L204 |

> 设计原则（验证规范 §3）：简单、快速、同时激发 EOS+不透明度+电离三张表。

## 3. &layer 块（每层一个，可多个）

namelist `L2781`：`nc, thick, r0, te0, zonpar, ti0, material`。
TiCheck 例（`data.in:L61-L69`）：

| 卡 | 含义 | 典型值 |
|---|---|---|
| `nc` | 单元数 | 20 |
| `thick` | 厚度 (cm) | 2.0e-4（2 μm） |
| `r0` | 初始密度 (g/cc) | 4.54（固体 Ti；注意表覆盖，见 pitfalls） |
| `te0`/`ti0` | 初始电子/离子温度 (eV) | 0.03（须 ≥ 表 T 下限） |
| `material` | 材料名（与 &material 块 name 对应） | 'Ti' |

多层示例：`cases/2015CPC/data.in:L61-L78`（Al 层 20 网格 2.0e-4 + Au 层 75 网格 0.2e-4）。

## 4. &material 块（每种材料一个）

namelist `L2739-L2741`；缺省值 `L2743-L2754`（eeos_file 缺省 "fort.13" 等）。
TiCheck 例（`data.in:L71-L86`）：

| 卡 | 含义 | TiCheck 值 |
|---|---|---|
| `name` / `ai` / `zi` | 材料名 / 原子量 / 常数电离度 | 'Ti' / 47.9 / 22 |
| `eeos_file` + `eeos_id` | 电子 IEOS 表 | 'tables/Ti_eos_e' / 22000304 |
| `ieos_file` + `ieos_id` | 离子 IEOS 表 | 'tables/Ti_eos_i' / 22000305 |
| `z_file` + `z_id` | Zeff 表；**z_id=-1 用常数 zi** | 'tables/Ti_LTE.ZEFF' / 27002000 |
| `planck_file` + `planck_id` | Planck 多群 | 'tables/Ti_LTE.PLANCK' / 27003000 |
| `ross_file` + `ross_id` | Rosseland 多群 | 'tables/Ti_LTE.ROSS' / 27004000 |
| `eps_file` + `eps_id` | 发射率（非 LTE）；**eps_id=-1 → LTE** | -1 |

id 匹配规则与迁移表命名约定见 `knowledge/table_loading.md`。

## 5. &pulse_wkb 块（激光，可选）

`m150304.f95:L2564`；namelist `L2569`：`inter, pimax, pitime, wl, delta, itype`。
2015CPC 例（`data.in:L112-L119`）：pimax=3.0e21（W/cm² 单位换算后）、pitime=300e-12、
wl=0.44e-4（cm）、itype=1（sin² 波形）。
验证算例（XCheck 模板）**不含激光块**——纯辐射浴驱动。

## 6. 常见错误

| 错误 | 原因 | 修复 |
|---|---|---|
| 表加载摘要缺某表/群数 0 | id 与表头第 1 字段不符 | 读表头 id 或 `*_id=0` 通配；`knowledge/table_loading.md` |
| 算例早期崩坏 | r0/te0 越出表覆盖 | 先查表网格范围（pitfalls/eos-density-range-limit、gas-vs-solid-case-density） |
| 热图断带 | ns_bout 太大（记录太少） | ns_bout=1 或 dt_bout ≤ texit/100（验证规范 §E） |

## 7. 延伸阅读

- `knowledge/table_loading.md`（六表加载细节）
- `validation_cases/TiCheck/data.in`（基准模板）
- `batch_migrate.py:L172-L243`（CASE_TEMPLATE 生成器）

## 8. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
