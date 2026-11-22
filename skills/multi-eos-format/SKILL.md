---
name: multi-eos-format
description: |
  MULTI-2D/1D 数据表格式专家（IEOS 反演状态方程表 / mgo 多群不透明度 / sgo 单群与 Zeff 表）。
  解释字节级格式（60 字符头、15 字符定宽、跨节打包）、单位换算链（×1e12→cgs、÷11604.519→eV）、
  IEOS 能量主序布局、EleTab/GasIEOS 电子离子表拆分、双温 ieose/ieosi 挂载；
  判断表文件是否合法、为何读错。
  触发词：IEOS, ieos, mgo, sgo, 状态方程表, EOS 表, 反演表, 不透明度表, 多群表, 单群表,
  Zeff, 电离度表, head line size, 表头, 60 字符, 单位换算, Mbar, 电子表, 离子表, 拆分,
  Mat2013_LoadMF, Mat2013_LoadIEOS, Mat2013_EleTab, GasIEOS, ieose, ieosi
triggers:
  - IEOS
  - ieos
  - mgo
  - sgo
  - 状态方程表
  - EOS 表
  - 反演表
  - 不透明度表
  - 多群表
  - 单群表
  - Zeff
  - 电离度表
  - head line size
  - 表头
  - 60 字符
  - 单位换算
  - Mbar
  - 电子表
  - 离子表
  - 拆分
  - Mat2013_LoadMF
  - Mat2013_LoadIEOS
  - Mat2013_EleTab
  - Mat2013_GasIEOS
  - ieose
  - ieosi
  - PLANCK M
  - ROSSELAND M
  - -INF
  - NAN
when_to_use: |
  1. 用户问 MULTI 表文件的格式（"这个 IEOS 文件格式对不对"、"表头 60 字符是什么"）
  2. 用户问 IEOS/mgo/sgo 三类表的区别与字段含义
  3. 用户问单位换算（"Mbar·cm³/g 怎么转 cgs"、"T 是 K 还是 eV"、"Zeff 表温度是 keV 吗"）
  4. 用户问 IEOS 数据布局（"p 数组怎么 reshape"、"能量主序"）
  5. 用户问电子/离子表拆分（"EleTab 算法"、"ieose/ieosi 怎么来的"）
  6. 加载表报错（"head line size != 60"、"bad number of tables"、"bad table type"）
  7. 用户问 -INF/NAN 特殊值、CRLF、Windows -1.#INF 等文件问题的原因
when_not_to_use: |
  - 要实际跑验证/修复脚本 → multi-table-tools（本 skill 只讲格式与原因）
  - 不透明度数据的物理来源与选用（Thermos/CELIA/SNOP/opc） → multi-opacity
  - 1D 输入卡怎么挂表（eeos_file 等） → multi-1d-ife
  - 端到端新材料迁移 → multi-material-migration
  - 某种具体材料有哪些表 → multi-materials-db
layer: knowledge
phase: 1
status: stable
created: 2026-08-11
last_updated: 2026-08-11
owner: claude
---

# multi-eos-format — MULTI 数据表格式专家（IEOS / mgo / sgo）

## 1. 角色与边界

### 1.1 我是做什么的

回答 MULTI-2D/1D 全部材料数据文件（"traditional MULTI format" 容器）的格式问题：
字节级结构、type 字段分类、单位换算链、IEOS 能量主序布局、特殊值（-INF/NAN）、
电子/离子表拆分（Mat2013_EleTab 算法）、双温 ieose/ieosi。所有结论都经过
源码级核对（`r94/matter-3.1/`），带行号锚点。

### 1.2 我不做什么

| 用户问题类型 | 归属 skill |
|---|---|
| 实际跑验证/修复/转换脚本 | `multi-table-tools` |
| 不透明度物理来源与选用（Thermos/CELIA/SNOP/opc） | `multi-opacity` |
| 1D 输入卡挂表（eeos_file/eeos_id 等） | `multi-1d-ife` |
| 端到端新材料迁移 | `multi-material-migration` |
| 某种材料有哪些表文件 | `multi-materials-db` |

## 2. 行为协议

按 `agent/TEMPLATES/skill-template.md §2` 通用协议。本 skill 要点：

- **格式问题给字节级答案**：字段宽度、顺序、布局都用表格/示意图写清楚
- **每个论断带锚点**：源码 `r94/matter-3.1/*.r:LXX` 或迁移指南 §节
- **加载报错先归类**：`head line size != 60` → CRLF（agent/pitfalls/crlf-line-endings.md）；
  `bad number of tables` → 2D 要求单表文件；`bad table type` → type 串不匹配
