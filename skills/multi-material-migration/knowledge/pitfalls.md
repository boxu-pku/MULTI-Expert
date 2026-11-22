---
title: 迁移类踩坑集（multi-material-migration 摘要索引，含历史事故）
skill: multi-material-migration
category: pitfalls
source_anchors:
  - 材料迁移验证规范.md §6
  - MULTI-2D_材料库迁移指南.md §8
  - agent/pitfalls/
doc_ref: "材料迁移验证规范.md §6（历史问题与修复记录）"
created: 2026-08-11
last_verified: 2026-08-31
verifier: claude
status: stable
tags:
  - 踩坑
  - 迁移
  - 历史事故
  - 索引
---

# 迁移类踩坑集

> **迁移前必读**：以下是真实发生的事故，每条都有完整档案（`agent/pitfalls/`）与
> 规范记录（`材料迁移验证规范.md §6`）。

## 1. 历史事故（2026-08-10 ~ 08-13，迁移前必读）

### ① Ne 退化子表（能跑但结果错）
Thermos 源文件第 50 子表 f1==f2=1200 eV → 1D load_table_multi 误判结束 →
后 28 群**静默丢弃**（77/78 群）。修复：删退化子表；`batch_migrate.py` 内置
`drop_degenerate_groups()`。**教训：验收核对群数（B3）**。
→ `agent/pitfalls/degenerate-opacity-group.md`

### ② Kr 算例物理崩坏（算例设计错）
固体密度（2.5 g/cc）算例辐射坍缩，ρ 冲出表上限（1890 vs 10）。
修复：气体密度（3.749e-3），误差 1e-13。**教训：选例先查表覆盖**。
→ `agent/pitfalls/gas-vs-solid-case-density.md`

### ③ 压强单位 bug（最凶险：能跑、守恒、结果错）
hyades→MPa 误用 ÷1e11（正确 ×1e-7），20 种材料压强小 1e4 倍。
首轮验收靠能量守恒**未能发现**，由 Kr 剖面 Pe≈0 暴露。
修复后全部重迁移重跑，与源表绝对值对照（≤3%）复验。
**教训：验收必须含与源表的物理量绝对值对照，不能只看守恒量**。
→ `agent/pitfalls/pressure-unit-confusion.md`

### ④ 能量轴 ×1000（2026-08-13，同类手写链事故）
手工转换链把 erg/g→J/g 误用 erg/g→J/kg 系数（恰差 1000），41 张迁移表能量轴膨胀：
压缩后温度恒 ~0 而密度/压力正常，**B1-B6 全部查不出**。
由 PdV 热力学一致性检查（比值 ≈1 vs ≈1000）全库审计暴露，已用 EOS-tools 重转修复。
**教训：同③——手写转换链是万恶之源；新增 PdV 检查入验收（S4a）**。
→ `agent/pitfalls/migrated-eos-energy-scale-1000x.md`

### ⑤ FEOS 自带转换器双 bug（2026-08-13）
`feos2multi.py`/`feos2r94.py` 布局（密度主序 vs 能量主序）+ 能量单位（×100）双 bug，
产物 P/T 振荡、RH 无解。**禁用**；FEOS→MULTI 走 `eos_convert.py --from feos --to multi`。
→ `agent/pitfalls/feos-converter-layout-energyunit.md`

### ⑥ EOS-tools MULTI 产物入库三步后处理（2026-08-31，DTFEOS 检验）
对 ⑤ 的正确路径补三条边界：`--from feos` 对**同位素混合物**（同 Z 不同 A，DT 的
D/T 均 Z=1）报 duplicate atom_z——绕行 FEOS 自产 SESAME 分表 `--from sesame --to multi`；
EOS-tools **不做**固定 de 列 P(ρ) 单调化（DT 实例 28/96 低能列非单调，须
`maximum.accumulate` 后处理）；表头 ID 写 1，须按惯例改 matnum×10⁴+304/305。
校验：check_multi_file + 与源 .data.txt 在 T(rho,de) 交叉对拍（DT：P 中位 0.03%）
+ 1D 算例（DTFEOSCheck 能量误差 3.7e-10）。
→ `agent/pitfalls/eos-tools-feos-isotope-duplicate-z.md`、`eos-tools-multi-monotonic-postfix.md`

## 2. 文件级高频坑

| 坑 | 处理 | 档案 |
|---|---|---|
| CRLF 行尾（head line size != 60） | fix_multi_file.sh | `crlf-line-endings.md` |
| Windows `-1.#INF000e+000` | fix_multi_file.sh | `windows-inf-field.md` |
| Fortran 缺 e 指数 | batch 自动修 | `missing-e-exponent.md` |
| IEOS 能量主序 reshape 读反 | reshape(NE,NR) | `ieos-layout-order.md` |
| EOS-tools zeff 头 1D 不认 | 改 ` 0.60000000E+01` | `zeff-type-string-variants.md` |
| Zeff 温度按 eV（实 keV） | — | `zeff-kev-not-ev.md` |
| Thermos 表头 id=0 | 输入卡 `*_id=0` | `thermos-id-zero.md` |

## 3. 数据局限（非迁移错误，但验收会 CAVEAT）

- Diamond/Cliquid：源 EOS 密度下限高 → 烧蚀越界（`eos-density-range-limit.md`）
- 温度回折截断（multi_temperature_trims）：迁移指南 §8-4
- 老表冷区负 P/T：inegpre / positive_P（迁移指南 §8-5）

## 4. 流程红线

1. 不跳验收条目；**子 agent 必须新起**（独立验收）
2. 机器 ACCEPT ≠ 完成——**用户人工确认后才标 ✅**
3. `validation_cases/` 产物**永久保留**，禁止 CLEAR
4. 工具实体不移动（`work/eos_opacity_tools/` 路径被脚本写死）

## 5. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
