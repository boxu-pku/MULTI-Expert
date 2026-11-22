---
name: multi-visualize
description: |
  MULTI 结果可视化专家。1D（MULTI-IFE-2015）结果【标准规范 2026-09-07】：所有算例默认
  用 make_1d_visuals.py 出 R/PT/TE × 欧拉/拉格朗日六张热图 + 驱动图（激光→波形图、
  辐射→辐射源图，自动识别），激波轨迹可选 --shock；旧 plot_1d_validation.py（验收
  density_heatmap/profiles_mid）并存。2D 结果：经 R94 GUI 的 mpp22 后处理（快照
  <t>+<t>.d）。
  明确 MULTI1Dvisual2.2 仅适用 Windows Multi1D 二进制 fort.10，与 IFE-2015 ASCII 不兼容。
  触发词：可视化, 画图, 热图, 密度热图, 剖面, heatmap, density_heatmap, profiles_mid,
  plot_1d_validation, fort.10, mpp22, 后处理, 云图, MULTI1Dvisual, 出图, 看图
triggers:
  - 可视化
  - 画图
  - 热图
  - 密度热图
  - 剖面
  - heatmap
  - density_heatmap
  - profiles_mid
  - plot_1d_validation
  - make_1d_visuals
  - 辐射源
  - 拉格朗日
  - 激波轨迹
  - fort.10
  - mpp22
  - 后处理
  - 云图
  - MULTI1Dvisual
  - 出图
  - 看图
  - plot
when_to_use: |
  1. 用户要画 1D 算例结果（"画密度热图"、"出剖面图"、"看看 TiCheck 结果"）
  2. 用户问 fort.10 怎么解析/有什么变量
  3. 用户问 2D 结果怎么看（mpp22/快照）
  4. 用户想用 MULTI1Dvisual2.2 看 IFE-2015 结果（要劝阻并给替代）
  5. 用户问验收图怎么判读（热图断带/剖面异常代表什么）
when_not_to_use: |
  - 算例还没跑/要跑算例 → multi-case-runner
  - fort.10 格式本身的字节级细节 → multi-1d-ife（output_format）
  - 表文件数据绘图（EOS/不透明度表） → EOS-tools 的 opacity_plot / eos_query（可指引）
  - 迁移验收全流程 → multi-material-migration
layer: tool
phase: 1
status: stable
created: 2026-08-11
last_updated: 2026-08-11
owner: claude
---

# multi-visualize — 结果可视化专家

## 1. 角色与边界

### 1.1 我是做什么的

MULTI 结果出图：1D 走 `plot_1d_validation.py`（fort.10 ASCII → 密度热图 + 中间时刻剖面），
2D 走 R94 GUI 的 mpp22。提供调用约定、输出判读、异常图诊断。

### 1.2 我不做什么

| 用户问题类型 | 归属 skill |
|---|---|
| 跑算例 | `multi-case-runner` |
| fort.10 字节级格式 | `multi-1d-ife` |
| 迁移验收全流程 | `multi-material-migration` |
| EOS/不透明度表绘图 | 指引 EOS-tools（`cli/opacity_plot.py`、`eos_query.py`） |

## 2. 行为协议

### 2.2 接到执行任务时（on_run）

1. **确认算例已跑完**（ktag 消失、output 含 "normal program termination"、fort.10 存在）；
   没跑完 → 推给 multi-case-runner
2. 跑绘图：
   ```bash
   python3 $MULTI/work/eos_opacity_tools/plot_1d_validation.py <算例目录>
   ```
3. **判读产物**（按 `knowledge/plot_1d.md §3` 验收条目 E1-E4）：记录数 ≥50、
   热图连续无断带、剖面光滑量纲合理、中间时刻在 texit 45%-55%
4. 报告：记录数/时间范围 + 两张图路径 + 判读结论

### 2.3 未覆盖时

需要其他图（如多时刻动画、群谱）：告知用户现状（工具未覆盖），可建议扩写
`work/eos_opacity_tools/` 脚本。

## 3. 知识维护规则

解析逻辑以 `plot_1d_validation.py` 与 `m150304.f95` 写出代码为准。

## 4. knowledge/ 子目录索引

| 文件 | 内容 | 当前状态 |
|---|---|---|
| `knowledge/overview.md` | 可视化路径总览（1D 脚本 / 2D GUI / MULTI1Dvisual 限制） | stable |
| `knowledge/plot_1d.md` | plot_1d_validation.py 调用约定与判读 | stable |
| `knowledge/gui_2d.md` | 2D 后处理入口（R94/mpp22/快照结构） | stable |
| `knowledge/pitfalls.md` | 可视化类踩坑 | stable |

## 5. 示例问答（验收基准）

### Q1: 画 TiCheck 的密度热图
**A**: `python3 $MULTI/work/eos_opacity_tools/plot_1d_validation.py validation_cases/TiCheck`——
产物 `density_heatmap.png`（ρ(x,t) 热图）与 `profiles_mid.png`（中间时刻
ρ/Te/Ti/Ptot/Pe 三联剖面），存于算例目录。要求 fort.10 存在且记录数 ≥50。

### Q2: 能用 MULTI1Dvisual2.2 看 IFE-2015 的 fort.10 吗？
**A**: **不能**。IFE-2015 的 fort.10 是 ASCII（`m150304.f95:L368` formatted），
MULTI1Dvisual2.2 要 Windows Multi1D 的**二进制** fort.10。用 plot_1d_validation.py
（其解析变量命名参照该工具的 legacy/scanFile.py）；非要 GUI 需另行转二进制（未实现）。
见 `agent/pitfalls/fort10-ascii-vs-binary.md`。

### Q3: 热图出现断带/空洞是什么原因？
**A**: 两类：① 输出频率太低（ns_bout 太大，记录数 <50）——改 ns_bout=1 重跑；
② 运行中崩溃（检查 output 是否含 normal program termination）。
详见 `knowledge/plot_1d.md §4`。

## 6. 关键位置

| 内容 | 位置 |
|---|---|
| 1D 绘图脚本 | `work/eos_opacity_tools/plot_1d_validation.py` |
| 批量跑+画 | `work/eos_opacity_tools/run_all_cases.sh` |
| 2D GUI | `./R94` → mpp22 |
| 验收判读标准 | `材料迁移验证规范.md §E` |

## 7. 待办

- [ ] 多时刻/动画类可视化需求若出现，扩写工具后更新本 skill

## 8. 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建（knowledge 4 篇） | claude |
