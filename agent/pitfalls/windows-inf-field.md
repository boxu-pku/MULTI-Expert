---
title: Windows MSVC 输出 "-1.#INF000e+000" 字段致解析失败
category: 文件格式
severity: 阻塞（不能跑）
first_seen: 2026-08-10
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - -INF
  - Windows
  - MSVC
  - Thermos
  - fix_multi_file
source_anchors:
  - r94/matter-3.1/Mat2013_LoadMF.r:L263-L265
  - work/eos_opacity_tools/fix_multi_file.sh:L28-L29
  - MULTI-2D_材料库迁移指南.md §5
---

# Windows MSVC 输出 "-1.#INF000e+000" 字段致解析失败

## 错误信息 / 现象

### 形式 1：check_multi_file.py
```
✗ <文件>
    ValueError: could not convert string to float: '-1.#INF000e+00'
```

### 形式 2：文件内容（Thermos 的 5 个文件）
```
   -1.#INF000e+000
```

## 原因

Windows MSVC 的 printf 把 -inf 输出为 `-1.#INF000e+000`，不是合法浮点字符串，
Python `float()` 与 C `atof` 语义都无法正确解析。

MULTI 的标准写法是 `"           -INF"`（15 字符定宽），读入时映射为 log 截断值 **-40**。

- 根因分类：**源文件问题**
- 受影响文件（迁移指南 §5）：`Thermos/{AuMG_Z,C_Z,Ne_Planck,Ne_Rosseland,V_Z}.dat`

**源码机制**：
```
MULTI 标准 -INF 的处理：r94/matter-3.1/Mat2013_LoadMF.r:L263-L265
   if(strcmp("           -INF",field)==0){ v[i]=-40; errflag1=1; }
```

## 修复

```bash
$MULTI/work/eos_opacity_tools/fix_multi_file.sh <文件>
# 内部执行（fix_multi_file.sh:L28-29）：
#   sed -i 's/-1\.#INF000e+000/           -INF/g'
#   sed -i 's/-1\.\#INF[0-9.e+]*/           -INF/g'
```

`batch_migrate.py` 的 `dos2unix_file(src, dst, fix_inf=True)` 已内置此修复。

## 锚点

- `r94/matter-3.1/Mat2013_LoadMF.r:L263-L265` — MULTI 标准 `-INF` → -40 的读取语义
- `work/eos_opacity_tools/fix_multi_file.sh:L28-L29` — 修复 sed 表达式
- `MULTI-2D_材料库迁移指南.md §5` — 已知问题文件清单

## 预防

- Thermos 系列文件迁移时一律 `fix_inf=True`（batch_migrate 已内置）。
- 修复后跑 `check_multi_file.py` 验证。

## 延伸

- 相关踩坑：`crlf-line-endings.md`、`missing-e-exponent.md`

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
