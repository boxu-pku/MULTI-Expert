---
title: 算例运行类踩坑集（multi-case-runner 摘要索引）
skill: multi-case-runner
category: pitfalls
source_anchors:
  - MULTI-2D_梳理文档.md §12
  - agent/pitfalls/
doc_ref: "MULTI-2D_梳理文档.md §12"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 踩坑
  - 运行
  - 索引
---

# 算例运行类踩坑集

| 现象 | 根因 | 处理 | 档案 |
|---|---|---|---|
| `x.2.*: command not found` | MULTI/PATH 未设 | export MULTI + PATH | `knowledge/run_protocol.md §1` |
| ktag 一直在 | 异常退出残留 | ps 确认无进程后 rm ktag | `MULTI-2D_梳理文档.md §12` |
| 1D 编译报 tables 找不到 | tables 软链失效 | 重跑 RUN（自动重建软链） | `knowledge/overview.md §2` |
| 能量误差超 1e-6 | 表越界（Kr 固体密度/Diamond 类） | 查表覆盖，改算例设计 | `agent/pitfalls/gas-vs-solid-case-density.md`、`eos-density-range-limit.md` |
| 群数比源表少 | 退化子表截断 | drop_degenerate_groups 后重迁 | `agent/pitfalls/degenerate-opacity-group.md` |
| 压强量级错（Pe≈0） | 表单位错 | 与源表对照；重迁移 | `agent/pitfalls/pressure-unit-confusion.md` |
| `more than 32 time step reductions`（2D） | 子步持续失败 | 查 output 定位子步 | `r94/m2d-core-9.1/M20_Step.r:L132` |
| 误清 validation_cases | 把验收产物当残留 | **禁止 CLEAR**；已被删则从 git/备份恢复 | `材料迁移验证规范.md §E` |
| fort.12/tables 是软链被当产物删 | 软链属性 | 重跑 RUN 重建 | `knowledge/overview.md §2` |

## 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
