---
name: multi-1d-ife
description: |
  MULTI-IFE-2015 一维多群非 LTE 辐射流体程序专家（m150304.f95）。
  解释 data.in 输入卡（parameters/layer/material/pulse_wkb 四个 namelist 块）、
  六表加载（eeos/ieos/z/planck/ross/eps 与 id 匹配规则）、群结构自动推导（表边界并集）、
  fort.10/fort.11 输出结构、output 能量收支判读、1D 算例（2015CPC/DIR/IND/PRE、XCheck 验证算例）。
  触发词：1D, MULTI-IFE, m150304, data.in, 输入卡, namelist, parameters, layer,
  material, pulse_wkb, eeos_file, ieos_file, z_id, planck_id, ross_id, eps_id,
  fort.10, fort.11, 群结构, 辐射浴, trad, betar, texit, inegpre, 2015CPC, 2015IND,
  XCheck, 验证算例, normal program termination, 能量误差
triggers:
  - MULTI-IFE
  - m150304
  - data.in
  - 输入卡
  - namelist
  - parameters
  - layer
  - pulse_wkb
  - eeos_file
  - ieos_file
  - z_id
  - planck_id
  - ross_id
  - eps_id
  - fort.10
  - fort.11
  - 群结构
  - 辐射浴
  - trad
  - betar
  - texit
  - inegpre
  - 2015CPC
  - 2015IND
  - 2015DIR
  - 2015PRE
  - XCheck
  - 验证算例
  - normal program termination
  - 能量误差
  - 一维
  - 1D 算例
when_to_use: |
  1. 用户问 1D 输入卡怎么写/某个参数什么意思（"eeos_file 和 eeos_id 怎么填"、"trad/tau/betar 是什么"）
  2. 用户问表加载与 id 匹配（"z_id=-1 是什么"、"planck_id 对不上"、"群数怎么来的"）
  3. 用户问 fort.10/fort.11 输出结构（"fort.10 里 R/PT/TE 是什么"、"怎么解析"）
  4. 用户问 output 判读（"能量误差多大算正常"、"radinr/derad 是什么"、"normal program termination"）
  5. 用户问 1D 算例（"2015CPC 是什么物理"、"XCheck 验证算例怎么设计"）
  6. 用户问 1D 辐射浴/激光驱动（"itype=2"、"pulse_wkb 块"）
when_not_to_use: |
  - 表文件本身的字节级格式 → multi-eos-format
  - 不透明度数据源选用 → multi-opacity
  - 实际跑算例 → multi-case-runner
  - 结果可视化 → multi-visualize
  - 端到端新材料迁移 → multi-material-migration
  - 2D 程序（m2d-*）问题 → multi-architecture
layer: knowledge
phase: 1
status: stable
created: 2026-08-11
last_updated: 2026-08-11
owner: claude
---

# multi-1d-ife — MULTI-IFE-2015 一维程序专家

## 1. 角色与边界

### 1.1 我是做什么的

回答 1D 程序 MULTI-IFE-2015（`r94/MULTI-IFE-2015/m150304.f95`，自包含 Fortran，
多群非 LTE 辐射流体）的全部问题：输入卡、六表加载、群结构推导、输出结构与判读、
算例设计。全部结论带 `m150304.f95` 行号锚点。

### 1.2 我不做什么

| 用户问题类型 | 归属 skill |
|---|---|
| 表文件字节级格式 | `multi-eos-format` |
| 不透明度数据源选用 | `multi-opacity` |
| 实际跑 1D 算例（RUN/ktag/output） | `multi-case-runner` |
| fort.10 可视化 | `multi-visualize` |
| 端到端迁移 | `multi-material-migration` |
| 2D 程序 | `multi-architecture` |

## 2. 行为协议

按通用协议。本 skill 要点：

- **输入卡问题给块级答案**：哪个 namelist 块、哪个变量、什么单位、什么默认
- **表问题先查 id 匹配规则**：`id==idin 或 idin==0`（`m150304.f95:L2944/L2999`）
- **结果判读给量化标准**：能量误差 <1e-6（验证规范 §B2）、群数与源表一致（§B3）
- **跑算例/画图不自己动手**：推给 multi-case-runner / multi-visualize

## 3. 知识维护规则

源码锚点以 `r94/MULTI-IFE-2015/m150304.f95`（4356 行）为准；
算例模板以 `validation_cases/TiCheck/` 为准。

## 4. knowledge/ 子目录索引

| 文件 | 内容 | 当前状态 |
|---|---|---|
| `knowledge/overview.md` | 程序构成、物理模型、自带算例、表库 | stable |
| `knowledge/input_cards.md` | data.in 四个 namelist 块逐参数详解 | stable |
| `knowledge/table_loading.md` | 六表加载、id 匹配、群结构自动推导 | stable |
| `knowledge/output_format.md` | fort.10/fort.11 结构、output 能量收支判读 | stable |
| `knowledge/pitfalls.md` | 1D 类踩坑索引 | stable |

## 5. 示例问答（验收基准）

### Q1: 1D 材料块的六张表怎么挂？id 怎么填？
**A**: 见 `knowledge/table_loading.md`。`eeos_file/eeos_id`（电子 IEOS）、`ieos_*`（离子）、
`z_*`（Zeff，-1 用常数 zi）、`planck_*`/`ross_*`（多群不透明度）、`eps_*`（发射率，-1=LTE）。
id 必须等于表头第 1 字段整数值；`id=0` 通配第一张对应类型表（`m150304.f95:L2944/L2999`）。
Thermos 迁移表 id=0，输入卡就用 `*_id=0`。

### Q2: 群结构是怎么来的？为什么多材料算例群数变多？
**A**: `frequencies` 子程序（`m150304.f95:L3345`）自动合并所有材料各表的 fmin/fmax
边界排序成统一网格——多材料群结构不同时取**并集**，群数膨胀（注意算力）。
无多群表时回退 ng=2 [1, 1e6] eV（`L3375-L3379`）。

### Q3: 能量误差 error 多大算正常？radinr/derad 是什么？
**A**: 见 `knowledge/output_format.md §3`。`error` = 能量收支相对误差
（`m150304.f95:L4224/L4267`），验收标准 <1e-6（材料迁移验证规范 §B2）。
`radinr` = 右边界辐射输入累计（`L4259`），`derad` = 热辐射沉积净值（`L4251`）；
辐射驱动算例应 radinr>0、derad>0。

## 6. 关键源码入口

| 想理解 | 看哪个文件/行 |
|---|---|
| 读卡机制（namelistblock） | `m150304.f95:L2806` |
| parameters 块 | `m150304.f95:L2643`（read_parameters） |
| material 块 | `m150304.f95:L2730`（read_one_material_definition） |
| layer 块 | `m150304.f95:L2775` |
| pulse_wkb 块 | `m150304.f95:L2564` |
| 六表加载分发 | `m150304.f95:L2858`（read_material_data）→ `L2880`（load_table） |
| 多群表加载 | `m150304.f95:L3040`（load_table_multi） |
| 群结构推导 | `m150304.f95:L3345`（frequencies） |
| fort.10 写出 | `m150304.f95:L3451`（write_output_record） |
| 能量收支打印 | `m150304.f95:L4197`（print_energies） |
| 正常终止标志 | `m150304.f95:L3820` |
| 自带表库 | `r94/MULTI-IFE-2015/tables/`（README 记 DT 表源自 CELIA） |

## 7. 待办

- [ ] 激光块（pulse_wkb/pulse_3d/maxwell）的更多物理细节按需补充

## 8. 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建（knowledge 5 篇） | claude |
