---
title: 标准运行流程（环境检查 → RUN → 等待 → 判读）
skill: multi-case-runner
category: recipes
source_anchors:
  - MULTI-2D_梳理文档.md §8.2, §12
  - work/eos_opacity_tools/run_all_cases.sh:L8-L37
doc_ref: "MULTI-2D_梳理文档.md §8"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 运行流程
  - 环境
  - ktag
  - 判读
---

# 标准运行流程

## 1. 环境检查（每次必做）

```bash
export MULTI=$MULTI_ROOT
export PATH=$PATH:$MULTI/r94/boot-3.2:.
```

`x.0.find`、`x.2.library` 等命令依赖 PATH；`$MULTI` 被 RUN 脚本与 Material.r
（`getenv("MULTI")`）引用。漏设的症状：`x.2.*: command not found` 或模块查找失败
（梳理文档 §12）。

## 2. 跑前检查

```bash
cd <算例目录>
ls ktag 2>/dev/null && {
    ps aux | grep -E 'multi|a\.out' | grep -v grep   # 真在跑？
    tail -5 output                                     # 还在步进？
}
# 进程不在 → ktag 是异常残留：rm ktag
```

1D 重跑前清理（run_all_cases.sh L17 的模式）：
`rm -f fort.10 fort.11 fort.12 block multidata.mod output cputime`
（**validation_cases 例外：不清 fort.10/output**——它们是验收产物；只在新算例首跑时跑 RUN）。

## 3. 执行

```bash
./RUN          # 内部 nohup 后台；stdout 基本无输出
```

## 4. 等待

```bash
for i in $(seq 1 60); do [ ! -f ktag ] && break; sleep 2; done
```

- 1D 验证算例：秒~十秒级（121 步）
- 官方 2015*：分钟级（2015IND 20 ns 球几何更久）
- **2D：分钟~小时级，本轮未逐一实测**——跑 2D 前先告知用户时长预期，
  建议 `nohup` 后台 + 定期查看 output（ARCHITECTURE.md §10 决策）

## 5. 判读（1D 验收口径）

```bash
grep -c "normal program termination" output   # 应 =1
grep "relative error in energy" output         # |error| 应 < 1e-6
grep -iE "ERROR|STOP|premature eof" output     # 应为空
```

表加载摘要（output 前部）：核对 eeos/ieos 的 NR/NE、planck/ross 的 **ng 群数**
与源表一致（验证规范 §B3）。详见 `knowledge/output_reading.md`。

## 6. 失败处理流程

1. 编译失败（RUN 阶段）：看 output 的 gfortran/gcc 报错；2D 看 r94 翻译报错行
2. 运行失败：看 output 尾部（Fortran runtime error / STOP / M20_Step 32 次减半）
3. 结果异常（error 超阈值）：查表覆盖（agent/pitfalls/eos-density-range-limit.md）、
   群数（degenerate-opacity-group.md）、单位（pressure-unit-confusion.md）
4. **不盲目重试**——同一错误重跑结果一样

## 7. 批量运行

`run_all_cases.sh`：遍历 `validation_cases/*Check`（跳过 TiCheck）→
无 multi 则 RUN（有则清输出后 RUN）→ 等 ktag（最多 120s）→ grep 能量误差 →
调 plot_1d_validation.py 出图。用法：`bash $MULTI/work/eos_opacity_tools/run_all_cases.sh`。

## 8. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
