---
name: multi-case-runner
description: |
  MULTI 算例运行专家（端到端）。运行 1D（2015*、XCheck 验证算例）与 2D（M2D_*）算例：
  RUN 脚本机制（x.2.library/x.2.build 或 gfortran）、ktag 运行标记语义、output 判读
  （表加载摘要/能量误差/normal program termination）、CLEAR 清理规则
  （validation_cases 永久保留禁止清理）、批量运行 run_all_cases.sh。
  触发词：跑算例, 运行, RUN, ktag, output, TiCheck, XCheck, 2015CPC, M2D, 算例,
  CLEAR, cputime, proceso, nohup, 批量运行, run_all_cases, 跑一下, 编译算例
triggers:
  - 跑算例
  - 运行
  - RUN
  - ktag
  - output
  - TiCheck
  - XCheck
  - 2015CPC
  - 2015IND
  - M2D
  - 算例
  - CLEAR
  - cputime
  - proceso
  - nohup
  - 批量运行
  - run_all_cases
  - 跑一下
  - 编译算例
  - 跑通
when_to_use: |
  1. 用户要跑算例（"跑一下 TiCheck"、"跑 2015CPC"、"跑 M2D_Radia_110"）
  2. 用户问算例运行状态（"还在跑吗"→ ktag；"跑完没有"→ output 判读）
  3. 用户问算例运行失败（编译错/运行崩/output 有 ERROR）
  4. 用户问结果文件（"output/cputime/ktag/<t> 文件都是什么"）
  5. 用户要批量跑验证算例（run_all_cases.sh）
  6. 用户问算例清理（CLEAR 规则；validation_cases 禁止清理）
when_not_to_use: |
  - 结果可视化（出图） → multi-visualize
  - 算例物理设计/输入卡含义 → multi-1d-ife（1D）或 multi-architecture（2D）
  - 迁移新材料并建验收算例 → multi-material-migration
  - 表文件修复/验证 → multi-table-tools
layer: operator
phase: 1
status: stable
created: 2026-08-11
last_updated: 2026-08-11
owner: claude
---

# multi-case-runner — 算例运行专家（端到端）

## 1. 角色与边界

### 1.1 我是做什么的

端到端跑 MULTI 算例：环境检查 → RUN → 等待/判读 → 报告。覆盖 1D（gfortran 链）
与 2D（r94 编译链）两类算例目录，含批量运行与清理规则。

### 1.2 我不做什么

| 用户问题类型 | 归属 skill |
|---|---|
| 跑完出图 | `multi-visualize` |
| 输入卡/物理设计 | `multi-1d-ife` / `multi-architecture` |
| 迁移并新建验收算例 | `multi-material-migration` |
| 表文件修复验证 | `multi-table-tools` |

## 2. 行为协议

### 2.2 接到执行任务时（on_run）

**标准流程**（详见 `knowledge/run_protocol.md`）：

1. **环境检查**：`echo $MULTI`；缺则 `export MULTI=$MULTI_ROOT`
   并把 `$MULTI/r94/boot-3.2` 与 `.` 加入 PATH
2. **识别算例类型**：目录有 `data.in` → 1D；有 `User.r` → 2D
3. **检查残留**：`ktag` 存在 → 先确认是否真在跑（`ps aux | grep -E 'multi|a.out'`），
   不在跑则 `rm ktag`
4. **执行** `cd <算例目录> && ./RUN`（后台 nohup）
5. **等待**：`while [ -f ktag ]; do sleep 2; done`（2D 算例可能数小时——
   **2D 运行本轮未逐一实测**，先与用户确认时长预期）
6. **判读**（`knowledge/output_reading.md`）：1D 看 normal program termination +
   error <1e-6 + 表加载摘要；2D 看 output 尾部与快照文件
7. **报告**：运行结果 + 关键指标 + 产物清单；需要出图 → 提示可接 multi-visualize

**禁令**：
- ❌ 不对 `validation_cases/` 任何目录执行 CLEAR / 删除产物（永久保留，验证规范 §E）
- ❌ 不在算例目录外乱扔编译产物
- ❌ 编译/运行出错时不盲目重试——先读 output 找根因

## 3. 知识维护规则

RUN 机制以各算例 RUN 脚本与 `MULTI-2D_梳理文档.md §8` 为准。

## 4. knowledge/ 子目录索引

| 文件 | 内容 | 当前状态 |
|---|---|---|
| `knowledge/overview.md` | 两类算例目录结构与 RUN 机制对比 | stable |
| `knowledge/run_protocol.md` | 标准运行流程（环境→RUN→等待→判读） | stable |
| `knowledge/output_reading.md` | output/ktag/cputime/快照 判读 | stable |
| `knowledge/pitfalls.md` | 运行类踩坑索引 | stable |

## 5. examples/ 与 recipes/

| 文件 | 内容 |
|---|---|
| `examples/run_1d_case.sh` | 跑 1D 算例的完整示例脚本（环境+RUN+等待+判读） |
| `examples/run_2d_case.sh` | 跑 2D 算例的完整示例脚本 |
| `recipes/ticheck.md` | 跑 TiCheck 验证算例 + 出图的完整流程单 |
| `recipes/batch_validation.md` | run_all_cases.sh 批量验证算例流程单 |

## 6. 示例问答（验收基准）

### Q1: 跑一下 TiCheck
**A**: 按 `recipes/ticheck.md`：
```bash
export MULTI=$MULTI_ROOT
export PATH=$PATH:$MULTI/r94/boot-3.2:.
cd $MULTI/validation_cases/TiCheck && ./RUN
# ktag 消失后判读 output（应含 normal program termination，error <1e-6）
```

### Q2: 算例 ktag 一直存在，是卡死了吗？
**A**: ktag 存在只表示"标记未清除"。先 `ps aux | grep -E 'multi|a.out'` 看进程是否真在跑，
`tail output` 看是否还在步进。进程死了但 ktag 在 = 异常退出残留，`rm ktag` 后查 output
找根因再重跑（`knowledge/output_reading.md §2`）。

### Q3: validation_cases 目录太占地方，能 CLEAR 吗？
**A**: **禁止**。validation_cases 全部产物（output + fort.10/11 + 两张 PNG）是人工验收依据，
永久保留（材料迁移验证规范 §E；`validation_cases/README.md`）。要清理的是 `cases/` 下
标准算例的运行残留（Manager2015 Case→Clear 或手工按 FILELIST）。

## 7. 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建（knowledge 4 + examples 2 + recipes 2） | claude |
