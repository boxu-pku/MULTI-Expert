---
title: MULTI-2D 软件构成与目录结构总览
skill: multi-architecture
category: overview
source_anchors:
  - MULTI-2D_梳理文档.md §1-§2
  - README.md
  - R94:L7-L16
doc_ref: "MULTI-2D_梳理文档.md §1, §2"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 架构
  - 目录结构
  - 软件构成
---

# MULTI-2D 软件构成与目录结构总览

> **TL;DR**：MULTI-2D = 1D/2D 辐射磁流体力学程序（ICF/HEDP/激光-等离子体/重离子束）。2D 物理核心 = m2d-* 模块族（三角形非结构网格 + 拉格朗日/欧拉/ALE）；1D = MULTI-IFE-2015。外围环境是 r94 模块化脚本体系（C + 自定义 r94 语言，少量 Fortran）。

## 1. 软件构成（梳理文档 §1）

- **物理核心**：`m2d-core-9.1`（总驱动）、`m2d-hydro2-7.0.4`（MHD 拉格朗日流体）、
  `m2d-radia-8.0`（辐射输运）、`m2d-heat-7.0`（电子热传导）、`m2d-ray-7.0`（激光光追）、
  `m2d-hib-7.0`（重离子束）、`m2d-ALE19-8.0`（ALE 投影）、`m2d-geometry-7.0`（几何拓扑）
- **网格生成**：`malla-6.0` + 公共域 `triangle`（Shewchuk）
- **物态/光学**：`matter-3.1` + `mat_*` 数据模块 + 迁移的 `mat_<X>-1.0`
- **GUI/后处理**：`ProgManager-1.4`、`CaseManager-1.1`、`mpp22-2.1`、`mpp13-3.1`、`mgs-4.1` 等
- **1D**：`MULTI-IFE-2015`（见 multi-1d-ife skill）
- 开发者：Rafael Ramis（UPM）等；许可 MIT（`LICENCE`）

## 2. 目录结构（梳理文档 §2）

```
MULTI-2D.2026.3/
├── README.md / INSTALL / R94 / LICENCE
├── .s96_base            # 模块路径表（核心！见 compile_chain.md）
├── 2026-06-16*.log      # 安装日志
├── archive/             # 各模块原始打包（plain tar）
├── installer/           # 安装脚本集合
├── r94/                 # 全部模块源代码 + 编译产物(lib.a) + 物态表 + 文档
│   ├── boot-3.2/        # 模块管理与编译驱动脚本（x.2.* 系列）
│   ├── kernel-4.4/、lib-4.3/、libA-1.2/、transl-4.3/   # 内核与基础库
│   ├── m2d-*/           # 2D 物理模块族
│   ├── matter-3.1/、mat_*/  # 物态接口与数据
│   ├── 26_MULTI_documents/  # PDF 文档（tutorial/multi_manual/r94_manual 等）
│   └── MULTI-IFE-2015/  # 1D 程序与表库
├── cases/               # 标准算例（22 个 M2D_* + 4 个 2015*）
├── validation_cases/    # 47 个材料验证算例（永久保留）
├── work/                # 默认工作目录；eos_opacity_tools/ 为工具实体
├── agent/               # MULTI-Expert 治理目录（本 skill 系统）
└── .claude/skills/      # MULTI-Expert skill 集合
```

## 3. 两个程序的关系

| | 2D（m2d-*） | 1D（MULTI-IFE-2015） |
|---|---|---|
| 语言 | r94 → C → gcc | 自包含 Fortran（gfortran） |
| 网格 | 三角形非结构 | 一维拉格朗日 |
| 辐射 | 单群灰体扩散 | 多群非 LTE |
| 入口 | 各算例 `User.r` 的 `entry multi2d()` | `data.in`（namelist） |
| 表消费 | IEOS 单表 + 解析 opafun | 六表（eeos/ieos/z/planck/ross/eps） |

详见各自 skill：本 skill（2D 架构）、`multi-1d-ife`（1D）。

## 4. 安装（梳理文档 §7）

`./INSTALL` 依次执行 installer/ 下脚本：解 archive/ → transl 翻译 → gcc 编译 →
ar 归档 → 建 `.s96_base`/`cases/`/`work/`/`R94`。重装某模块：删其 `LOCK` 文件后重跑 INSTALL。
依赖：gcc、gfortran、X11 开发包、xterm。

## 5. 延伸阅读

- `knowledge/compile_chain.md`（模块体系与编译链）
- `knowledge/m2d_core.md`（2D 核心模块）
- `knowledge/cases_and_gui.md`（算例与 GUI）

## 6. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
