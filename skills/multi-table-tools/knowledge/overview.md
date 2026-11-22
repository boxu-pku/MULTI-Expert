---
title: 表工具总览与场景选用表
skill: multi-table-tools
category: overview
source_anchors:
  - work/eos_opacity_tools/check_multi_file.py:L1-L16
  - work/eos_opacity_tools/batch_migrate.py:L1-L18
  - MULTI-2D_材料库迁移指南.md §6
doc_ref: "MULTI-2D_材料库迁移指南.md §6（工具清单与位置）"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 工具
  - 总览
  - 选用
---

# 表工具总览与场景选用表

> **TL;DR**：工具实体在 `work/eos_opacity_tools/`（勿移动）+ 外部 EOS-tools。按场景选用：验证→check_multi_file.py；修复→fix_multi_file.sh；拆分→split_ieos_table.py；opc 转换→opc2sgo.py；批量迁移→batch_migrate.py；1D 可读性→tread.f95；外部格式转换→EOS-tools CLI。

## 1. 场景 → 工具速查

| 场景 | 工具 | 详见 |
|---|---|---|
| 验证表文件能否被 MULTI 读取 | `check_multi_file.py` | `knowledge/validate_and_fix.md §1` |
| 修 CRLF / Windows -1.#INF | `fix_multi_file.sh` | `knowledge/validate_and_fix.md §2` |
| 验证 1D Fortran 可读性 | `tread.f95` | `knowledge/validate_and_fix.md §3` |
| 批量回归测试（IEOS/不透明度） | `strict_binary_test.py` / `strict_opacity_test.py` | `knowledge/validate_and_fix.md §4` |
| 双解析器逐值对比 | `verify_multi_eos.py` | `knowledge/validate_and_fix.md §4` |
| 总 IEOS → 电子/离子表 | `split_ieos_table.py` | `knowledge/convert_and_split.md §1` |
| hyades opc → sgo 单群表 | `opc2sgo.py` | `knowledge/convert_and_split.md §2` |
| hyades/SESAME/FEOS → MULTI | EOS-tools CLI（eos_convert/opacity_convert） | `knowledge/convert_and_split.md §3` |
| 清单驱动批量迁移（full/celia/eos_only） | `batch_migrate.py` + `migrate_manifest.py` | `knowledge/convert_and_split.md §4` |
| 为 EOS-only 材料配 opc 单群不透明度 | `migrate_opc_batch.py` | `knowledge/convert_and_split.md §5` |
| 生成 2D 材料函数 Material_mig.r | `gen_material_functions.py` | `knowledge/convert_and_split.md §6` |

## 2. 通用规则

1. **新增/修改任何表文件后必跑** `check_multi_file.py`（迁移指南 §6.2：
   "新增材料后必跑；通过即保证 2D 可读"）
2. 给 **1D** 用的文件再跑 `tread.f95`
3. EOS-tools 转换后检查 `*.conversion-audit.json/csv`（P95/最大相对误差、覆盖率）
4. 破坏性操作（fix 原地改文件）有自动 .bak 备份；仍建议先确认
5. 多文件批量：`check_multi_file.py <文件...>` 支持多参数；退出码 0=全过 1=有失败

## 3. 环境变量约定

```bash
export MULTI=$MULTI_ROOT   # 多数脚本内部已写死该路径
# batch_migrate.py / migrate_opc_batch.py / gen_material_functions.py
# 内部 sys.path 已含 EOS-tools 与工具目录，直接 python3 运行即可
```

## 4. 延伸阅读

- `MULTI-2D_材料库迁移指南.md §6-§7`（工具清单 + 操作手册）
- 各 knowledge 条目

## 5. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
