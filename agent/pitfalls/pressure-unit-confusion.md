---
title: dyne/cm²→MPa 是 ×1e-7 非 ÷1e11（2026-08-10 单位事故）
category: 单位换算
severity: 警告（能跑但结果错）
first_seen: 2026-08-10
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 单位
  - 压强
  - MPa
  - Mbar
  - hyades
  - 能量守恒查不出
source_anchors:
  - work/eos_opacity_tools/batch_migrate.py:L137-L138
  - MULTI-2D_材料库迁移指南.md §8-9
  - 材料迁移验证规范.md §6-3
---

# dyne/cm²→MPa 是 ×1e-7 非 ÷1e11（2026-08-10 单位事故）

## 错误信息 / 现象

无报错。转换后的表**压强整体小 1e4 倍**，程序照常运行、能量守恒依然满足，
由 Kr 算例剖面图 Pe≈0 异常才暴露。

## 原因

2026-08-10 首次批量迁移时，`batch_migrate.py` 的 hyades→MPa 换算误用 `÷1e11`
（那是 dyne/cm²→**Mbar** 的系数；正确为 **×1e-7**，1 MPa = 1e7 dyn/cm²）。

- 根因分类：**用户操作错（转换脚本 bug）**
- **关键教训：能量守恒类指标发现不了单位错误**——错单位的表自洽，程序照样守恒。
  必须与源表做**物理量绝对值对照**。

**修复后代码**：
```python
# work/eos_opacity_tools/batch_migrate.py:L137-L138
P_mpa = np.array(P, dtype=float) * 1e-7      # dyne/cm2 → MPa (1 MPa = 1e7 dyn/cm2)
E_jpg = np.array(E, dtype=float) / 1e4       # erg/g → J/g
```

## 修复

1. 修正换算系数（已修，L137）
2. 全部 20 种 hyades 源材料**重迁移重跑**
3. 复验时与源表直接数值对照（≤3%）确认

## 单位速查（防再犯）

| 转换 | 系数 |
|---|---|
| dyne/cm² → MPa | ×1e-7 |
| dyne/cm² → Mbar | ÷1e11（×1e-11） |
| erg/g → J/g | ÷1e4（×1e-4） |
| MULTI 文件能量/压强 → cgs | ×1e12 |
| MULTI 文件 T(K) → eV | ÷11604.519（1D 代码用 11605） |

## 锚点

- `work/eos_opacity_tools/batch_migrate.py:L137-L138` — 修复后的正确系数与注释
- `MULTI-2D_材料库迁移指南.md §8-9` — 事故教训（物理注意事项第 9 条）
- `材料迁移验证规范.md §6-3` — 历史问题记录第 3 条

## 预防

- **任何自定义转换链完成后，必须与源表做物理量绝对值抽查对照**（能量守恒查不出单位错）。
- 验收标准已内置：迁移验证规范 §B/§C 要求与源表对照。

## 延伸

- 相关踩坑：`ieos-layout-order.md`（同样"能跑但结果错"类）

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
