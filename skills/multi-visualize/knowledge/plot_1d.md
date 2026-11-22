---
title: plot_1d_validation.py 调用约定与产物判读
skill: multi-visualize
category: internals
source_anchors:
  - work/eos_opacity_tools/plot_1d_validation.py:L22-L26
  - work/eos_opacity_tools/plot_1d_validation.py:L36-L94
  - work/eos_opacity_tools/plot_1d_validation.py:L97-L162
  - 材料迁移验证规范.md §E
doc_ref: "材料迁移验证规范.md §E（E1-E4 验收条目）"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - plot_1d_validation
  - 热图
  - 剖面
  - 判读
---

# plot_1d_validation.py 调用约定与产物判读

## 1. 用法

```bash
python3 $MULTI/work/eos_opacity_tools/plot_1d_validation.py <算例目录>
# 例: python3 $MULTI/work/eos_opacity_tools/plot_1d_validation.py validation_cases/TiCheck
```

前提：算例目录内有 `fort.10`（ASCII）。产物**存于算例目录内**：
- `density_heatmap.png` — 密度热图 ρ(x,t)
- `profiles_mid.png` — 中间时刻（最接近 texit/2 的记录）密度/温度/压强三联剖面

stdout 报告：`记录数: N, 时间: t0 ~ t1 s`（L110）。

## 2. 实现要点（判读异常时对照）

- 解析器 `read_fort10_ascii`（L36-L94）：两节头（计数+变量名+索引+值）跳过第一节，
  第二节按变量名连续重复切段（`var_slices`，L64-L70），逐行读值；
  **e12.5 省略 e 的指数用正则插回**（L82-L86）
- 热图（L112-L129）：pcolormesh，X=时间（ns)、Y=位置（μm，拉格朗日随体坐标 XC）、
  色标=ρ；Y 轴限首记录的初始靶范围（`d["X"][0]`）
- 剖面（L131-L157）：`imid = argmin|times − 0.5·texit|`；三联图
  ρ / Te+Ti / PT+PE（横轴 μm）

## 3. 验收判读条目（材料迁移验证规范 §E）

| 条目 | 标准 | 怎么看 |
|---|---|---|
| E1 | 两 PNG 存在且非空；解析记录数 ≥ 50 | stdout 的"记录数" |
| E2 | 热图密度场随时间连续演化、无断带/无 NaN 空洞 | 目视 |
| E3 | 剖面曲线光滑、量纲合理（ρ>0；T 在表覆盖范围内；P 无异常振荡） | 目视+物理判断 |
| E4 | 中间时刻实际时间在 texit 的 45%–55% | profiles_mid.png 标题里的 t 值 |

算例输出频率要求：`ns_bout=1`（或 dt_bout ≤ texit/100）——否则记录数不足（E1 失败）。

## 4. 异常图诊断

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 记录数 <50 / 热图断带 | ns_bout 太大 | 改 ns_bout=1 重跑算例 |
| 脚本报 float 解析错 | fort.10 非 ASCII（跑错程序）或文件损坏 | 确认是 IFE-2015 产物 |
| 热图空洞/NaN | 运行中崩溃 | 查 output（multi-case-runner） |
| 剖面 Pe≈0 或压强量级离谱 | 表单位错误（历史事故） | 与源表绝对值对照（agent/pitfalls/pressure-unit-confusion.md） |
| 中间时刻偏离 50% | 输出稀疏 | 同 E1 处理 |

## 5. 批量绘图

`run_all_cases.sh`（L8-L37）：遍历 `validation_cases/*Check`（跳过 TiCheck），
逐个重跑（如需要）+ 等待 ktag 消失 + grep 能量误差 + 调 plot_1d_validation.py。

## 6. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
