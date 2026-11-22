---
title: 验收标准全条目（A/B/C/D/E）+ 子 agent 提示词模板 + 人工确认闸门
skill: multi-material-migration
category: reference
source_anchors:
  - 材料迁移验证规范.md §4
  - 材料迁移验证规范.md §5
  - 材料迁移验证规范.md §F
doc_ref: "材料迁移验证规范.md §4-§6"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 验收标准
  - 子agent
  - 提示词
  - 人工确认
---

# 验收标准与子 agent 验收

> 本体：《材料迁移验证规范.md §4-§6》。**机器验收（子 agent）与人工确认（用户）是两道独立闸门**。

## 1. A. 格式合规（必过）

```bash
M=$MULTI_ROOT
python3 $M/work/eos_opacity_tools/check_multi_file.py <每个迁移文件>
```
- A1 全部输出 ✓，退出码 0
- A2 IEOS 的 NR/NE 与迁移记录一致；mgo 子表数=群数；sgo type 字符串正确

## 2. B. 算例运行（必过，查 `validation_cases/<X>Check/output`）

| 条目 | 标准 |
|---|---|
| B1 | 含 `normal program termination` |
| B2 | 能量相对误差 `error` 绝对值 < 1e-6 |
| B3 | 表加载摘要：eeos/ieos 指向新表且 NR/NE 正确；planck/ross 的 **ng 群数与源表一致**；Z 表（若挂）NR/NT 正确 |
| B4 | 实际到达 texit（步进日志最后一行 time = texit） |
| B5 | 能量收支合理：radinr>0、derad>0、电子/离子能量上升、无 NaN/异常巨大值 |
| B6 | 无 `ERROR`、`STOP`、`premature eof` 等字样 |

## 3. C. 物理合理性（必过）

- C1 表网格范围覆盖算例实际状态（ρ 含固体密度；T 覆盖 0.03 eV–100 eV 以上）
- C2 拆分自洽性（S4）偏差与官方 Be 表同量级（~20% 内正常）
- C3 2D 材料函数存在于 Material.r / Material_mig.r 且已重编译
  （`grep -c "Material<X>" Material.c` ≥ 1 且 .c 新于/同日于 .r）

## 4. D. 文档登记 / E. 可视化（必过）

- D1 清单已登记新材料及全部文件（D2 来源/日期/算例名由主 agent 补充）
- E1 两个 PNG 存在且非空；解析记录数 ≥ 50
- E2 热图密度场连续演化、无断带/NaN 空洞
- E3 剖面光滑、量纲合理（ρ>0；T 在表覆盖内；P 无异常振荡）
- E4 中间时刻实际时间在 texit 45%–55%

## 5. 子 agent 提示词模板（规范 §5 原文，复制替换占位符）

```
你是独立的验收 agent。请按 $MULTI_ROOT/材料迁移验证规范.md 
第 4 节的标准，验收材料 <X> 向 MULTI-2D.2026.3 的迁移。

迁移文件清单：
  - <文件1>（如 r94/mat_Ti-1.0/Ti_eos）
  - <文件2>（如 r94/MULTI-IFE-2015/tables/...）
验收算例：$MULTI_ROOT/validation_cases/<X>Check
  （已运行，结果在 output；可视化产物 density_heatmap.png / profiles_mid.png 已生成）
迁移记录：<简要说一步骤 S1-S7b 的实际情况>

请逐条检查 A1-A2、B1-B6、C1-C3、D1、E1-E4（D2 由主 agent 后续补充，跳过；
F 节人工确认由用户执行，不在你的检查范围）。
输出格式：
  [PASS/FAIL] 条目号 - 一句话证据
最后给出总结论：ACCEPT（全部 PASS）或 REJECT（列出需修复项）。
不要修改任何文件，只做只读检查。
```

**执行要点**：
- 必须**新起**子 agent（独立验收，不带迁移者上下文）
- 迁移记录要如实写（含修复过什么）——子 agent 会据此重点复查
- REJECT 项修复后复验（可同一子 agent，说明修复点）

## 6. F. 人工确认（最终闸门，规范 §F）

- F1 子 agent 全部 PASS 后，**用户**人工查看 `validation_cases/<X>Check/` 的
  `output`、`density_heatmap.png`、`profiles_mid.png`
- F2 用户明确确认 → 清单标"完全迁移 ✅"；之前状态 = "机器验收通过，待人工确认"
- 任何情况下不得跳过/代替用户确认

## 7. 历史验收记录参照

《材料迁移验证规范.md §6》已有：Ti（16/16，用户已确认）、批次1（26+3 种）、
批次2（30 种）、单位修复复验（20 种）、opc 批次（18 ACCEPT + 3 CAVEAT）。
历史问题与修复记录（Ne/Kr/压强单位）在同节——**新验收先读历史记录避免重蹈**。

## 8. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
