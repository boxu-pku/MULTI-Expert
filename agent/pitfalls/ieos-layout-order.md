---
title: IEOS p/t 是能量主序 p[j*NR+i]（E 行 ρ 列），numpy 默认 reshape 会读错
category: 文件格式
severity: 警告（能跑但结果错）
first_seen: 2026-08-10
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - IEOS
  - 布局
  - reshape
  - 能量主序
  - numpy
source_anchors:
  - r94/matter-3.1/Mat2013_LoadMF.r:L47-L50
  - r94/matter-3.1/Mat2013_EleTab.r:L66-L67
  - MULTI-2D_材料库迁移指南.md §8-7
---

# IEOS p/t 是能量主序 p[j*NR+i]（E 行 ρ 列）

## 错误信息 / 现象

无报错。用 numpy 默认 `(NR, NE)` reshape 解析 IEOS 的 p/t 数组后，
得到的 (ρ,E) 对应关系错误，与源表对照出现**假象大偏差**（2026-08 两次验收都踩过）。

## 原因

IEOS 表的 p/t 数组布局是**能量主序**：前 NR 个值对应第一个 ΔE（即 E 行 ρ 列），
索引公式 `p[j*NR+i]`（j=能量索引，i=密度索引）。

numpy 默认 C 顺序 `reshape(NR, NE)` 会把前 NE 个值当作第一行——与 MULTI 约定正好相反。

**源码机制**（文档注释 + 实现双重证据）：
```
r94/matter-3.1/Mat2013_LoadMF.r:L47-L50
   "the first NR values correspond to the first energy increment"
r94/matter-3.1/Mat2013_EleTab.r:L66-L67
   T_e[j]=tot_T[j*nr+i];  P_e[j]=tot_P[j*nr+i]-rho*cte*tot_T[j*nr+i];
```

## 修复

```python
p = vals.reshape(NE, NR)      # 正确：(能量, 密度)
p_ji = p[j, i]                # 等价于扁平数组 p[j*NR+i]

# 错误做法（会得到假象大偏差）：
p = vals.reshape(NR, NE)      # ✗
```

## 锚点

- `r94/matter-3.1/Mat2013_LoadMF.r:L47-L50` — 布局的文档注释
- `r94/matter-3.1/Mat2013_EleTab.r:L66-L67` — C 实现中 j*nr+i 索引的直接体现
- `MULTI-2D_材料库迁移指南.md §8-7` — 陷阱记录（物理注意事项第 7 条）

## 预防

- 任何手工解析 IEOS 的脚本：reshape 用 `(NE, NR)`，或按 `j*NR+i` 索引。
- mgo/sgo 的 `lo[NT×NR]` 同样是"T 行 ρ 列"主序，同法处理。
- 与源表对照验证时若出现"系统性大偏差"，先怀疑布局读反。

## 延伸

- 相关踩坑：`pressure-unit-confusion.md`（同类"无报错但结果错"）
- `split_ieos_table.py:L77`（`布局: p/t 为 (ne, nr) 即 p[j*nr+i]`）

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
