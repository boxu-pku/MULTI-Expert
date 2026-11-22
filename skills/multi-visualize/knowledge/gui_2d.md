---
title: 2D 后处理入口 — R94 GUI / mpp22 / 快照结构
skill: multi-visualize
category: reference
source_anchors:
  - R94:L7-L16
  - MULTI-2D_梳理文档.md §9, §10
doc_ref: "MULTI-2D_梳理文档.md §9（后处理与可视化）"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 2D
  - mpp22
  - GUI
  - 快照
---

# 2D 后处理入口

> **TL;DR**：`./R94` 启动 GUI → Manager2015 选 case → Table 选时间帧/变量 → mpp22 出云图。快照 = 二进制时间文件 `<t>` + 描述文件 `<t>.d`。需要 X11。

## 1. 启动与流程（梳理文档 §8.1、§9）

```bash
cd $MULTI_ROOT && ./R94
# R94:L7-L12 设 MULTI/PATH；L15-L16 在 work/ 下构建并后台启动 ProgManager2025
```

1. ProgManager2025 主面板 → Launch 菜单启动 **Manager2015** 与 **mpp22**
2. Manager2015 中选 case（`cases/*`）
3. Table 窗口选时间帧 → 变量，mpp22 立刻出图（云图/矢量图）
4. 程序间 X11 ClientMessage 联动——多窗口同开时选择自动同步
5. mpp13：1995 风格动画式后处理（演示用）

**前提**：X11 环境（远程：X11 forwarding 或 VNC）。

## 2. 快照文件结构（梳理文档 §8.2、§10）

| 文件 | 内容 |
|---|---|
| `cases/<case>/<t>`（如 `0`、`1.2e-9`、`5`） | 时刻 t 的二进制快照（HydroOutputAtTimes 写出） |
| `cases/<case>/<t>.d` | 字段描述：变量名 + 偏移 + 长度 |

常用变量：`rho`、`T`/`Te`/`Ti`、`P`/`Pe`/`Pi`、`TR`、`v`、`ne`、`depo`/`D/V`、`ct`。
自定义输出：`User.r` 里 `m2d_write("name", array)` 注册 + `hydro.output='myoutput(1)'`
（梳理文档 §9-4）。

## 3. 命令行替代（无 X11 时）

- 2D 快照是自定义二进制——程序内读写接口是 `multi_data-2.2` 模块
- 无现成 CLI 绘图脚本（与 1D 的 plot_1d_validation.py 不同）；
  需要时用 r94 环境写脚本或开 X11
- 预存结果示例：`cases/M2D_Hohlraum_110/`（100+ 时间快照）

## 4. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
