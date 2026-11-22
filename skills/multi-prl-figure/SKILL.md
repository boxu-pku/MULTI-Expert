---
name: multi-prl-figure
description: |
  MULTI 项目出版级曲线图风格专家（IM_tool PRL 风格，2026-09-17 三轮指正收敛 +
  2026-09-22 增补）。凡是"汇总图/出版图/漂亮一点/PRL 风格/报告插图/逐发对比图/
  波形展示图"等单图或小面板曲线类图件，一律按本 skill 配方出图，禁止裸 matplotlib
  默认风格。数据图（速度-时间、能量扫描、Hugoniot、 Us/Up、激光波形、对比实验模拟）
  是典型对象；热图类走 multi-visualize（PlotEngine 本体），不在本 skill 范围。
  触发词：PRL 风格, 出版图, 汇总图, 美化, 画好看, 报告插图, 曲线图, 对比图,
  summary figure, publication style, IM_tool 风格
triggers:
  - PRL 风格
  - 出版图
  - 汇总图
  - 美化
  - 报告插图
  - 曲线图
  - summary figure
  - publication
---

# MULTI 出版级曲线图（IM_tool PRL 风格）

## 何时用本 skill

任何要给用户看/进报告/进论文的**曲线类图**（速度-时间、扫描汇总、波形、
实验 vs 模拟对比）。工作图（快速诊断）不必；热图与标准九件套走
multi-visualize。

## 核心配方（照抄即对）

```python
import sys
sys.path.insert(0, "$MULTI_LIBS/IM_tool/IM_tool")
from im_app.core.plot_style import (PRL_COLORS, PRL_STYLE,
                                     apply_prl_style, save_prl_figure)
import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
mpl.rcParams.update(PRL_STYLE)
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(4.8, 4.2))          # 4.8 in 单栏宽
apply_prl_style(fig, ax, xlabel="Time (ns)",
                ylabel=r"Rear-surface velocity (km/s)")
ax.tick_params(which="both", top=False, right=False)  # 仅左下刻度（覆盖 PRL 默认）
ax.xaxis.label.set_size(15)    # 轴标 15（4.8in 画布收敛值）
ax.yaxis.label.set_size(15)
ax.tick_params(labelsize=12)   # 刻度 12
ax.legend(fontsize=10.5, frameon=False, loc=<空白区>)  # 图例 10.5 无框
save_prl_figure(fig, out)      # 300 dpi + tight bbox
```

字号基线 **15 / 12 / 10.5**（轴标/刻度/图例；2026-09-17 三轮指正收敛，
勿用 IM_tool 默认 20/16/14——那套是给交互大画布的）。**轴标按画布分档
（2026-09-22 指正）**：单面板 4.8×4.2 用 15；双面板叠放（4.8×5.9 类）
轴标降到 **13**——面板多了 15 会显得过大挤压版面。

## 历史指正全录（每条都改过两三次才收敛，勿再犯）

1. **仅左下刻度**：`top=False, right=False`（apply_prl_style 默认开了
   上下右，必须显式关掉）。
2. **图例不压线**：先想清楚曲线的空白区再选 loc；无框 frameon=False；
   实在没空白就扩 ylim 给图例腾位（2026-09-16"图例扩范围"指正）。
3. **标注不与图例/曲线相撞**：标注位置以**数据保证空白**的角落为准，
   不要猜——速度类图前段基线恒为 0，贴虚线左下 (x=e1-0.25, y=0.05,
   ha="right", va="bottom") 是保证空位（2026-09-22 两次指正：顶部贴线
   会被图例挡住）。角标（如总能 E）同理放脉冲结束后的空白角。
4. **无标题**：出版图不放 set_title，发次/算例名用图例文本或角落小标签
   （如 "SHOT051" 右上，bold 12.5）。
5. **标签纯英文**：图例/轴标/标注一律英文（serif 无 CJK 字形，中文出
   方块；无 Glyph missing 警告 = 图内无 CJK 的硬证据）。
6. **激光波形 = 线性插值 + 线性坐标**：itype=4 + mtab=1 的表是线性折线，
   绝不能画成 steps-post（2026-09-21 指正）；断点可叠小圆点。**坐标轴
   一律线性**（2026-09-22 指正"log 看着奇怪"勿用）——量级差靠断点圆点
   与角标承载，弱脚若贴底属正常物理呈现，勿为"看清"而换 log。
7. **激光面板角标只标总能**："E = xxx J"（= 注量×光斑面积）放脉冲结束
   后的空白角（2026-09-16 指正，勿标多行参数）。
7b. **DELAS/LASER 差分单位坑**：fort.10 全局量取回是**秒**时基，差分
   必须先 ×1e9 转 ns 再 ×1e2 才是 W/cm²——用秒时基会大 1e9 倍直接飞出
   量程（2026-09-22 指正"absorbed 与 incident 不重叠"即此坑）。健康
   检查：临界面沉积下 absorbed/incident 积分比应 ≈1.00；若两线不重叠
   先查单位再怀疑物理。
8. **双面板共享 x 轴**：sharex + hspace≈0.06，字号统一；上面板刻度数字
   自动隐藏（tight_layout 处理，出图后仍要目检一次）。**时间轴必须从
   0 开始**（2026-09-22 指正）——下面板激光的完整历史（尤其"早期无脚"
   这类结论靠前期空白展示）是图义的一部分，截窗会砍掉波形。
