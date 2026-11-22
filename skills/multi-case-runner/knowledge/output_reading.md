---
title: output / ktag / cputime / 快照 判读
skill: multi-case-runner
category: internals
source_anchors:
  - r94/MULTI-IFE-2015/m150304.f95:L3820
  - r94/MULTI-IFE-2015/m150304.f95:L4224-L4267
  - 材料迁移验证规范.md §B
  - MULTI-2D_梳理文档.md §8.2
doc_ref: "材料迁移验证规范.md §B; MULTI-2D_梳理文档.md §8.2"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - output
  - ktag
  - 判读
  - 能量误差
---

# output / ktag / cputime / 快照 判读

## 1. 1D output 结构（按出现顺序）

1. **编译信息**（gfortran 输出，若有 warning）
2. **表加载摘要**：每种材料的六表加载情况——文件名、id、NR/NE/NT、**ng 群数**
   （验收 §B3 核对点）
3. **步进日志**：istep, time, dt, ...（每步一行；最后一行 time 应 = texit，§B4）
4. **能量收支**（`print_energies`，`m150304.f95:L4197`）：
   `radinr`（右边界辐射输入累计，`L4259`）、`derad`（热辐射沉积净值，`L4251`）、
   `error`（能量收支相对误差，`L4224` 计算、`L4267` 输出）等
5. **终止标志**：`normal program termination`（`L3820`）

**验收口径**（材料迁移验证规范 §B）：

| 条目 | 标准 | 命令 |
|---|---|---|
| B1 | 含 normal program termination | `grep -c "normal program termination" output` |
| B2 | error 绝对值 < 1e-4（2026-08-13 由 1e-6 放宽） | `grep "relative error in energy" output` |
| B3 | 表加载摘要 NR/NE/ng 与源表一致 | 目视 output 前部 |
| B4 | 步进最后一行 time = texit | `tail output` |
| B5 | radinr>0、derad>0、能量上升、无 NaN | 目视能量收支段 |
| B6 | 无 ERROR/STOP/premature eof | `grep -iE "ERROR|STOP|premature eof" output` |

## 2. ktag 状态机

```
RUN 开始  →  ktag 存在（echo nada >ktag）
正常结束  →  ktag 消失（proceso 末尾 rm ktag）
异常退出  →  ktag 残留（需人工 rm）
```

判读："ktag 在" ≠ "在跑"——先 `ps aux | grep -E 'multi|a.out'` + `tail output` 确认。

## 3. cputime

`/usr/bin/time` 的 stderr：user/sys/elapsed 时间与内存。性能分析用，正确性判读不涉及。

## 4. 结果数据文件

| 文件 | 内容 | 消费方式 |
|---|---|---|
| `fort.10` | 全变量时间序列（ASCII） | plot_1d_validation.py（→ multi-visualize） |
| `fort.11` | 剖面表（ASCII） | 直接阅读 |
| `<t>` / `<t>.d`（2D） | 二进制快照 + 描述 | mpp22 GUI |

## 5. 2D output（补充）

2D output 同样是每步摘要（dt、CFL、沉积量、产额等），但无统一验收口径——
逐算例看物理（本轮 2D 未逐一实测）。崩溃信号：`M20_Step: more than 32 time step
reductions`（`M20_Step.r:L132`）。

## 6. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
