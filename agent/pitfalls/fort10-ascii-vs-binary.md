---
title: IFE-2015 fort.10 是 ASCII，MULTI1Dvisual2.2 要二进制（互不兼容）
category: 可视化
severity: 阻塞（不能跑）
first_seen: 2026-08-10
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - fort.10
  - ASCII
  - 二进制
  - MULTI1Dvisual
  - plot_1d_validation
source_anchors:
  - r94/MULTI-IFE-2015/m150304.f95:L368
  - 材料迁移验证规范.md §E
  - work/eos_opacity_tools/plot_1d_validation.py:L10-L21
---

# IFE-2015 fort.10 是 ASCII，MULTI1Dvisual2.2 要二进制（互不兼容）

## 错误信息 / 现象

用 `$MULTI_APP/MULTI1Dvisual2.2`（GUI 工具）打开 IFE-2015 算例的 fort.10：
读不出记录 / 解析错乱。

## 原因

两种 fort.10 是**不同格式**：

| 程序 | fort.10 格式 | 适用工具 |
|---|---|---|
| MULTI-IFE-2015（m150304.f95，本项目） | **ASCII**（`form='formatted'`，e12.5） | `plot_1d_validation.py` |
| Windows Multi1D | **二进制** | MULTI1Dvisual2.2 |

- 根因分类：**格式同名不同物**
- ASCII 版结构：头计数+变量名+索引 ×2 节，之后每条记录定长值序列
  （变量 R/PT/TE/PE/TI/ZI/XC/X/TR…）

**源码机制**：
```
r94/MULTI-IFE-2015/m150304.f95:L368
   open(10,file='fort.10',form='formatted')   ← formatted = ASCII
```

## 修复

- IFE-2015 结果可视化：用 `plot_1d_validation.py`（热图+剖面）：
  ```bash
  python3 $MULTI/work/eos_opacity_tools/plot_1d_validation.py validation_cases/<X>Check
  ```
- 需要 GUI 交互查看时：需另行把 ASCII 转换为 Windows Multi1D 二进制格式（未实现）。

## 锚点

- `r94/MULTI-IFE-2015/m150304.f95:L368` — fort.10 的 formatted 打开方式
- `材料迁移验证规范.md §E` — 两种格式不兼容的说明
- `work/eos_opacity_tools/plot_1d_validation.py:L10-L21` — ASCII fort.10 结构注释

## 预防

- 看到 fort.10 先确认来源程序，再选解析工具。
- 解析逻辑参照 MULTI1Dvisual2.2 的 `legacy/scanFile.py` 变量命名（R/PT/TE/PE/ZI/XC/X/TR…）。

## 延伸

- 相关踩坑：`missing-e-exponent.md`（ASCII fort.10 的 e12.5 省略 e 问题）

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
