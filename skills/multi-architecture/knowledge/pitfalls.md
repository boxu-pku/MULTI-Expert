---
title: 架构/编译/运行环境类踩坑集（multi-architecture 摘要索引）
skill: multi-architecture
category: pitfalls
source_anchors:
  - MULTI-2D_梳理文档.md §12
  - r94/m2d-core-9.1/M20_Step.r:L132
doc_ref: "MULTI-2D_梳理文档.md §12（常见注意点）"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 踩坑
  - 编译
  - 环境
  - 索引
---

# 架构/编译/运行环境类踩坑集

## 1. 环境类（梳理文档 §12）

| 现象 | 根因 | 修复 |
|---|---|---|
| `x.2.*: command not found` | $MULTI 未设或 boot-3.2 不在 PATH | `export MULTI=<根>`; `export PATH=$PATH:$MULTI/r94/boot-3.2:.` |
| 算例后台"卡死" | ktag 残留（上次异常退出） | `rm ktag` 后重跑 |
| GUI 打不开 | 无 X11 | X11 forwarding / VNC |
| 改了模块源码算例没变 | 未重编译该模块 lib.a | `cd r94/<mod> && x.2.library`，再重编算例 |

## 2. 编译类

| 现象 | 根因 | 修复 |
|---|---|---|
| `can't translate *.r` | r94 语法错 | 例程引用写 `'name(N)'`（单引号+参数个数），梳理文档 §12 |
| 链接缺符号 | DEPENDENCES 不全/依赖未编译 | `x.2.linklist` 查依赖；先编依赖模块 |
| 删了 LOCK 不重装 | INSTALL 逻辑 | 删 LOCK 后重跑 `./INSTALL`（梳理文档 §7） |

## 3. 运行类

| 现象 | 根因 | 修复 |
|---|---|---|
| `M20_Step: more than 32 time step reductions`（`M20_Step.r:L132`） | 子步持续失败 | 查 output 定位；常见为表越界（见 agent/pitfalls/eos-density-range-limit.md） |
| 案例目录一堆 `0`/`1.2e-9` 文件 | 上次运行的快照 | Case→Clear 按 FILELIST 清理（validation_cases 禁止！） |
| 物态表"分群不对应" | 不同案例用不同群结构（如 AU_op03 是 0.3 μm 群） | 换材料时对应群结构（梳理文档 §12） |

## 4. 关联档案

- 表格式类坑：`multi-eos-format/knowledge/pitfalls.md`
- 1D 类坑：`multi-1d-ife/knowledge/pitfalls.md`
- 中央陷阱库：`agent/pitfalls/`

## 5. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
