---
title: Zeff 表 T 网格是 log10(keV) 非 eV（r94 注释陈旧）
category: 文件格式
severity: 警告（能跑但结果错）
first_seen: 2026-08-10
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - Zeff
  - 电离度
  - keV
  - log10
  - 注释陈旧
source_anchors:
  - r94/MULTI-IFE-2015/m150304.f95:L2226-L2227
  - r94/matter-3.1/Mat2013.r:L31
  - MULTI-2D_材料库迁移指南.md §1.4
---

# Zeff 表 T 网格是 log10(keV) 非 eV（r94 注释陈旧）

## 错误信息 / 现象

无报错。若按 log10(T/eV) 生成或解释 Zeff 表，温度网格整体偏移 3 个数量级，
插值得到的电离度完全错误。

## 原因

- `Mat2013.r` 注释写 "NT logarithms of temperatures (eV)"——**陈旧文档**。
- 实际文件（如 `AU_op03z` 网格 -3~+2）只有按 **keV** 解释才有物理意义（1 eV~100 keV）。
- **1D 源码铁证**：`zbr` 子程序插值自变量是 `log10(t)-3`，
  即 log10(T[eV])−3 = **log10(T[keV])**。

**源码机制**：
```
r94/MULTI-IFE-2015/m150304.f95:L2226-L2227  (subroutine zbr)
   rlog = log10(r)
   tlog = log10(t)-3.        ← 对比不透明度 opa 用的是 tlog = log10(t)（L2287）
```

陈旧注释：
```
r94/matter-3.1/Mat2013.r:L31
   $$      m.zeff.lt - NT logarithms of temperatures (eV)   ← 错，实为 keV
```

## 修复

- 生成 Zeff 表：T 网格写 log10(T/keV)。EOS-tools 已按 keV 处理，与实际文件一致。
- 读取/解释既有 Zeff 表：lt 值 + 3 才是 log10(T/eV)。

## 锚点

- `r94/MULTI-IFE-2015/m150304.f95:L2226-L2227` — zbr 的 `log10(t)-3` 铁证
- `r94/matter-3.1/Mat2013.r:L31` — 陈旧注释现场
- `MULTI-2D_材料库迁移指南.md §1.4` — 差异说明（⚠ 注记）

## 预防

- 当前 2D 代码不读外部 Zeff 表（无实际影响）；**1D 用 Zeff 表时必须按 keV 处理**。
- 写新工具解析 Zeff 表时以 zbr 源码为准，不信注释。

## 延伸

- 相关踩坑：`zeff-type-string-variants.md`

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
