---
title: 工具使用类踩坑集（multi-table-tools 摘要索引）
skill: multi-table-tools
category: pitfalls
source_anchors:
  - agent/pitfalls/
  - work/eos_opacity_tools/batch_migrate.py:L137-L138
doc_ref: "MULTI-2D_材料库迁移指南.md §8"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 踩坑
  - 工具
  - 索引
---

# 工具使用类踩坑集

## 1. 高频坑（完整档案在 agent/pitfalls/）

| 场景 | 坑 | 工具侧处理 |
|---|---|---|
| Multi_BACK 文件验证 | CRLF → 头长 61 | fix_multi_file.sh → check（`crlf-line-endings.md`） |
| Thermos 文件 | `-1.#INF000e+000` | fix_multi_file.sh / batch 的 fix_inf=True（`windows-inf-field.md`） |
| hyades 源转换 | 压强单位 ×1e-7（非 ÷1e11） | batch_migrate L137 已修复；**勿改回**（`pressure-unit-confusion.md`） |
| 手工转换链（历史） | 能量轴 ×1000（J/g vs J/kg 混淆），温度恒 0 但守恒查不出 | **一律改用 EOS-tools 重转**；验收加 PdV 一致性检查（`migrated-eos-energy-scale-1000x.md`） |
| FEOS→MULTI 转换 | feos2multi/feos2r94 布局+能量 ×100 双 bug | **禁用**，用 `eos_convert.py --from feos --to multi`；唯一例外按档案两步修复（`feos-converter-layout-energyunit.md`） |
| Fortran 源表 | 缺 e 指数（`8.33534443-110`） | batch 的 fix_missing_e_fields 自动处理（`missing-e-exponent.md`） |
| EOS-tools zeff 给 1D | type 串 1D 不认 | 改头 ` 0.60000000E+01`（`zeff-type-string-variants.md`） |
| Thermos 多群给 1D | f1==f2 退化子表截断 | batch 的 drop_degenerate_groups 自动处理（`degenerate-opacity-group.md`） |
| 手工解析 IEOS | 能量主序 reshape 读反 | reshape(NE,NR)（`ieos-layout-order.md`） |

## 2. 工具使用规则提醒

1. **EOS 转换一律用 EOS-tools**（铁律 6 / L-008）：不手写转换链、不用 FEOS 自带转换器
2. **任何转换/修复后必跑 check_multi_file.py**（退出码 0 才算完）
3. **转换后与源表做物理量绝对值对照 + PdV 热力学一致性检查**——
   能量守恒/格式通过都查不出单位错（两起事故证实）
4. EOS-tools 转换必查 audit 报告（P95/覆盖率）
5. `batch_migrate.py` 的路径常量（MULTI/TABLES/CASES）写死为
   `$MULTI_ROOT`——**移动项目目录会导致静默写错位置**
6. fix_multi_file.sh 原地改文件（有 .bak）；批量 `-d` 模式前先确认目录范围

## 3. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
