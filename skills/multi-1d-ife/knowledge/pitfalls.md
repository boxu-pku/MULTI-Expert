---
title: 1D 程序类踩坑集（multi-1d-ife 摘要索引）
skill: multi-1d-ife
category: pitfalls
source_anchors:
  - agent/pitfalls/
  - 材料迁移验证规范.md §6
doc_ref: "材料迁移验证规范.md §6（历史问题记录）"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 踩坑
  - 索引
  - 1D
---

# 1D 程序类踩坑集

> 完整档案在 `agent/pitfalls/`；历史问题记录在 `材料迁移验证规范.md §6`。

## 1. 表加载类

| 现象 | 根因 | 档案 |
|---|---|---|
| 群数比源表少（Ne 77/78） | f1==f2 退化子表截断 load_table_multi | `agent/pitfalls/degenerate-opacity-group.md` |
| 表找不到/群数 0 | Thermos 表头 id=0，输入卡 id 不匹配 | `agent/pitfalls/thermos-id-zero.md` |
| Zeff 表被当 IEOS 读 | type 串 ` 6.00000000e+00` 1D 不认 | `agent/pitfalls/zeff-type-string-variants.md` |
| Zeff 值离谱 | T 网格按 eV（实 keV） | `agent/pitfalls/zeff-kev-not-ev.md` |

## 2. 算例运行类

| 现象 | 根因 | 档案 |
|---|---|---|
| Kr 固体密度算例辐射坍缩崩坏 | ρ 冲出表上限（1890 vs 10） | `agent/pitfalls/gas-vs-solid-case-density.md` |
| Diamond/Cliquid 越界/崩溃 | 源 EOS 表密度下限高 | `agent/pitfalls/eos-density-range-limit.md` |
| Air 算例异常 | 初温 < 表 T 下限 | `agent/pitfalls/gas-vs-solid-case-density.md` |
| 压强整体小 1e4 倍（首批次） | dyne/cm²→MPa 单位 bug | `agent/pitfalls/pressure-unit-confusion.md` |

## 3. 输出/可视化类

| 现象 | 根因 | 档案 |
|---|---|---|
| fort.10 解析 float 失败 | e12.5 省略 e（`-0.33689-232`） | `agent/pitfalls/missing-e-exponent.md` |
| MULTI1Dvisual2.2 打不开 fort.10 | IFE-2015 是 ASCII，GUI 要二进制 | `agent/pitfalls/fort10-ascii-vs-binary.md` |
| 热图断带 | ns_bout 太大 | `材料迁移验证规范.md §E`（ns_bout=1） |

## 4. 判读类提醒

- `normal program termination` + `error < 1e-6` + 群数一致 = 机器验收三要素（§B1-B3）
- 能量守恒**查不出**单位错误——必须另与源表绝对值对照
- output 中出现 `ERROR`/`STOP`/`premature eof` 即为 FAIL

## 5. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