- **文件问题先问来源**：Multi_BACK/Windows 来源的文件优先怀疑 CRLF 与 -1.#INF

### 2.2 接到执行任务时

N/A（知识层）。实际验证/修复推给 multi-table-tools。

## 3. 知识维护规则

- 格式结论以 `r94/matter-3.1/` 源码为准；治理文档（迁移指南 §1-2）是二手摘要
- 发现新格式坑 → 追加 `agent/pitfalls/`，并在此登记

## 4. knowledge/ 子目录索引

| 文件 | 内容 | 当前状态 |
|---|---|---|
| `knowledge/overview.md` | 容器格式总览：60 字符头 + 15 字符定宽 + type 分类表 | stable |
| `knowledge/ieos_format.md` | IEOS 字节级规范、单位换算链、能量主序布局、EleTab/GasIEOS 拆分、双温挂载 | stable |
| `knowledge/mgo_sgo_format.md` | mgo 多群 / sgo 单群 / Zeff 表规范、type 串变体表、双读取器兼容 | stable |
| `knowledge/pitfalls.md` | 格式类踩坑集（摘要 + 指向 agent/pitfalls/） | stable |

## 5. 示例问答（验收基准）

### Q1: IEOS 文件的结构是什么？单位怎么换算？
**A**: 见 `knowledge/ieos_format.md`。60 字符头（id|type|NR|NE，4×15 字符）+ 15 字符定宽数据
（每行 4 值，跨节连续打包）。数据五节：r[NR] (g/cc)、de[NE] (Mbar·cm³/g)、e0[NR]、
p[NE×NR] (Mbar)、t[NE×NR] (K)。读入端 ×1e12→cgs、÷11604.519→eV
（锚点：`m150304.f95:L2959-L2965`；迁移指南 §1.2）。

### Q2: 为什么我的 p 数组 reshape 后和源表对不上？
**A**: IEOS p/t 是**能量主序** `p[j*NR+i]`（E 行 ρ 列），前 NR 个值对应第一个 ΔE。
numpy 默认 `reshape(NR,NE)` 读反了；用 `reshape(NE,NR)` 或按 `j*NR+i` 索引
（锚点：`Mat2013_LoadMF.r:L47-L50`、`Mat2013_EleTab.r:L66-L67`；
agent/pitfalls/ieos-layout-order.md）。

### Q3: 报 "head line size != 60" 是什么原因？
**A**: 表头不是恰好 60 字符。99% 是 Windows CRLF 行尾（\r 被 C 解析器算进行长，
变成 61）。跑 `fix_multi_file.sh` 去 CR 即可（锚点：`Mat2013_LoadMF.r:L101-L102`；
agent/pitfalls/crlf-line-endings.md）。少数情况：字段本身少前导空格（如 Ti_Ross 59 字符，迁移指南 §5）。

### Q4: 2D 加载 EOS 报 "bad number of tables"？
**A**: 2D 的 `Mat2013_LoadIEOS` 要求文件**恰好 1 张 IEOS 表**（`Mat2013_LoadIEOS.r:L26-L28`）。
多表文件要拆分，或用 `Mat2013_LoadMF` 自行按 id 取表（1D 就是按 id 从多表文件挑表）。

## 6. 关键源码入口

| 想理解 | 看哪个文件 |
|---|---|
| 容器解析（LoadMF，IEOS/mgo/sgo 通吃） | `r94/matter-3.1/Mat2013_LoadMF.r:L52` |
| 60 字符头检查 | `r94/matter-3.1/Mat2013_LoadMF.r:L101-L102` |
| type 分类（mgo/sgo/Zeff/IEOS 兜底） | `r94/matter-3.1/Mat2013_LoadMF.r:L110-L149` |
| -INF→-40 / NAN→0 | `r94/matter-3.1/Mat2013_LoadMF.r:L263-L269` |
| 2D 单表 IEOS 加载 | `r94/matter-3.1/Mat2013_LoadIEOS.r:L18` |
| 电子表拆分（EleTab） | `r94/matter-3.1/Mat2013_EleTab.r:L17`（C 实现） |
| 理想气体离子表（GasIEOS） | `r94/matter-3.1/Mat2013_GasIEOS.r:L23` |
| Mat2013 结构体字段 | `r94/matter-3.1/Mat2013.r:L56-L71` |
| 1D 端 EOS 单位换算 | `r94/MULTI-IFE-2015/m150304.f95:L2959-L2965` |
| 格式验证工具 | `work/eos_opacity_tools/check_multi_file.py` |

## 7. 待办

- [ ] 无（格式知识已逐字节验证）

## 8. 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建（knowledge 4 篇，锚点全部经 grep/read 验证） | claude |
