---
title: 不透明度类踩坑集（multi-opacity 摘要索引）
skill: multi-opacity
category: pitfalls
source_anchors:
  - MULTI-2D_材料库迁移指南.md §5, §8
  - agent/pitfalls/
doc_ref: "MULTI-2D_材料库迁移指南.md §5, §8"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 踩坑
  - 索引
  - 不透明度
---

# 不透明度类踩坑集

> 完整档案在 `agent/pitfalls/`；本文件是不透明度相关条目的索引 + 速查。

## 1. 表加载类

| 现象 | 根因 | 修复 | 档案 |
|---|---|---|---|
| 1D 群数比源表少（如 Ne 77/78） | f1==f2 退化子表致 load_table_multi 误判结束 | `drop_degenerate_groups()`（batch_migrate 内置） | `agent/pitfalls/degenerate-opacity-group.md` |
| 1D 找不到 Thermos 表 | 表头 id=0，输入卡 id 不匹配 | `*_id=0` 通配 | `agent/pitfalls/thermos-id-zero.md` |
| 1D 把 Zeff 表当 IEOS | type 串 ` 6.00000000e+00` 1D 不认 | 改头 ` 0.60000000E+01` | `agent/pitfalls/zeff-type-string-variants.md` |
| Zeff 电离度离谱 | T 网格按 eV（实 keV） | — | `agent/pitfalls/zeff-kev-not-ev.md` |
| `head line size != 60` / float 解析失败 | CRLF / -1.#INF | `fix_multi_file.sh` | `agent/pitfalls/crlf-line-endings.md`、`windows-inf-field.md` |

## 2. 模型理解类（无报错但用法错）

| 误解 | 正解 | 出处 |
|---|---|---|
| 2D 直接消费多群表 | 2D 是单群灰体；LoadOpa/LoadTab 已禁用；用解析式或单群表插值 | `knowledge/overview.md §2` |
| nphis 是群数 | nphis 是角度离散 | `M20_Transport.r:L84` |
| opc 表是多群 | opc 是 (ρ,T) 网格**平均**不透明度（Planck 全零=仅 Rosseland） | `knowledge/data_sources.md §3` |
| EPS 表 2D 可用 | EPS 仅 1D（非 LTE）支持 | 迁移指南 §8-6 |
| 把 κ 当 λ 返回 opafun | λ=1/(κ·ρ) | 迁移指南 §7.3 |

## 3. 数据局限类

| 现象 | 根因 | 处置 |
|---|---|---|
| Diamond/Cliquid 烧蚀算例越界 | 源 EOS 表密度下限高（0.35/0.23 g/cc） | `agent/pitfalls/eos-density-range-limit.md` |
| Kr 固体密度算例崩坏 | 辐射坍缩 ρ 冲出表上限 | 气体密度算例，`agent/pitfalls/gas-vs-solid-case-density.md` |
| 拟合 opafun 精度有限 | rms ~1-2 dex | 精度敏感用查表或 1D 校核，`knowledge/freepath_mechanism.md §3` |

## 4. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
