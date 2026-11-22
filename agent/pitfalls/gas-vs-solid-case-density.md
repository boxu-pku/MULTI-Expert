---
title: 验证算例密度选取：Kr 固体密度算例辐射坍缩崩坏 → 气体密度
category: 算例运行
severity: 阻塞（不能跑）
first_seen: 2026-08-10
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - Kr
  - 算例设计
  - 辐射坍缩
  - 密度
  - Air
  - 初温
source_anchors:
  - 材料迁移验证规范.md §6-2
  - MULTI-2D_材料库清单.md §四-6
---

# 验证算例密度选取：Kr 固体密度算例辐射坍缩崩坏 → 气体密度

## 错误信息 / 现象

KrCheck 用固体密度（2.5 g/cc）时：辐射驱动下材料剧烈压缩（辐射坍缩），
ρ 冲出 EOS 表上限（1890 vs 表上限 10 g/cc），算例物理崩坏。

## 原因

100 eV 辐射浴驱动下，低气压材料被辐射波压缩。若材料 EOS 表 ρ 上限不够高，
压缩后的状态越界。这是**物理预期行为**，非表格缺陷。

- 根因分类：**算例设计问题**
- 同类问题：**Air 初温需 ≥ 表 T 下限**（0.03 eV 初温若低于表下限同样越界）

## 修复

- Kr 算例改用**气体密度** 3.749e-3 g/cc（`MULTI-2D_材料库清单.md §四-6`），
  修复后能量误差 1e-13。
- 算例设计原则（验证规范 §3）：先查表覆盖，再定 r0/te0/ti0。

## 锚点

- `材料迁移验证规范.md §6-2` — Kr 算例修复记录
- `MULTI-2D_材料库清单.md §四-6` — KrCheck 气体密度说明
- `validation_cases/KrCheck/data.in` — 现行算例（r0 为气体密度）

## 预防

- 新材料验证算例：r0 取**固体密度**前先确认表 ρ 上限 ≥ 10×r0（压缩裕量）；
  不够则改用气体密度。
- te0/ti0 ≥ 表 T 下限。

## 延伸

- 相关踩坑：`eos-density-range-limit.md`
- 算例模板：`work/eos_opacity_tools/batch_migrate.py` CASE_TEMPLATE（L172-L243）

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
