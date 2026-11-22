# Recipe: 批量重跑全部材料验证算例（run_all_cases.sh）

> 场景：批量回归（如工具链/表文件变更后），重跑 `validation_cases/*Check` 并刷新可视化。
> ⚠ 会覆盖各算例的 output/fort.10/PNG —— 这些是人工验收档案；
> **执行前必须向用户确认**。TiCheck 被脚本跳过（首个已确认档案）。

## 1. 执行

```bash
bash $MULTI_ROOT/work/eos_opacity_tools/run_all_cases.sh
```

脚本行为（`run_all_cases.sh:L8-L37`）：
1. 遍历 `$MULTI/validation_cases/*Check`（跳过 TiCheck）
2. 无 `multi` 可执行 → `./RUN`；有 → 清 `fort.10 fort.11 fort.12 block multidata.mod output cputime` 后 `./RUN`
3. 等 ktag 消失（最多 120 秒；超时跳过绘图）
4. `grep "normal program termination" output` → 提取能量误差打印
5. 调 `plot_1d_validation.py` 刷新两张 PNG

## 2. 输出判读

```
===== AgCheck =====
  完成, 能量误差: 3.2e-08
  （两张 PNG 路径）
```

- 每个算例应"完成"+ 误差 <1e-6
- "!! 未正常结束" → 单独复查该算例（tail output；常见问题见
  `../knowledge/pitfalls.md`）
- 已知 CAVEAT：DiamondCheck（1.17e-4，表范围局限）、CliquidCheck（0.58 ns 崩溃）——
  数据局限非回归失败（`MULTI-2D_材料库清单.md §1.2`）

## 3. 时长预估

约 47 个算例 × 秒级 + 绘图 ≈ 15-30 分钟。建议后台：
`nohup bash run_all_cases.sh > batch_run.log 2>&1 &`

## 4. 相关

- 单算例流程：`ticheck.md`
- 可视化判读：`multi-visualize/knowledge/plot_1d.md`
