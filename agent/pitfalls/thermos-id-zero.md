---
title: Thermos 表头 id=0，1D 输入卡用 *_id=0 匹配任意
category: 表加载
severity: 警告（能跑但结果错）
first_seen: 2026-08-10
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - Thermos
  - id=0
  - 输入卡
  - planck_id
  - ross_id
source_anchors:
  - r94/MULTI-IFE-2015/m150304.f95:L2944
  - r94/MULTI-IFE-2015/m150304.f95:L2999
  - MULTI-2D_材料库清单.md §三
---

# Thermos 表头 id=0，1D 输入卡用 *_id=0 匹配任意

## 错误信息 / 现象

Thermos 迁移表的表头 id 字段是 0。1D 输入卡若写 `planck_id=27003000` 之类的
"猜的 id"，表会**找不到**（加载摘要中该表缺失或群数 0）。

## 原因

1D 表匹配规则：`if((id==idin.or.idin==0).and...)` —— 输入卡 `*_id=0` 是通配符，
匹配文件中第一张对应类型的表；非 0 id 必须精确等于表头第 1 字段的整数值。

**源码机制**：
```
r94/MULTI-IFE-2015/m150304.f95:L2944  (EOS 匹配)
   if((id==idin.or.idin==0).and.itype==1)then
r94/MULTI-IFE-2015/m150304.f95:L2999  (群表匹配)
   if((id==idin.or.idin==0).and.itype>1)then
```

## 修复

- Thermos 迁移表（`tables/X_Thermos.PLANCK/.ROSSELAND/.ZEFF`）输入卡写 `*_id=0`。
- 或先用工具读真实 id：`python3 -c "print(int(float(open('<文件>').readline()[0:15])))"`。
- 命名约定见 `MULTI-2D_材料库清单.md §三`。

## 锚点

- `r94/MULTI-IFE-2015/m150304.f95:L2944` — EOS 表 id 匹配行
- `r94/MULTI-IFE-2015/m150304.f95:L2999` — 群表 id 匹配行
- `MULTI-2D_材料库清单.md §三` — 1D 表库命名约定（Thermos id=0）

## 预防

- 迁移生成的算例由 `batch_migrate.py` 自动读 `head_id()` 填 id（L58-L62），无需手工。
- 手工写输入卡时：先读表头 id 再填，或用 0 通配。

## 延伸

- 相关踩坑：`degenerate-opacity-group.md`

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
