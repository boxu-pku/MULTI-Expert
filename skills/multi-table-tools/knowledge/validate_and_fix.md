---
title: 验证与修复工具 — check_multi_file.py / fix_multi_file.sh / tread.f95 / strict 系列
skill: multi-table-tools
category: internals
source_anchors:
  - work/eos_opacity_tools/check_multi_file.py:L13-L16
  - work/eos_opacity_tools/check_multi_file.py:L80-L124
  - work/eos_opacity_tools/fix_multi_file.sh:L18-L31
  - work/eos_opacity_tools/tread.f95:L1-L16
  - work/eos_opacity_tools/verify_multi_eos.py:L1-L10
doc_ref: "MULTI-2D_材料库迁移指南.md §6.2"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - check_multi_file
  - fix_multi_file
  - tread
  - 验证
  - 修复
---

# 验证与修复工具

## 1. check_multi_file.py — 严格格式验证器（新增材料后必跑）

**语义**：严格复现 `Mat2013_LoadMF` 的 C 解析（60 字符头、15 字符定宽、跨节打包、
mgo 群边界行、-INF→-40/NAN→0），IEOS/mgo/sgo 通吃。**通过即保证 2D 可读**
（`check_multi_file.py:L1-L16` 报头注释）。

**用法**（L13-L15）：
```bash
python3 $MULTI/work/eos_opacity_tools/check_multi_file.py <文件> [文件2 ...]
```

**输出判读**（L111-L124）：
- `✓ <文件>  (N 个子表)` + 前 5 个子表摘要（类型/网格/群边界/id）→ 通过
- `✗ <文件>` + `ValueError: ...` → 失败；退出码 0=全过 1=有失败
- 典型失败：`头行长度=61 != 60`（CRLF）、`could not convert string to float`（-1.#INF 或缺 e 指数）

**子表摘要怎么看**：IEOS 显示 `IEOS NR=x NE=y id=z`；mgo 显示
`mgo[PLANCK M] NRxNT 群[f1~f2]eV id=`；sgo 显示 `sgo[type=...] NRxNT id=`。
**验收对照**：NR/NE 与迁移记录一致、mgo 子表数=群数、sgo type 正确（验证规范 §A2）。

## 2. fix_multi_file.sh — 修 CRLF + Windows -INF

**语义**（报头 L1-L15）：① CRLF→LF（C 解析器遇 \r 报 head line size != 60）；
② `-1.#INF000e+000`→`           -INF`（MULTI 标准，读入映射 -40）。

**用法**：
```bash
$MULTI/work/eos_opacity_tools/fix_multi_file.sh <文件> [文件2 ...]   # 原地修复(先备份 .bak)
$MULTI/work/eos_opacity_tools/fix_multi_file.sh -d <目录>            # 目录批量
```

**行为**（L18-L31）：无 \r 且无 #INF 的文件不动（"无需修复"）；
修复前 `cp -n file file.bak`；`sed -i 's/\r$//'` + 两条 -INF sed（L27-L29）。

**修复后必须验证**（check_multi_file.py）。

## 3. tread.f95 — 1D Fortran 表头可读性验证

**语义**：复刻 1D 的表头读取 `read(u,'(e15.0,a,2e15.8)')`（`tread.f95:L9`），
验证 1D Fortran 能否正确读出 id/type/NR/NT（尤其 Zeff type 串变体兼容性）。

**用法**：
```bash
cd /tmp && gfortran -o tread $MULTI/work/eos_opacity_tools/tread.f95
./tread <表文件>
# 输出: id=   27003000 type=[PLANCK M       ] nr=   30 nt=   50
# 失败: HEADER READ FAIL（stop 1）
```

注意：只验**表头**，不验数据体；数据体验证靠 1D 算例实测或 check_multi_file.py
（Fortran 与 C 的数据体语义一致，但 type 串解释不同——见 pitfalls/zeff-type-string-variants.md）。

## 4. 回归/对比测试脚本

| 脚本 | 用途 |
|---|---|
| `strict_binary_test.py` | IEOS 批量严格测试（含 Multi_BACK 全量清单）；其 `CStrictParser` 类被 gen_material_functions 复用 |
| `strict_opacity_test.py` | 不透明度批量严格测试；`load_opacity_strict` 被 batch_migrate 复用 |
| `verify_multi_eos.py` | 双向验证：严格解析器 vs EOS-tools 解析器**逐值对比**（转换正确性核查） |
| `batch_check_eos.py` | EOS 批量检查 |

## 5. 常见问题

| 问题 | 处理 |
|---|---|
| 头行长度 59/61 ≠ 60 | 59=字段缺前导空格（补空格）；61=CRLF（fix_multi_file.sh） |
| float 解析失败 | -1.#INF → fix；缺 e 指数 → batch_migrate 的 fix_missing_e_fields 已内置 |
| 验证通过但 1D 读错表 | type 串 1D 不认（Zeff ` 6.00000000e+00`）→ 改 ` 0.60000000E+01` |

## 6. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
