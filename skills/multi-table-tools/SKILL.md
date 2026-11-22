---
name: multi-table-tools
description: |
  MULTI 表文件验证/修复/转换/拆分工具箱（包装 work/eos_opacity_tools/ 与 EOS-tools，
  不复制实体）。何时用：验证表文件能否被 MULTI 读取（check_multi_file.py）、
  修复 CRLF 与 Windows -1.#INF（fix_multi_file.sh）、总 IEOS 拆电子/离子表（split_ieos_table.py）、
  hyades opc 转 sgo 单群表（opc2sgo.py）、清单驱动批量迁移（batch_migrate.py + migrate_manifest.py）、
  1D Fortran 可读性验证（tread.f95）、格式转换（EOS-tools CLI eos_convert/opacity_convert）。
  触发词：验证, 修复, 转换, 拆分, check_multi_file, fix_multi_file, split_ieos_table,
  opc2sgo, batch_migrate, migrate_manifest, tread, EOS-tools, eos_convert, opacity_convert,
  dos2unix, 表验证, 格式检查, 严格解析, 双向验证
triggers:
  - 验证
  - 修复
  - 转换
  - 拆分
  - check_multi_file
  - fix_multi_file
  - split_ieos_table
  - opc2sgo
  - batch_migrate
  - migrate_manifest
  - tread
  - EOS-tools
  - eos_convert
  - opacity_convert
  - dos2unix
  - 表验证
  - 格式检查
  - 严格解析
  - 双向验证
  - verify_multi_eos
  - 工具
when_to_use: |
  1. 用户要验证表文件能否被 MULTI 读取（"验证一下这个文件"、"格式对不对"）
  2. 用户要修复文件（"CRLF 怎么办"、"-1.#INF 怎么修"）
  3. 用户要拆分总 IEOS 为电子/离子表
  4. 用户要转换格式（hyades/SESAME/FEOS → MULTI；多群聚合；opc → sgo）
  5. 用户要批量迁移多种材料（清单驱动）
  6. 用户要验证 1D Fortran 可读性（tread.f95）
when_not_to_use: |
  - 问格式原理（为什么这样设计） → multi-eos-format
  - 问不透明度数据源选用 → multi-opacity
  - 端到端新材料迁移（含算例/验收/登记全流程） → multi-material-migration
  - 结果可视化 → multi-visualize
  - 跑算例 → multi-case-runner
layer: tool
phase: 1
status: stable
created: 2026-08-11
last_updated: 2026-08-11
owner: claude
---

# multi-table-tools — 表文件工具箱（验证/修复/转换/拆分）

## 1. 角色与边界

### 1.1 我是做什么的

提供 `work/eos_opacity_tools/` 各脚本与 EOS-tools CLI 的**调用约定**：
什么场景用哪个工具、命令怎么写、输出怎么判读、退出码语义。
**工具实体不移动不复制**（ARCHITECTURE.md §10），本 skill 只写调用知识。

### 1.2 我不做什么

| 用户问题类型 | 归属 skill |
|---|---|
| 格式原理（为什么 60 字符头） | `multi-eos-format` |
| 不透明度源选用 | `multi-opacity` |
| 端到端迁移（S1-S9 全流程） | `multi-material-migration` |
| 可视化 | `multi-visualize` |
| 跑算例 | `multi-case-runner` |

## 2. 行为协议

### 2.1 接到查询时

按 `knowledge/` 给调用约定（命令 + 参数 + 输出判读 + 锚点）。

### 2.2 接到执行任务时（on_run）

1. **确认场景选工具**（§4 索引表）；**EOS 转换一律用 EOS-tools**（铁律 6/L-008：
   不手写转换链；禁用 FEOS 自带 feos2multi/feos2r94——布局+能量单位双 bug，
   唯一例外按 `agent/pitfalls/feos-converter-layout-energyunit.md` 两步修复）
2. **先备份/先干跑**：fix_multi_file.sh 自动备份 .bak；破坏性操作前向用户确认
3. **跑完验证**：转换/修复后必跑 check_multi_file.py；给 1D 用的再跑 tread；
   未经 EOS-tools CLI 的转换加做 源表绝对值对照 + PdV 检查
   （`agent/pitfalls/migrated-eos-energy-scale-1000x.md` 判定方法）
4. **报告格式**：命令 → 输出要点 → 下一步建议（如"格式通过，可挂 2D/1D"）

### 2.3 工具未覆盖时

如需要新工具（如新格式解析），告知用户并建议扩写脚本到 `work/eos_opacity_tools/`
（不放进 skill）。

## 3. 知识维护规则

- 工具脚本报头注释（用法/语义）是调用约定的一手来源，引用带行号
- 工具行为变更时同步本 skill

## 4. knowledge/ 子目录索引

| 文件 | 内容 | 当前状态 |
|---|---|---|
| `knowledge/overview.md` | 工具总览与场景选用表 | stable |
| `knowledge/validate_and_fix.md` | check_multi_file.py / fix_multi_file.sh / tread.f95 / strict 系列 | stable |
| `knowledge/convert_and_split.md` | split_ieos_table.py / opc2sgo.py / batch_migrate.py / migrate_opc_batch.py / EOS-tools CLI | stable |
| `knowledge/pitfalls.md` | 工具使用类踩坑 | stable |

## 5. 示例问答（验收基准）

### Q1: 怎么验证一个 Multi_BACK 原始文件能否被 MULTI 读取？
**A**: 两步（`knowledge/validate_and_fix.md`）：
```bash
M=$MULTI_ROOT
$M/work/eos_opacity_tools/fix_multi_file.sh <文件>          # 修 CRLF + -1.#INF
python3 $M/work/eos_opacity_tools/check_multi_file.py <文件> # 严格验证
```
全 ✓ 且退出码 0 = 2D 可读；给 1D 用再 `gfortran tread.f95 && ./a.out <文件>`。

### Q2: 总 IEOS 怎么拆成电子/离子表？
**A**: `python3 split_ieos_table.py <总表> <A> <e输出> <i输出> [e_id i_id]`——
复刻 Mat2013_EleTab 算法（减理想离子）+ 理想气体离子表（γ=5/3）。
id 约定 int(Z)×10⁶+304/305。详见 `knowledge/convert_and_split.md §1`。

### Q3: EOS-tools 怎么把 hyades EOS 转成 MULTI？
**A**: 见 `knowledge/convert_and_split.md §3`：
```bash
cd $MULTI_LIBS/EOS_converter_xubo/EOS-tools
python3 cli/eos_convert.py --from hyades --to multi \
    --electron-file <源> --zeff-file none --atom-a <A> --atom-z <Z> --name <X> \
    --output <输出前缀>
```
产物 `<X>_electron.multi/_ion.multi/_zeff.multi` + conversion-audit 报告。
⚠ zeff 表头需改 ` 0.60000000E+01` 才能给 1D 用。

## 6. 工具实体位置（勿移动）

| 工具 | 路径 |
|---|---|
| 本项目工具集 | `work/eos_opacity_tools/`（check/fix/split/opc2sgo/batch_migrate/migrate_manifest/migrate_opc_batch/tread.f95/strict_*/verify_multi_eos/plot_1d_validation/run_all_cases/gen_material_functions） |
| EOS-tools | `$MULTI_LIBS/EOS_converter_xubo/EOS-tools`（cli/eos_convert.py、opacity_convert.py、eos_query.py、eos_generate.py） |

## 7. 待办

- [ ] 无

## 8. 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建（knowledge 4 篇） | claude |
