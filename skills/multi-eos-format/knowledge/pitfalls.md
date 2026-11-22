---
title: 表格式类踩坑集（multi-eos-format 摘要索引）
skill: multi-eos-format
category: pitfalls
source_anchors:
  - MULTI-2D_材料库迁移指南.md §5
  - agent/pitfalls/
doc_ref: "MULTI-2D_材料库迁移指南.md §5, §8"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 踩坑
  - 索引
  - 格式
---

# 表格式类踩坑集

> **TL;DR**：本文件是格式类陷阱的摘要索引；完整档案（现象/根因/修复/预防）在 `agent/pitfalls/`。遇错先按"错误信息"列匹配。

## 1. 文件级问题（来自 Multi_BACK/Windows 源）

| 错误信息/现象 | 根因 | 快速修复 | 完整档案 |
|---|---|---|---|
| `head line size != 60` | CRLF 行尾（头变 61 字符） | `fix_multi_file.sh <文件>` | `agent/pitfalls/crlf-line-endings.md` |
| float() 报 `-1.#INF000e+00` | Windows MSVC -inf 输出 | `fix_multi_file.sh`（→ `           -INF`） | `agent/pitfalls/windows-inf-field.md` |
| float() 报 `8.33534443-110` | Fortran 定宽省略 e 指数 | 读取端正则插 e（已内置于 batch_migrate/plot 脚本） | `agent/pitfalls/missing-e-exponent.md` |

## 2. 布局/单位/解释类（无报错但结果错）

| 现象 | 根因 | 快速修复 | 完整档案 |
|---|---|---|---|
| p/t 与源表对照大偏差 | IEOS 能量主序被 reshape 读反 | `reshape(NE,NR)` 或 `p[j*NR+i]` | `agent/pitfalls/ieos-layout-order.md` |
| 压强整体小 1e4 倍 | dyne/cm²→MPa 误用 ÷1e11 | ×1e-7；与源表绝对值对照 | `agent/pitfalls/pressure-unit-confusion.md` |
| 温度恒 0、压力/密度正常 | 手工转换链能量轴 ×1000（J/g vs J/kg） | **EOS-tools 重转**；PdV 检查判定 | `agent/pitfalls/migrated-eos-energy-scale-1000x.md` |
| FEOS 转换产物 P/T 振荡/RH 无解 | feos2multi/feos2r94 布局+能量 ×100 双 bug | 禁用，改 `eos_convert.py --from feos --to multi` | `agent/pitfalls/feos-converter-layout-energyunit.md` |
| Zeff 插值离谱 | T 网格按 eV 解释（实为 keV） | lt+3 = log10(T/eV) | `agent/pitfalls/zeff-kev-not-ev.md` |
| 1D 把 Zeff 表当 IEOS | type 串 ` 6.00000000e+00` 1D 不认 | 改头 ` 0.60000000E+01` | `agent/pitfalls/zeff-type-string-variants.md` |

## 3. 加载行为类

| 现象 | 根因 | 快速修复 | 完整档案 |
|---|---|---|---|
| `bad number of tables` | 2D LoadIEOS 要求单表文件 | 拆表或用 LoadMF 按 id 取 | `knowledge/ieos_format.md §4` |
| 1D 群数比源表少 | f1==f2 退化子表截断 | `drop_degenerate_groups()` | `agent/pitfalls/degenerate-opacity-group.md` |
| 1D 找不到表 | Thermos 表头 id=0，输入卡 id 不匹配 | 输入卡 `*_id=0` 通配 | `agent/pitfalls/thermos-id-zero.md` |

## 4. 已知坏文件（勿用，迁移指南 §5）

| 文件 | 问题 |
|---|---|
| `mat_Au-1.0/AU_eosd` | 双表文件且首表缺 101 个值；无加载器引用 |
| `mat_Au-1.0/AU_SIMPLE_PLANCK_MG` | f1/f2 行仅 24 字符（<30 被拒） |
| `mat_Ti/Ti_Ross` | 头行 59 字符（补 1 空格可修；SNOP_LTE.ROSS 已覆盖同数据） |
| `mat_He/Untitled.30*` | .305 混入 16 字符 3 位指数字段 | 

## 5. 诊断流程建议

1. **先问文件来源**：Multi_BACK/Windows → 优先跑 `fix_multi_file.sh` + `check_multi_file.py`
2. **看错误信息**：对上表匹配
3. **无报错但结果错**：怀疑布局/单位/解释（§2），与源表做绝对值对照
4. **1D 加载异常**：看 output 的表加载摘要（id、NR/NE/NT、ng 群数）

## 6. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
