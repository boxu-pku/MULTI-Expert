---
title: Fortran 定宽输出省略 e 指数（"8.33534443-110"）
category: 文件格式
severity: 阻塞（不能跑）
first_seen: 2026-08-10
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - Fortran
  - e12.5
  - 指数
  - Epoxy
  - fort.10
source_anchors:
  - work/eos_opacity_tools/batch_migrate.py:L99-L128
  - work/eos_opacity_tools/plot_1d_validation.py:L82-L86
  - r94/MULTI-IFE-2015/m150304.f95:L3615
---

# Fortran 定宽输出省略 e 指数（"8.33534443-110"）

## 错误信息 / 现象

### 形式 1：EOS 源表（Epoxy eos_502.dat 等）
```
 8.33534443-110      ← 3 位指数时 Fortran 省略 "e"，实为 8.33534443e-110
```

### 形式 2：1D 输出 fort.10
```
-0.33689-232        ← 实为 -0.33689e-232
```

## 原因

Fortran 定宽格式（如 `e15.8` / `e12.5`）在指数为 3 位数时宽度不够，按标准**省略字符 e**
以保证数字部分完整。Python `float()` 无法解析这种形式。

- 根因分类：**源文件问题 / 输出格式固有行为**
- fort.10 数值写出用 `(e12.5)`：`r94/MULTI-IFE-2015/m150304.f95:L3615`
  （另 L3620/L3625 同格式）

## 修复

读取端用正则**在最后一个 +/- 号前插回 e**：

```python
import re
m = re.match(r"^([+-]?\d+\.?\d*)([+-]\d+)$", s)   # "8.33534443-110"
if m:
    v = float(f"{m.group(1)}e{m.group(2)}")        # → 8.33534443e-110
```

已内置于：
- `batch_migrate.py:fix_missing_e_fields()`（L99-L128）——EOS 源表转换前自动修复
- `plot_1d_validation.py`（L82-L86）——解析 fort.10 时自动处理

## 锚点

- `work/eos_opacity_tools/batch_migrate.py:L117-L120` — 插 e 正则修复
- `work/eos_opacity_tools/plot_1d_validation.py:L82-L86` — fort.10 解析同款处理
- `r94/MULTI-IFE-2015/m150304.f95:L3615` — fort.10 的 `(e12.5)` 写出格式

## 预防

- 任何手工解析 MULTI 表文件/fort.10 的脚本都要带这个正则兜底。
- 不要试图"修复"fort.10 输出——那是 Fortran 标准行为，在读取端处理。

## 延伸

- 相关踩坑：`windows-inf-field.md`、`fort10-ascii-vs-binary.md`

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
