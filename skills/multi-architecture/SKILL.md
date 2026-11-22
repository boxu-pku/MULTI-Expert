---
name: multi-architecture
description: |
  MULTI-2D 软件架构专家。解释 r94 模块化体系（约 50 个模块、MODINFO/DEPENDENCES/FILELIST）、
  .s96_base 路径表与别名机制、r94 语言→C→gcc 编译链（boot-3.2/x.2.* 脚本）、
  2D 核心模块族（m2d-core/hydro2/radia/heat/ray/hib/ALE/malla/geometry）、
  hydro 数据结构与 M20_Step 时间推进、GUI（R94/ProgManager/Manager2015/mpp22）与后处理。
  触发词：架构, 模块, r94, MODINFO, DEPENDENCES, .s96_base, 别名, x.2.library, x.2.build,
  编译链, m2d-core, m2d-hydro2, m2d-radia, m2d-heat, m2d-ray, m2d-hib, ALE, malla,
  triangle, M20_Step, hydro 结构体, User.r, entry multi2d, R94, ProgManager, Manager2015,
  mpp22, GUI, 后处理, 快照
triggers:
  - 架构
  - 模块
  - r94
  - MODINFO
  - DEPENDENCES
  - .s96_base
  - 别名
  - x.2.library
  - x.2.build
  - 编译链
  - m2d-core
  - m2d-hydro2
  - m2d-radia
  - m2d-heat
  - m2d-ray
  - m2d-hib
  - ALE
  - malla
  - triangle
  - M20_Step
  - hydro 结构体
  - User.r
  - entry multi2d
  - R94
  - ProgManager
  - Manager2015
  - mpp22
  - GUI
  - 后处理
  - 快照
  - kernel-4.4
  - transl-4.3
when_to_use: |
  1. 用户问 MULTI-2D 整体架构/模块组成（"这个项目怎么组织的"、"m2d-* 模块都是什么"）
  2. 用户问 r94 语言与编译（"x.2.library 做了什么"、"User.r 怎么变成可执行文件"、"entry multi2d 是什么"）
  3. 用户问模块解析（".s96_base 是什么"、"别名机制"、"DEPENDENCES 怎么递归链接"）
  4. 用户问 2D 求解流程（"M20_Step 每步做什么"、"hydro 结构体有哪些字段"）
  5. 用户问 GUI/后处理（"R94 启动什么"、"mpp22 怎么用"、"快照文件 .d 是什么"）
  6. 用户问标准算例库（"22 个 M2D_* 算例都是什么"）
when_not_to_use: |
  - 表文件格式（IEOS/mgo/sgo） → multi-eos-format
  - 不透明度物理与数据源 → multi-opacity
  - 1D 程序（m150304.f95） → multi-1d-ife
  - 材料清单 → multi-materials-db
  - 实际跑算例 → multi-case-runner
  - 实际改材料函数/迁移 → multi-material-migration
layer: knowledge
phase: 1
status: stable
created: 2026-08-11
last_updated: 2026-08-11
owner: claude
---

# multi-architecture — MULTI-2D 软件架构专家

## 1. 角色与边界

### 1.1 我是做什么的

回答 MULTI-2D 软件架构问题：r94 模块化体系、编译链、2D 核心模块族与求解流程、
GUI/后处理、标准算例库。一手来源是 `MULTI-2D_梳理文档.md`（内容详尽且已验证），
本 skill 做摘要导航 + 源码锚点。

### 1.2 我不做什么

| 用户问题类型 | 归属 skill |
|---|---|
| 表文件格式 | `multi-eos-format` |
| 不透明度物理/数据源 | `multi-opacity` |
| 1D 程序细节 | `multi-1d-ife` |
| 材料清单 | `multi-materials-db` |
| 实际跑算例 | `multi-case-runner` |

## 2. 行为协议

按通用协议。本 skill 要点：

- **架构问题先引梳理文档**：`MULTI-2D_梳理文档.md` §1-§12 是权威总览，回答时给"摘要+§节锚点"
- **源码问题给行号**：r94 模块下的 .r 文件 + boot-3.2 脚本都有精确行号
- **运行操作不动手**：跑算例推给 multi-case-runner

## 3. 知识维护规则

`MULTI-2D_梳理文档.md` 是一手来源；本 skill 知识条目是摘要层。

## 4. knowledge/ 子目录索引

| 文件 | 内容 | 当前状态 |
|---|---|---|
| `knowledge/overview.md` | 软件构成与目录结构总览 | stable |
| `knowledge/compile_chain.md` | r94 模块体系、.s96_base、x.2.* 编译链 | stable |
| `knowledge/m2d_core.md` | 2D 核心模块族、hydro 结构体、M20_Step 求解流程 | stable |
| `knowledge/cases_and_gui.md` | 标准算例库、GUI/后处理、快照文件 | stable |
| `knowledge/pitfalls.md` | 架构/编译类踩坑索引 | stable |

## 5. 示例问答（验收基准）

### Q1: User.r 是怎么变成可执行文件的？
**A**: 见 `knowledge/compile_chain.md §2`。r94 脚本先由 transl-4.3 翻译成 C
（`x.2.libgen:29-31` 调 `r94` 翻译器），`gcc -c -O -DLinux` 编译（`x.sys.compile:4`），
`ar r lib.a` 归档（`x.sys.archive:4`）；`x.2.build` 生成 main.c（`x.2.build:15-27`，
调 DStart/DLibera/DStop）并链接全部依赖 lib.a（`x.sys.ld:4`）。
入口约定：`entry multi2d()` 或 `entry multi()`。

### Q2: .s96_base 是什么？别名机制怎么工作？
**A**: 模块路径表，格式 `类型:挂载目录:模块名:`（`.s96_base:1-10`）。
`default` 是当前版本，`alias` 把旧版本号映射到当前（如 m2d-core-7.0.9→m2d-core-9.1，
`.s96_base:29-34`）。`x.0.find` 用 `fgrep ":$key:"` 查表（`x.0.find:11,36,51`）。
User.r 的 DEPENDENCES 写旧版本号也能透明解析。

### Q3: M20_Step 每个时间步做什么？
**A**: 见 `knowledge/m2d_core.md §2`。HydroEOS → （可选 Relax/fusion）→
M20_Hydrodynamics → M20_HIB/M20_RayTracing → M20_Transport；任一步 status>1 则
dt 减半重试（超 32 次 STOP）（`M20_Step.r:L63-L139`）。

## 6. 关键源码入口

| 想理解 | 看哪个文件 |
|---|---|
| 架构总览（权威） | `MULTI-2D_梳理文档.md` |
| 模块清单（MODINFO） | `r94/<module>/MODINFO` |
| 路径表 | `.s96_base` |
| 编译脚本 | `r94/boot-3.2/x.2.library`、`x.2.build`、`x.2.linklist`、`x.0.find` |
| 总驱动 | `r94/m2d-core-9.1/M20_Step.r:L63` |
| hydro 结构体 | `r94/m2d-core-9.1/Hydro.r:L141` |
| 输运驱动 | `r94/m2d-core-9.1/M20_Transport.r:L106` |
| 流体驱动 | `r94/m2d-core-9.1/M20_Hydrodynamics.r:L146` |
| GUI 入口 | `R94`（根目录，L7-L16） |

## 7. 待办

- [ ] m2d-radia-8.0 内部数值算法（M19_Radia）如需深入再单列条目

## 8. 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建（knowledge 5 篇） | claude |
