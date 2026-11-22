---
name: multi-opacity
description: |
  MULTI 不透明度与辐射输运专家。解释 2D 单群（灰体）扩散模型与 freepath/opafun 机制
  （λ(ρ,T) 解析公式或查表）、1D 真多群非 LTE 模型、四个不透明度数据源
  （Thermos/CELIA/SNOP/hyades opc）的特征与选用、多群→单群聚合（Rosseland/Planck 平均）、
  拟合自由程公式。触发词：不透明度, opacity, 多群, 单群, 灰体, Rosseland, Planck,
  自由程, freepath, opafun, Thermos, CELIA, SNOP, opc, 辐射输运, 扩散, 发射率, EPS,
  非LTE, NLTE, 群结构, 平均自由程
triggers:
  - 不透明度
  - opacity
  - 多群
  - 单群
  - 灰体
  - Rosseland
  - Planck
  - 自由程
  - freepath
  - opafun
  - Thermos
  - CELIA
  - SNOP
  - opc
  - 辐射输运
  - 扩散
  - 发射率
  - EPS
  - 非LTE
  - NLTE
  - 群结构
  - 平均自由程
  - multigroup
  - one group
  - grey
when_to_use: |
  1. 用户问 2D 辐射输运怎么用不透明度（"多群不透明度怎么用"、"2D 能用多群表吗"）
  2. 用户问 freepath/opafun 回调机制（"自由程公式怎么写"、"opafun 是什么"）
  3. 用户问不透明度数据源选用（"Thermos 和 CELIA 有什么区别"、"opc 表是什么"、"SiO2 的不透明度用哪个"）
  4. 用户问多群→单群聚合（"怎么把多群表合成单群"、"Rosseland 平均怎么算"）
  5. 用户问 1D 多群/非 LTE（"EPS 发射率"、"LTE 和非 LTE"）
  6. 用户问某材料不透明度借用规则（"LiD 借 Li 表"、"WC 借 W 表"）
when_not_to_use: |
  - mgo/sgo 文件字节级格式 → multi-eos-format
  - 1D 输入卡怎么写（planck_file/ross_id 等） → multi-1d-ife
  - 实际跑转换/拟合脚本 → multi-table-tools
  - 某种材料有哪些不透明度文件 → multi-materials-db
  - 辐射输运求解器内部（M19_Radia 数值算法） → multi-architecture（2D 模块层面）
layer: knowledge
phase: 1
status: stable
created: 2026-08-11
last_updated: 2026-08-11
owner: claude
---

# multi-opacity — 不透明度与辐射输运专家

## 1. 角色与边界

### 1.1 我是做什么的

回答 MULTI 的不透明度问题：2D 单群输运模型与 freepath/opafun 机制、
1D 多群非 LTE 模型、四个不透明度数据源（Thermos/CELIA/SNOP/hyades opc）的特征与选用、
多群→单群聚合与自由程拟合。物理选择 + 机制解释，带源码锚点。

### 1.2 我不做什么

| 用户问题类型 | 归属 skill |
|---|---|
| mgo/sgo 字节级格式 | `multi-eos-format` |
| 1D 输入卡写法（planck_file 等） | `multi-1d-ife` |
| 实际跑 opc2sgo/聚合/拟合脚本 | `multi-table-tools` |
| 某种材料的不透明度文件位置 | `multi-materials-db` |
| 端到端迁移 | `multi-material-migration` |

## 2. 行为协议

按通用协议。本 skill 要点：

- **先分清 1D 还是 2D**：两个程序的辐射模型完全不同（单群灰体 vs 多群非 LTE），
  同一问题的答案相反（如"多群表能不能用"：1D 能，2D 不能直接消费）
- **数据源问题查映射表**：`Multi_BACK_材料不透明度映射表.md` 是权威
- **物理合理性提醒**：不透明度表来源混杂（迁移指南 §8-1），定量科研需追溯来源

## 3. 知识维护规则

同通用规则；映射表（`Multi_BACK_材料不透明度映射表.md`）是一手来源。

## 4. knowledge/ 子目录索引

| 文件 | 内容 | 当前状态 |
|---|---|---|
| `knowledge/overview.md` | 1D/2D 辐射模型对比：单群灰体扩散 vs 多群非 LTE | stable |
| `knowledge/freepath_mechanism.md` | 2D freepath/opafun 机制、调用链、拟合公式 | stable |
| `knowledge/data_sources.md` | Thermos/CELIA/SNOP/opc 四源特征、选用与借用规则 | stable |
| `knowledge/pitfalls.md` | 不透明度类踩坑索引 | stable |

## 5. 示例问答（验收基准）

### Q1: 2D 能用多群不透明度表吗？
**A**: **不能直接消费**。2D 辐射输运是单群（灰体）扩散：`M20_Transport` 要求
`freepath(hydro,mid,rho,t)→λ[cm]` 回调，每单元 1 个 λ 值（`M20_Transport.r:L161`）；
`Mat2013_LoadOpa/LoadTab` 被作者禁用（"not tested software"）。
两条路：解析拟合（标准做法，λ=a·T^s/ρ^r）或 LoadMF 读单群表自写插值回调
（见 `knowledge/freepath_mechanism.md`；迁移指南 §2.1、§7.3）。

### Q2: 四个不透明度数据源怎么选？
**A**: 见 `knowledge/data_sources.md`。优先级与 Multi_BACK 原生用法一致：
元素→Thermos 多群（43 元素）；D/C 系→CELIA；Ti→SNOP（30 群）；SiO2 族/聚合物/水等
→hyades opc 单群平均（含借用规则：LiD→Li 表、WC→W 表、SS→Fe 表、碳族→C 表）。

### Q3: 多群表怎么聚合成单群？
**A**: EOS-tools `--opacity-groups 1`（Rosseland 用 dB/dT 调和矩、Planck 用 B 算术矩，
迁移指南 §6.1）；hyades opc 表本身就是单群平均，用 `opc2sgo.py` 转 sgo。
2D 用法则对 Rosseland 平均自由程做 log10 λ = a + s·logT + r·logρ 最小二乘拟合
（`gen_material_functions.py:L53-L79`）。

## 6. 关键源码入口

| 想理解 | 看哪个文件 |
|---|---|
| 2D 输运驱动与 freepath 回调 | `r94/m2d-core-9.1/M20_Transport.r:L106,L157-L164` |
| opafun 逐材料执行 | `r94/m2d-core-9.1/Material.r:L596-L605`（Material_Freepath） |
| 解析自由程示例 | `Material.r:L57-L61`（Al）、`L110-L121`（Au）、`L432-L437`（Ti） |
| 迁移材料拟合式 | `Material_mig.r`（56 个函数，注释含拟合系数与 rms） |
| 被禁用的表加载 | `r94/matter-3.1/Mat2013_LoadOpa.r:L22`、`Mat2013_LoadTab.r:L19` |
| 1D 多群加载 | `r94/MULTI-IFE-2015/m150304.f95:L3040`（load_table_multi） |
| 1D 群结构推导 | `m150304.f95:L3345`（frequencies） |
| Rosseland 拟合实现 | `work/eos_opacity_tools/gen_material_functions.py:L53-L79` |

## 7. 待办

- [ ] 2D 辐射求解器（M19_Radia）的数值算法细节暂归 multi-architecture，后续视需要单列

## 8. 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建（knowledge 4 篇） | claude |
