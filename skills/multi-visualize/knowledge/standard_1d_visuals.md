---
title: 1D 算例标准可视化规范 v1.0（定稿，用户 2026-09-07 冻结）
skill: multi-visualize
category: standard
source_anchors:
  - work/viz_tools/make_1d_visuals.py
  - agent/pitfalls/laser-pulse-edge-output-resolution.md
  - cases/CH-Au-Diamond_800J-1ns/viz/
  - cases/preheat/CH-Al-SiO2_rad140-60/viz/
doc_ref: "用户指令（2026-09-07，多轮迭代后定稿冻结），本文件为规格正本"
created: 2026-09-07
last_verified: 2026-09-07（双算例 9+9 张全量复验）
verifier: claude+双算例实测（激光/辐射分支）
status: stable-frozen
tags:
  - 可视化规范
  - 定稿
  - make_1d_visuals
  - 热图
  - 激光波形
  - 辐射源
  - 激波轨迹
---

# 1D 算例标准可视化规范 v1.0（定稿）

## 0. 总则

所有 1D 模拟算例，跑完默认出 **9 张**（无驱动 8 张）。

**实体实现位于 MULTI1Dvisual 包内**（2026-09-07 迁入，用户指令：
"放到包里作为工具函数，单独调用，不影响主窗口运行逻辑"）：
`$MULTI_APP/MULTI1Dvisual2.3/utils/standard_visuals.py`（StandardVisualizer
类；导入零副作用——不建 QApplication、不强设 matplotlib 后端，主窗口
可安全导入复用）。

```bash
# 单独脚本调用（offscreen）
python3 $MULTI_APP/MULTI1Dvisual2.3/utils/standard_visuals.py <算例目录> [--shock ...]
```
```python
# 库用法（主窗口/其它脚本内）
from utils.standard_visuals import StandardVisualizer
StandardVisualizer(case_dir).run()          # 全套 9 张
StandardVisualizer(case_dir).run(shock=True, vars_=("PT",))
```

兼容旧入口：`$MULTI/work/viz_tools/make_1d_visuals.py` 已改薄壳转调
包内（勿在薄壳改逻辑）。产物在 `<算例>/viz/`。数据热图用包内
PlotEngine；两张示意图 matplotlib 直画。**勿自写脚本复刻、勿每次
重写**——微调用现成选项。数据访问全走 Fort10Parser 只读 API
（get_spatial_data_all_times / get_time_series_global /
get_grid_positions），不触碰主窗口状态。

| # | 文件 | 内容 |
|---|---|---|
| 1-6 | `heat_{R,PT,TE}_{xc,lc}.png` | 密度/压强/温度 × 欧拉/拉格朗日热图 |
| 7 | `target_layout.png` | 靶与驱动设计示意 |
| 8 | `grid_layout.png` | 初始网格划分示意 |
| 9 | `laser_waveforms.png` 或 `rad_source.png` | 驱动图（自动识别） |

## 1. 六张数据热图规格

- **引擎**：`PlotEngine.plot_interpolated_heatmap`，transpose（x=时间 ns，
  y=位置 µm），n_interp_points=600，cmap **jet**，dpi 180
- **坐标**：欧拉 `XC`（当前格心）/ 拉格朗日 `LC`（**初始格心**，
  time-invariant——用户定稿；CMC/CMI 是质量坐标 g/cm²、NC/NI 是
  格号，均非规范所指）
- **变量与色标**（可 `--vmin-V/--vmax-V` 覆盖）：
  - R：线性，95% 分位上界、下界 0，单位 g/cm³（2026-09-07 用户定稿：不再强行 log）
  - PT：线性，**95% 分位**上限（极值常为烧蚀面尖峰）、−vmax/20 下限，
    **单位 GPa**（factor 1e-10）
  - TE：线性，同 R 策略，单位 eV

## 2. target_layout.png 规格（靶与驱动示意）

- **布局**：x=位置（层从左到右竖条带）、y=示意横向 [0,1]；
  **无 colorbar、无坐标轴**；figsize **8.5×7**（整图近正方 w/h≈1.2）；
  dpi 180
- **层色**：初始密度 R[0] 纯色带（无演化结构）；色按**密度 rank 均匀
  采样 jet[0.12, 0.88]**（数值映射时相近密度如 2.65/2.70 几乎同色，
  rank 保区分度且色序随密度单调）
- **线**：层间白竖线 lw1.8、**靶外缘黑框 lw2.8**——所有线**只画在
  靶范围 [0,1] 内**（axvline 贯穿全轴会超出，禁用）
