---
title: EOS 表密度下限高致烧蚀算例越界（Diamond/Cliquid 实例）
category: 算例运行
severity: 警告（能跑但结果错）
first_seen: 2026-08-10
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - EOS
  - 密度范围
  - Diamond
  - Cliquid
  - 烧蚀
  - 表覆盖
source_anchors:
  - MULTI-2D_材料库清单.md §1.2
  - MULTI-2D_材料库迁移指南.md §8-3
---

# EOS 表密度下限高致烧蚀算例越界（Diamond/Cliquid 实例）

## 错误信息 / 现象

- DiamondCheck：能量误差 1.17e-4 超阈值（标准 <1e-6）
- CliquidCheck：0.58 ns 处崩溃

## 原因

两种材料的源 EOS 表**密度下限过高**（Diamond 0.35 g/cc、Cliquid 0.23 g/cc），
烧蚀算例中材料被加热膨胀进入稀薄区，ρ 掉出表覆盖范围，EOS 插值越界。

- 根因分类：**源数据局限（非迁移错误）**
- 同属此类：低温/相变区的 RT→RE 插值误差（迁移指南 §8-3）

## 修复

- 选例时**先查表覆盖范围**：`check_multi_file.py` 输出网格范围，
  或用 EOS-tools `eos_query.py` 查看 ρ/T 覆盖。
- 烧蚀类算例要求表 ρ 下限远低于固体密度（稀薄尾区会被扫到）。
- 数据局限材料：换更宽 EOS 源（Water 先例：2026-08-11 从窄表 eos_312 换宽表
  eos_311 后复验通过 2.4e-9）或接受局限并在清单中标注 ⚠。

## 锚点

- `MULTI-2D_材料库清单.md §1.2` — Diamond/Cliquid 的 ⚠ 标记与说明
- `MULTI-2D_材料库迁移指南.md §8-3` — RT→RE 插值误差与低温区注意
- `材料迁移验证规范.md §C1` — 验收要求"网格范围覆盖算例实际状态"

## 预防

- 迁移新材料设计验证算例时：先查 EOS 表 ρ/T 范围 ≥ 算例将到达的状态区间。
- 清单中 ⚠ 材料做烧蚀算例前必须人工评估。

## 延伸

- 相关踩坑：`gas-vs-solid-case-density.md`（另一类表范围越界）

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
