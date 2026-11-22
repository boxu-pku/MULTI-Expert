---
title: 可视化类踩坑集（multi-visualize 摘要索引）
skill: multi-visualize
category: pitfalls
source_anchors:
  - agent/pitfalls/fort10-ascii-vs-binary.md
  - 材料迁移验证规范.md §E
doc_ref: "材料迁移验证规范.md §E"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 踩坑
  - 可视化
  - 索引
---

# 可视化类踩坑集

| 现象 | 根因 | 处理 | 档案 |
|---|---|---|---|
| MULTI1Dvisual2.2 打不开 fort.10 | IFE-2015 是 ASCII，GUI 要二进制 | 用 plot_1d_validation.py | `agent/pitfalls/fort10-ascii-vs-binary.md` |
| fort.10 解析 float 失败 | e12.5 省略 e（`-0.33689-232`） | 脚本已内置正则；自写解析须加 | `agent/pitfalls/missing-e-exponent.md` |
| 热图断带/记录数 <50 | ns_bout 太大 | ns_bout=1 重跑 | `材料迁移验证规范.md §E` |
| 剖面压强量级离谱 | 表单位错（历史事故） | 与源表绝对值对照 | `agent/pitfalls/pressure-unit-confusion.md` |
| 2D GUI 打不开 | 无 X11 | X11 forwarding / VNC | `MULTI-2D_梳理文档.md §12` |
| 找错 fort.10 | 同名不同物（Windows Multi1D 产物混放） | 确认来源程序 | `agent/pitfalls/fort10-ascii-vs-binary.md` |

## 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