- **标注**：宽层（>5% 靶厚）"材料 厚度µm"竖排层内（白字黑描边 11pt）；
  窄层引线到顶部交错（y=1.07/1.16，黑字 9.5pt）；相邻同材料网格段
  自动合并
- **驱动箭头束**：9 个沿 y∈[0.05,0.95] 铺满靶高（光束截面覆盖整个
  靶面），水平指向靶面：激光 `inter<0`→左侧向右 / `inter>0`→右侧向左；
  辐射 `betar≠0`→右侧向左 / `betal≠0`→左侧向右；crimson，lw3.0，
  mutation_scale 28；参数摘要（波长/强度/脉宽 或 Tr,max/时长）竖排
  箭头束外侧 10.5pt

## 3. grid_layout.png 规格（网格划分示意）

与 target_layout 同布局（竖条带、近正方、无轴）：

- 层底 rank 色 **α0.35** 浅衬
- **竖直细线 = 初始界面**（X[0]，灰 0.25、lw0.55，仅 [0,1] 内；
  疏密即格宽——细格段成密带、粗格段逐线可分）
- 层界面黑粗线 lw2.2（仅 [0,1]）；靶外缘黑框 lw2.8
- 各**真实网格段**（不合并）标 "材料\nnc=…, dx=…µm"：宽段竖排层内
  10pt；窄段引线 9pt；标题含总格数

## 4. 驱动图规格（自动识别：有 &pulse_wkb→激光；betar/betal≠0→辐射）

- **laser_waveforms.png**：三线 = 名义解析（ttab/ptab×pimax，黑实线）
  + fort.10 **LASER 差分**（入射，蓝点线）+ **DELAS 差分**（吸收，
  红虚线）；y 轴量级自适应（10^n 取峰值量级）；stdout 报能量闭合
  （入射/吸收 J/cm²、吸收率、峰值）
- **rad_source.png**：名义 Tr(t)（ptab×trad，黑实线）+ fort.10 **TR
  源边界格**时间序列（红点；betar≠0 取右格，betal≠0 取左格）

## 5. 可选项

| 选项 | 说明 |
|---|---|
| `--shock` | 激波轨迹白线（lw2 黑描边，仅欧拉热图），默认不画 |
| `--shock-rho/--shock-x0/--shock-xmax` | 轨迹判据（默认最深层 r0×1.2、层左/右界面） |
| `--vars R,PT` / `--coords euler` | 子集出图 |
| `--vmin-PT/-vmax-PT` 等 | 色标覆盖（如看烧蚀面尖峰 `--vmax-PT 1500`） |
| `--driver auto/laser/rad/none` | 驱动类型覆盖 |
| `--outdir` / `--no-driver` | 输出目录 / 跳过驱动图 |

## 6. 实现口径（踩坑内嵌，详见 pitfall laser-pulse-edge-output-resolution）

- 吸收/入射功率一律 fort.10 **累计值差分**（LASER/DELAS）；不用
  fort.11 Σdepo·w（dt_aout 欠采样段 trapz 出荒谬吸收率）
- data.in 解析只认**赋值行**、剥 `!` 注释（头注释 "pimax = 800J/..."
  会被正则抢匹配）；`&layer` 块匹配锚定**行首 `/`**（块内注释
  "um/cell" 的斜杠会截断非贪婪匹配 → 材料名变 '?'）
- PlotEngine save_figure 静默 False 必须 assert
- 方波沿要在图上"看起来方"：算例 dt_bout ≤ 沿宽（沿取脉宽 ~1%）
- 绘图标签一律英文（PRL serif 无 CJK 字形）

## 7. 定稿产物指纹（2026-09-07 双算例全量复验）

- **CH-Au-Diamond_800J-1ns（激光）9 张**：吸收率 100%（wkb 口径，
  DELAS=LASER=159160 J/cm²）；--shock 轨迹 24.8 km/s
- **包内迁移验证**（2026-09-07）：包内工具与旧 work/viz_tools 实现
  18 张产物 md5 逐字节一致；导入后 QApplication 实例 None、matplotlib
  后端不变（零副作用实测）
- **preheat/CH-Al-SiO2_rad140-60（辐射）9 张**：名义 Tr 140 eV vs
  边界 TR 130.6 eV
- 旧 plot_1d_validation.py（迁移验收 E 条目 density_heatmap/
  profiles_mid）继续并存，不替代