9. **exp vs sim 线型约定**：实验 = 黑（raw 细 0.6 + 趋势粗 1.7），
   模拟 = PRL red（raw 细 + 趋势粗虚线）；标记：实验实心圆带黑边
   （ms 6.5, mec k, mew 0.7），模拟方块。
10. **每图出完必须目检**：本环境视觉通道不稳，优先 analyze_image+CDN
    URL，失败则转文本/数值校验并明告用户"建议人工过目"。
11. **出图前必须跑程序化重叠检测（2026-09-23 用户定规，必要条件）**：
    图例/角标/所有标注两两 bbox 互检（**文字 vs 文字也要查**——当日剖面图
    右上角算例名与灰色 "foam | rear CH" 注标相撞就是漏查文字对）+ 每个
    bbox 对全部曲线采样点碰撞测试，全部 0 命中才算 CLEAN、才能交付；
    视觉通道损坏时此项是唯一硬闸。范本：
    `cases/X_phase_contrast/make_backing_profiles.py` 末段
    overlap-check（legend.get_window_extent + transData.transform 采样）。
    **2026-09-28 增补**：图例 bbox 对曲线/点的碰撞要用
    `legend.get_window_extent()` × 视窗内数据采样（先按 xlim/ylim 裁剪
    再 transform，否则被裁掉的线段会假命中）；条目多（≥8）时图内放
    不下就**移轴外**（底部 ncol 列），勿硬塞——范本
    `reshock/reshock_pc_summary.py`（双列图内版曾压 143 个数据点）。

## 参照脚本（照抄布局与字号，勿凭记忆重写）

- `cases/HMX_simulation/make_shots_summary.py` —— 散点汇总图定稿范本
  （2026-09-17 三次指正的收敛体）
- `cases/HOPG_simulation/scheme2_scan/flat_scan/laser_waveform_pub.py`
  —— 激光波形出版形态（名义入射+吸收+E 角标）
- `cases/H2O_multi_layer/visar_match_051_054/make_abs_pubfigs.py` ——
  双面板（速度+激光）逐发出版图范本（2026-09-22，绝对时轴）
- IM_tool 本体：`$MULTI_LIBS/IM_tool/IM_tool/im_app/core/plot_style.py`

## 增补：分析/对照类图件的累积裁定（2026-09-27 double_shock_pc 收敛，用户定规）

12. **汇总/分析图同样只认 4.8in 三档字号**（15/12/10.5 + 仅左下刻度 +
    无标题）：Hugoniot/状态对照等分析图不是"工作图"，进交付物就按本
    配方（2026-09-27 用户打回"字体大小不合格"，即用了 8in 画布+默认
    字号）。图上**不重复标注**图例已能区分的信息（颜色对应发次就不再
    逐点标发次号）。
13. **换坐标面三件套**：数据坐标、轴标签、xlim **必须同步改**——漏改
    xlim 会全图画在轴外，且 annotate 的 window extent 退化成单位盒、
    overlap 检测报假阳性（2026-09-27 P–V→P–ρ 实录）。
14. **轴限从数据取**：上限 = 所画曲线实际极大值 × 1.05–1.06。用状态
    中值×倍数会把曲线峰截在面板外（"右侧图没画全"指正）。
15. **savefig 一律 `bbox_inches='tight', pad_inches=0.3`**：tight 裁剪
    会裁到轴线，边框紧贴画布边缘（指正实录）。
16. **overlap 检测器过滤视界外幻影刻度**：locator 生成但 ylim 外不绘制
    的 tick 仍有 bbox，会与标题等假报碰撞——只统计落在所属 axes 邻域
    （expanded ~1.16）内的刻度。
17. **组合图（热图+剖面双子图）**：共享 ylim 裁到数据带并**画同高参考
    线**显式化共享（否则空白带会被读成"轴没共享"）；热图内标注白字
    黑描边字号 ≥10.5–11；右面板 legend 放右上；suptitle 16pt；
    PlotEngine 复用 = 画图前重定向 `eng.fig/eng.ax` 到外部子图。
18. **模型同图规则**：剖面/热图类 **FEOS 与 porous C 不同图**（用户
    裁定）；P–CR/Hugoniot 对照类可同图（绿=feos、青=pc 惯例色）。
19. **Hugoniot 面选择**：含 Rayleigh 线 → P–V（直线只在比容面；P–ρ
    投影是双曲）；无 Rayleigh → P–ρ（状态点分辨更好）。marker 约定：
    波前态 state1 空心圈、波后态实心圈、理论点白底星；主 Hugoniot
    黑色粗实线、二次分支细彩线。
20. **色标跨引擎传值核对因子口径**：PT 文档定标 = `p95×1e-10`（GPa，
    与 value_factor 同口径）——除以 1e12 得 Mbar 数值直接传入 = 范围
    小 100 倍、全图糊顶（两次打回实录）。
21. **参照脚本（2026-09-27 新增）**：
    `cases/double_shock_pc/reshock/reshock_pc_summary.py`（Hugoniot
    汇总范本：4.8in 三档、黑主线、双 marker 约定、overlap_report）；
    `reshock_49190_states.py`（组合图范本：PlotEngine 重定向、共享轴
    参考线、字号基线）；`reshock_49190_secondary.py`（P–V Rayleigh/
    理论分支范本）。

## 与 multi-visualize 的分工

- 诊断/热图/标准九件套 → multi-visualize（PlotEngine 本体，勿复刻）
- 出版级曲线/汇总/对比 → 本 skill（IM_tool PRL 配方）
- 同一批数据两种都要时：先出诊断套，再按本配方出出版图
