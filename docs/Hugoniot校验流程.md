# 冲击 Hugoniot 校验流程（第二轮核验）

> 用途：对每种材料的 EOS 表做冲击 Hugoniot 关系校验（Us-Up、P-ρ），独立于迁移验收的第一轮（格式+跑通）检查。
> 试点材料：Al（2026-08-13 加密网格重跑+全理论线对比，结果见 `validation_cases/Al/hugoniot_summary/`）。

## 一、物理设置

厚平板 + 一端恒定辐射温度浴 → 准定常（弱衰减）冲击波：

- 算例模板：`work/eos_opacity_tools/make_hugoniot_cases.py <材料> <rho0> <厚度cm> <trad列表>`
- Al 当前配置：100 μm 厚、**800 单元**（0.125 μm/单元）、**400 条输出记录**
  （2026-08-13 起替代旧 200 单元配置；过渡区约 4 单元、波后平台分辨充分）
- 驱动端（右侧）辐射浴恒定（itype=2, betar=1）
- Al 强度系列：trad = 50/75/100/200/300 eV 五档
  （`validation_cases/Al/hugoniot_T50|75|100|200|300`；T75 为填补 Up 2–6 km/s 空档新增）

### 标准配置：quiet start（2026-08-19 用户定版，所有 EOS 入库校验启用）

**状态方程入库 Hugoniot 校验一律启用 quiet start，参数与 BN 族验证保持一致**：

- `iquiet = 1, tquiet = 0.05`——冻结 Te/Ti<0.05 eV 的冷固态单元的流体动力学
  （单元被加热超过阈值后解冻），消除辐射前驱在冷区吹出的污染流；
- **冷初态 `te0 = ti0 = 0.03` eV（~350 K）**——贴参考线 300 K 初态
  （旧模板 0.1 eV 偏暖，带来 ~0.4 pct 系统偏差）；
- 实测收益（BN 族，2026-08-19）：波前 v_pre 中位归零、能量误差最高改善
  5 个量级（0.29→4.3e-6）、弱档救活（cBNFEOS T75 从提取失败→12 点
  dUs −1.07%）、可用档 dUs 系统性改善 ~0.3-0.7 pct；
- 限制：驱动能量不足的档（如 cBNFEOS T50）冲击平台不成形是本质问题，
  quiet start 不能救；
- **工具链要求**：需 2026-08-18 13:47 后含 quiet start 的 `m150304.f95`
  重编译的 multi；旧 binary 遇 `iquiet` 报
  "Cannot match namelist object name iquiet"（重编译：
  `cp -s $MODULE/m150304.f95 multi.f95; cp $MODULE/multidata.mod .;
  gfortran multi.f95 -o multi`）。

## 二、波前/波后提取（extract_hugoniot.py）

```
python3 work/eos_opacity_tools/extract_hugoniot.py <算例目录> <rho0>
```

### 方法

1. 波前 = 密度抬升 10% 的最左位置（**线性插值到亚单元精度**）
2. **Us(t) = 波前轨迹 x_f(t) 的当地冲击波速度**：以每个采样时刻为中心、
   ±12 条记录（≈±0.5 ns）做**局部线性拟合**，斜率即 Us（冲击向左传播，
   斜率为负，取绝对值）；同时给出拟合 R²。不做全程多项式拟合——衰减波
   全程单一多项式会把当地速度平均掉。拟合窗口与 R² 写入逐点溯源图，
   可逐点人工复核。
3. 波后状态 = **自适应平台取样**：从波前向后扫描压强剖面，连续 3 个
   相邻单元相对变化 <0.5% 处为平台起点，取其后 4 单元平均
   （2026-08-13 起替代固定 i_f+2..i_f+5 偏移——辐射前驱会把过渡区加宽，
   石英类材料达 ~14 单元，固定偏移会取进过渡区造成系统性负残差；
   Al 过渡区 ~4 单元时自动退化为原行为）；波前态 =
   i_f−30..i_f−10 单元中位数（ρ0、P0、v0；溯源图标题另给出 Te_pre 检验预热）
4. 每个采样点自带 Rankine-Hugoniot 动量残差 (P1−P0) vs ρ0·Us·(Up−Up0)

### 可用性门禁（A–E，替代旧版固定 10%~55% 时间窗）

| 门禁 | 判据 | 剔除的物理时段 |
|---|---|---|
| A | 波前态纯净：ρ_pre 在 ρ0±1% 且 \|v_pre\| ≤ 0.05 km/s | **自由界面稀疏波**（预热膨胀）污染波前态的时段（冲击快出界面时必然触发） |
| B | 局部轨迹斜率 < 0（冲击仍在前进） | 稀疏波追上冲击波后阈值位置倒退（斜率翻正）的时段 |
| C | 取样窗口不越界（i_f−30 ≥ 0） | 波前贴到计算域边界的时段 |
| D | ρ_post ≥ 1.05·ρ0 | 驱动建立期、冲击尚未成形的初始瞬态 |
| E | RH 动量残差 \|resid\| < 25% | 最终安全网 |

采样时在可用窗口内再跳过头部 5%（驱动建立期），均匀取 12 点。

### 逐点溯源图（hugoniot_point_profiles.py）

```
python3 work/eos_opacity_tools/hugoniot_point_profiles.py <算例目录> <rho0>
```

汇总图上每个点对应 `<算例>/hugoniot_points/point_XX_tYYns.png` 一张四联图：
ρ / v / P 剖面（聚焦激波区，标注波前、波前态/波后态取样单元）
+ **波前轨迹面板**（绿色=过门禁时段、灰色=被剔除时段、红色线段=本点
Us 的局部拟合窗口），标题含提取值、Te_pre、RH 残差、拟合 R²。

## 三、汇总出图（hugoniot_report.py）

```
python3 work/eos_opacity_tools/hugoniot_report.py <材料> <rho0> <算例目录...>
```

产物（在 `validation_cases/<材料>/hugoniot_summary/`）：
- `<材料>_hugoniot_points.csv`：全部采信点（含逐点 RH 残差、拟合 R²、记录号）
- `<材料>_hugoniot_UsUp.png` / `<材料>_hugoniot_Prho.png`：**全部理论线**
  叠加，IM-tool PRL 风格（serif、刻度朝内+次刻度、无框图例；
  复用 `IM_tool/im_app/core/plot_style.py`，不复制）
- 模拟点统一黑圆点、不分算例标记；**图上只画 RH 残差 ≤1% 的高置信点**
  （2026-08-13 起由 5% 收紧到 1%；1~25% 的点保留在 CSV 与
  `plot_data/multi_points_<材料>.csv` 的 `high_conf=0` 行，不上图）
- `plot_data/`：**绘图数据落盘**——每条理论线一个 CSV（Up/Us/P/ρ 四列，
  Celliers 另有误差带 CSV）+ `multi_points_<材料>.csv`（绘图用列序，
  含 high_conf 标记），脱离脚本也能复画
- 表文件与编号（MID）信息：`validation_cases/<材料>/材料表信息.md`
  （1D 六表 id 已字节级验证，2D 对应表另列，勿混用）

## 四、理论数据（IM-tool 标准库，全画）

`$MULTI_LIBS/IM_tool/IM_tool/im_app/standard_library/materials/`

- **Al 四条**：`Al_3717_sesame.txt`（SESAME 3717 主 Hugoniot，1000 点）、
  `Al_3720_sesame.txt`（SESAME 3720）、`Al_Celliers2005.txt`（实验解析拟合
  Us=17.992+1.167·(up−9.838)，带误差带 σ(a0)=0.078, σ(a1)=0.026）、
  `Al_FEOS.hug`（FEOS，列 Rho T P E Us Up，表头注明单位）
- 加载器：`hugoniot_report.py` 内 `load_theory_txt/load_theory_hug`
- 其他可用材料：Quartz（7360/7385/FEOS/Hamel2012）、cBN、C_diam、BN_LEA 等
- IM-tool 自带格式验证：`IM_tool/scripts/validate_hugoniot.py`

## 五、结果

### Al（2026-08-13，800 单元 + 门禁 A–E + 自适应平台取样）

5 算例 × 12 点 = 60 个采信点（CSV：`Al/hugoniot_summary/Al_hugoniot_points.csv`）。
1% 高置信阈值下出图 41 点：

| 算例 | Up 覆盖 (km/s) | Us (km/s) | ≤1% 点数 | 备注 |
|---|---|---|---|---|
| T50 | 1.1–2.4 | 6.4–8.9 | 5 | t<4.7 ns 冲击未定常（残差至 −13%），晚期贴线 |
| T75 | 3.2–4.7 | 9.5–11.9 | 9 | 贴线 |
| T100 | 6.7–8.3 | 13.9–16.3 | 11 | 贴线 |
| T200 | 31–34 | 44–48 | 11 | **平台取样修复后全程贴线** |
| T300 | 58–63 | 78–84 | 6 | 同上 |

- 自适应平台取样的重要修正：此前固定偏移取样在高驱动/宽过渡区下产生
  −4~−15% 系统性残差（T300 一度误判"P-ρ 偏高 10%"），实为取样位置落在
  过渡区内。**修正后 T200/T300 的 Us-Up 与 P-ρ 全程贴理论线（P-ρ 压 FEOS 线）**。
- 门禁自动性：T50 在 t≈10 ns 后（波前距左界 <25 μm）被门禁 A/B 全部剔除
  ——正是"冲击快出界面时自由界面稀疏波使点不可用"的时段。
- 四条理论线在 Al 上互相高度一致；MULTI 点全程贴合。
- 旧版产物存档：各算例 `hugoniot_points_v1_200cells/`（200 单元）、
  `hugoniot_points_v2_fixedwindow/`（固定窗口取样）、`hugoniot_summary/_archive_v1/`。

### Quartz（Multi_BACK，ρ0=2.65 α-石英，2026-08-13；改名前叫 Silica）

4 算例（trad=50/75/100/150 eV）×12 点 = 48 采信点，1% 高置信 27 点，
Up 2.6–25 km/s：

- **Us-Up 全程贴合四条理论线**（SESAME 7360/7385、Hamel 2012+误差带、FEOS）；
- **P-ρ 几乎压在 SESAME 7385 线上** —— Multi_BACK 这张 α-石英表行为最接近 7385；
- 辐射前驱加宽效应明显：过渡区 ~14 单元（Al 仅 ~4），是自适应平台取样的
  关键应用场景；晚期近界面点被门禁 A 正常剔除（T150 350 条记录仅 74 条过门禁）。

### Silica（Multi_BACK，ρ0=2.204 熔石英玻璃，2026-08-13；改名前叫 Quartz）

4 算例（trad=50/75/100/150 eV）×12 点 = 48 采信点，Up 2.6–21 km/s。
**对比基准说明**：四条石英理论线均为 α-石英 ρ0=2.65，与本材料初始密度不同，
仅作参照；主判据为**表自洽 Hugoniot 线**（`compute_table_hugoniot.py` 由
本表 eeos+ieos 反解 RH 能量方程得到，灰虚线，非独立理论验证）：

- **P-ρ 全程精确压在表自洽线上**（冲击物理实现与表插值一致）；
- Us-Up 与自洽线一致且落入 α-石英理论线散布带（该区间 Us-Up 对 ρ0 不敏感）；
- P-ρ 与 α-石英 2.65 线的偏移是 ρ0 不同的预期效应，不是误差。

### QuartzFEOS / SilicaFEOS（FEOS 模型表，2026-08-13 生成，08-14 换 EOS-tools 重转；改名前 SilicaFEOS/QuartzFEOS 互换）

FEOS 计算（`$MULTI_LIBS/FEOS/FEOS`，7387 α-quartz(2.65→QuartzFEOS) / 7386 fused silica(2.204→SilicaFEOS)，
TF+SoftSphere+Maxwell）→ **EOS-tools 转换**（1D 表，192×512 细网格）入库。
初版用 FEOS 自带转换器时发现其**两个 bug**（布局密度主序、能量单位 ×100，
见《MULTI-2D_材料库迁移指南.md》§7.4 与陷阱库），EOS-tools 版无此问题。

- **基准对照（QuartzFEOS）**：本表反解 Hugoniot 与 FEOS 官方 `Quartz.hug`
  对比 **P≤3.5%、Us≤1.3%**（含近环境端 +0.1%）——生成+转换链全通 ✅；
- Hugoniot 算例（各 4 档 ×12 点，dttevar/dttivar=0.5 限幅）：
  **全强度档干净贴线**（QuartzFEOS 42/48、SilicaFEOS 41/48 点 ≤1%，
  余点 4% 内）——T50/75/100/150 全程贴合 FEOS 线/自洽线 ✅；
- **曾出现的问题与修复（2026-08-14）**：初版算例在 T≥100 出现波后密度网格尺度
  持续振荡，诊断为**双温交换 sloshing**（振荡单元 Ti 被打到 0、Te 7-9 eV；
  FEOS TF 电子 EOS 的 Cv 结构使交换时间尺度远小于 dt，欠阻尼格式 overshoot）。
  修复：data.in 设 `dttevar=dttivar=0.5`（每步 Te/Ti 相对变化限幅），振荡消除，
  提取点全部回线。降 fei 无效。详见 `agent/pitfalls/two-temperature-sloshing.md`；
  `make_hugoniot_cases.py` 模板已默认带 0.5。

### CH（Multi_BACK，ρ0=1.044，2026-08-14）

3 算例（trad=50/75/100 eV）×24 点 = 72 采信点（高置信 70 点），Up 4.9–20.6 km/s。
**三线判据**：

- **表自洽线**：Us-Up 与 P-ρ 全程压线 ✅；
- **PS 表交叉参照**（`REF_HUG` 机制首例，PS_eos 自洽反解，同为 1.044
  聚苯乙烯独立表）：两表互差 ≲3%（Up≤20 km/s），提取点落两线之间；
- **CH SESAME 7592**（IM-tool reference_curves，2026-08-14 加入）：
  重叠段 70 高置信点 Us 中位 **+9.1%**（T100 +6.9%）；7592 低压端压缩比异常
  （η≈2.0 @ 0.13 Mbar，多孔 CH EOS 特征）——非同一初态材料，仅作参考带；
- **预热限制显著**：低 Z + 20 群辐射穿透深，T150 预热在冲击成形前吞没全靶
  （350 条仅 1 条过门禁），该档不可用；T50-T100 可用窗也短于 Al/SiO2。

### PSFlash（FLASH LaserSlab IONMIX4 聚苯乙烯，ρ0=1.05，2026-08-14）——方法失效记录

**结论：Hugoniot 方法对本材料不可用**（所有驱动强度）。此前"点压自洽线"的
判断有误（12 点时目测），加密到 5 档 119 点后推翻。

失效模式与证据（三种独立判据，均已固化）：

1. **等温线判据**（`hugoniot_report.py` 的 `COLD_LOCUS` 机制，灰点划线自动叠加）：
   trad=35–55 eV 全部 5 档的提取点贴 **T=2 eV 等温压缩线**（中位 -1.4~-5.7%），
   而非表自洽 Hugoniot 线（Us 偏 -5%~-11%）。提取态内能几乎不增（E1-E0≈0
   vs RH 要求 0.26 Mbar·cc/g）——是（近）等温压缩波，不满足 RH 能量方程。
2. **剖面判据**（`hugoniot_case_profiles.py <case> <rho0>`，产 `profiles_check.png`）：
   ρ/v/P 各时刻剖面无冲击间断，全是渐进斜坡（辐射扩散介导波前），
   图上标注波前位置与平台取样窗，供人工检验取样逻辑。
3. **能量账**：机械能通量缺口 2.2e17 ≪ 辐射浴通量 6.4e18 erg/cm²/s（比值 ~29），
   波前由辐射通量供能。

物理原因：IONMIX 6 群在 100–1000 eV 段透明（κ~300 cm²/g，mfp≈33 μm ≈ 靶厚），
材料对自身驱动辐射**光学薄**——弱档成辐射介导等温压缩波、强档（≥60 eV）预热
吞没（冲击-壳层合并 + 表 LTE RH 无解）。**RH 动量残差门禁对两种模式都失明**
（动量守恒对二者都成立）。判定次序：先看剖面有无间断 → 再对照等温线 →
最后查表 RH 可解性。

本材料验证改为：PSFlashCheck（能量 5.6e-12）+ 源 cn4 绝对值对照 + 不挂 EPS 的
Te 剖面与 CHCheck 一致（76–78 vs 77 eV，EOS 独立交叉验证）+ 表级 PS/CH 交叉参照。

### WaterFEOS（FEOS 模型水，ρ0=1.0，2026-08-14）

3 算例（trad=75/100/150 eV）×~24 点 = 67 采信点，RH 动量残差 ≤1.2%。
参照线为**三源 RH**（FEOS/AQUA/Multi_BACK 源数据经同一 RH 求解器，
`work/water_migration_2026-08-14/hugoniot_3way_extended.npz`）——独立于转换链，
有判据意义（表自洽线已按用户要求移除出图）。

- **PSFlash 教训后的三重判据全过**：
  1. 等温线污染 ✅（P₁ 高出初温等温线 +224%~+1115%，真实冲击）；
  2. 剖面间断 ✅（三档均有清晰冲击跃变，`profiles_check.png`）；
  3. FEOS 源对比：同 Up 下 Us 中位 +0.6~+2.1%、ρ₁ −0.8~−2.7%；
     P-ρ 面 +9~+25% 是水 Hugoniot 饱和压缩段陡曲线放大 ρ 偏差所致。
- **T50 弱驱动不可用**：slab 火箭加速 + 全域预压缩破坏波前态纯度
  （门禁 A 拒绝；算例存 `work/water_migration_2026-08-14/abandoned_cases/`）。
- 算例需 inegpre=1 + tempmin 补丁（披露见 `材料表信息.md`）。

### Water（Multi_BACK hyades 族，ρ0=1.0，2026-08-14）

**8 源强算例**（trad=30–300 eV），可用 6 档（75–300）：68 采信点、
高置信 47 点，**Up 13.3–129.8 km/s（P 0.5→230 Mbar）**。
参照线为三源 RH（同 WaterFEOS；自洽线按要求不上图；出图仅高置信点）。

- **三重判据全过**：等温线污染 ✅（P₁ 高出初温等温线 +305%~+13700%，
  随源强单调增）；剖面间断 ✅（六档 profiles_check.png）；
  **Multi_BACK 源对比（同源基准）dUs 分档中位 −0.4%~+1.8%，
  46/47 点 ≤±3%**，Up 两个量级全程贴源；
- T300 冲击建立期暂态（RH 3~21%）由高置信过滤自然剔除；
  T200/T300 稳态点少（波前快速出域）；
- T30/T50 不可用（门禁 A 全拒——slab 火箭加速 + 预压缩，与 WaterFEOS 一致）；
- 跨源语境：对 FEOS 源 ~±1%、对 AQUA +12%（三源本征差异，非误差）。

### ParyleneHub（EOS_hub SESAME 7770，ρ0=1.29，2026-08-17）

8 档（30–300 eV），可用 5 档（30–125）×12 点 = 60 点（高置信 54），Up 1–42 km/s。
交叉参照 = 库内 hyades 源 Parylene 表（67×128，不同表，可能同溯 SESAME 7770）。
**三重判据全过**：等温线 ✅（P₁ 高出 +22%~+387%）；剖面间断 ✅；
**交叉参照 dUs 中位 +0.3%，54/54 ≤±3%**——两表一致性极好。
≥150 eV 预热吞没（gateA 全拒，同 CH T150）。

### LiFHub（EOS_hub SESAME 7270，ρ0=2.64，2026-08-17）

**Quartz 阻抗参考**（LiF/石英惯用阻抗匹配对，四条理论线 7360/7385/Hamel/FEOS）：
Us-Up 面一致偏 **+10.5~+16.9%**（LiF 离子晶体硬于相变软化石英，物理预期，
构成阻抗下边界带）；P-ρ 面不可比（石英相变高压缩）。

8 档（30–300 eV），可用 7 档（30–200）×~12 点 = 83 点（高置信 66），Up 1–110 km/s。
三重判据全过（等温线 +27%~+488% 剖面间断）。交叉参照 LiF_wk（WeiKang DFT）：
**有效段（Up≥40，T₁≥25 eV）dUs −2.4%~+0.6%**；低 Up 段 −32%~−63% 系
**参照自身冷区编造失效**（WeiKang 表无冷曲线，其"自洽线"在 Up≈1 km/s 给出
3.1 Mbar 物理错误）——交叉参照失效段的判读方法记入本节。
T300 预热吞没。

### cBNHub（EOS_hub 邢展彬 FP 表，ρ0=3.45，2026-08-17）

6 档（30–150 eV，T 上限 1.6 keV 限制高档），可用 5 档 60 点（高置信 57）。
三重判据过（等温线 +20~+39%——极硬固体冷压主导但确有加热；剖面间断清晰）。
**模拟 vs 表自洽 Hugoniot dUs +0.5~+1.3%**（一致性判据，极好）。
**vs kang2025 理论线**（IM_tool cBN_rho3.40/3.42/3.44.txt）域内 dUs 中位
+14.7~+16.1%（三条一致）——表比 kang2025 参考硬 ~15%，模型间差异；
P-ρ 面同 ρ 下 P 高 ~66%（不可比平面）。
教训（数据处理）：xlsx 参考曲线常含 (0,0) 锚点行与高压缩噪声段
（P 跳 1e4 GPa 级），**必须过滤 comp>1 且 P 有效段**再转参考线
（张帅线转换已固化此过滤，留 reference_curves 备查）。

### hBNFEOS（FEOS 重算 hBN.feos 主表，ρ0=2.04，2026-08-18）

- 新规约首例：FEOS 迁移一律从 `.feos` 主表 + showeos 生成 `.hug` 源参考线
  （已沉淀 multi-material-migration skill）。
- **dt 塌缩陷阱**（pitfall degenerate-cold-electron-dttevar-collapse）：
  6 档全部在波后某时刻 "var fail" 死循环；打桩定位为冷简并电子 Te 底板
  离散跳变（dt 无关 ~27×）撞 dttevar=0.5 限幅。修复：dttevar/dttivar=1e12。
- 可用 4 档（50–150）48 点；**主判据 vs showeos .hug 源 RH 线：
  dUs 中位 +0.77%，46/48 ≤±3%**；vs 表自洽 +0.35%；等温线/剖面间断 ✅。
- T200 弱档（4 记录）、T300 预热吞没。

### CHHub（EOS_hub SESAME 7592 + LANL C1H1 30 群，ρ0=1.044，2026-08-18）

- **配对教训（AlHub 规则的边界）**：Garching"文件名指槽位"规则仅当存在
  elec/ieos 成对文件时适用。本目录唯一 e/i 候选 `7592.ieos.multi` 实为
  **TOTAL 总表**（与 `7592_3eos.multi` TOTAL 子表逐值一致 1e-7）——按名配
  ieos 会错；走 split_ieos_table.py 正规拆分（同 LiFHub）。
- 可用 4 档（50–150 eV）48 点；**T200/T300 预热吞没**（0 gate-A 记录），
  与 CH(T150)/LiFHub(T300)/PSFlash 同族行为。
- 三重判据：等温线 ✅（P₁ 高出初温等温线 5–6 量级）；剖面间断 ✅；
  源对比 ✅（vs 表自洽中位 **+0.1%**，46/48 ≤±3%）。
- 理论线：LiuXing PS A.3 PBE dUs 29/48 ≤±3%（中位 −1.1% 或 +0.4%，插值
  口径）；SESAME 7592 线 +10.2%——**7592 系多孔 CH 非同一初态**，与库内
  Multi_BACK CH 表的 +9.1% 同特征，属预期非缺陷。
- LANL 不透明度群边界为**线性 eV**（1,10,50,100…），勿按 log10 解析。

### AlHub（EOS_hub Garching 3717 族，ρ0=2.7，2026-08-17 定版）

5 档（50–300 eV）×12 点 = 60 点（高置信 56）三重判据全过；
**Us-Up 对四条理论线 dUs 中位 +2.6~+4.2%**（FEOS/3717/3720/Celliers），
与 stock Al（≤1%）同量级，合格。

**重要教训（配对方式）**：Garching 族文件名（elec.multi/ieos.multi）指
MULTI 的 eeos/ieos **槽位**，不指 SESAME 表号/物理分量。我曾按"表号=
分量"重配（eeos=i304+ieos=elec.multi），结果 Hugoniot 对线 −11% 且表级
RH 无有效解，一度误判为版本差异（已推翻，用户纠正）。**判定实验**：
两种配对各算表级 Hugoniot 对理论线——按名配对 +1.6~+2.8%，按表号配对无解。
后续迁移 Garching 族 e/i 对一律按文件名配槽位。

### 不能校验的情况（记录在案）

- **SiO2wk12**（WeiKang DFT 表）：电子表 T 上限 13.5 eV，辐射驱动下烧蚀区
  出表、无激波——Hugoniot 方法不可用（数据限制，算例现场保留）；
- **Silica**（Multi_BACK，ρ0=2.204）：熔石英玻璃，与 α-石英（2.65）理论线
  初始密度不同，不能直接对比（已用表自洽线判据完成校验）。

## 六、推广到其他材料的流程

1. `make_hugoniot_cases.py <X> <rho0> 1e-2 50,100`（trad 按材料调整；
   低 Z/气体材料要重新评估预热；`MAT_TABLES` 字典需先补该材料表配置；
   **注意表 T 范围是否覆盖烧蚀区温度**，否则会出表无激波）
2. 运行 → `extract_hugoniot.py` 看门禁剔除构成与残差分布
3. `hugoniot_point_profiles.py` 出逐点溯源图（人工抽查取样逻辑）
4. `hugoniot_report.py` 汇总出图（理论线在 `THEORY_TXT` 登记后自动叠加，
   误差模型在 `ERR_MODELS` 登记后自动画带）
5. 与用户/文献理论曲线对比，记录偏差到材料清单

### 无独立理论线的材料：表自洽 Hugoniot 判据

`compute_table_hugoniot.py <eeos> <ieos> <rho0> <T0_eV> <eta_max>`：
由材料自己的 eeos+ieos 表反解 RH 能量方程得主 Hugoniot 参考线
（ρ1/T/P/Us/Up）。与模拟提取点对比可验证**冲击物理实现与表插值一致性**
（不能证明表的物理正确性，不是独立理论验证）。在 `hugoniot_report.py`
的 `SELF_HUG` 登记后以灰虚线自动叠加并落盘 `plot_data/self_hugoniot_<X>.csv`。
适用：我们库中大多数无公开 Hugoniot 数据的迁移材料（首例：Quartz 2.204）。

## 六、推广到其他材料的流程

1. `make_hugoniot_cases.py <X> <rho0> 1e-2 50,100`（trad 按材料调整；
   低 Z/气体材料要重新评估预热；`MAT_TABLES` 字典需先补该材料表配置）
2. 运行 → `extract_hugoniot.py` 看门禁剔除构成与残差分布
3. `hugoniot_point_profiles.py` 出逐点溯源图（人工抽查取样逻辑）
4. `hugoniot_report.py` 汇总出图（理论线在 `THEORY_TXT` 登记后自动叠加）
5. 与用户/文献理论曲线对比，记录偏差到材料清单

## 2026-08-20 批量补验（库内 47+3 种全覆盖）

此前 20 种之外的全部六表材料一次性补齐二轮（hugoniot_T50/100/200/300，
quiet start 标准配置；MAT_TABLES/SELF_HUG 配置自动解析自各材料 XCheck data.in）。
结果与排障模式：

- **贴线良好**：41 种有采信点，33 种 dUs 中位 |med|≤1%（vs 表自洽线）。
- **inegpre=1 修 tridia 奇异**（冷端负 Pe）：CD2/Cliquid/Cphenolic/D-T50。
- **tempmin=0.02 修 tridia/奇异**（opc 低温外推）：CH2_wk/H/PE/Mylar。
- **dttevar/dttivar=1e12 修 dt 塌缩**（nexit 耗尽、dt→1e-16，同
  degenerate-cold-electron-dttevar-collapse pitfall）：D/PU/Ni/H-T50/T100。
- **方法不可用（门禁 A 全剔=预热膨胀吞没波前，同 PSFlash 机理）**：
  H/He/H_wk；表 ρ 域不含初态：CH2_wk(0.954 vs 1.91-9.6)/Fe_wk(7.874 vs
  11.8-66.7)/Pb_wk(算例外推 CAVEAT)。
- **异常待查**：N/O 首步非确定性 NaN 段错误（见
  `agent/pitfalls/n-o-firststep-nan-segfault.md`，非源码回归）；
  Air tridia 奇异且 inegpre/tempmin 无效；Xe dUs 中位 +2.4% 偏高；
  Be_wk −38%（源 19 点定性参考级）；SiO2wk14 −2.9%（已知 CAVEAT）。

批量脚本模式：`xargs -P 24` 并行 RUN + 门禁提取 + `hugoniot_report.py`
逐材料汇总；dUs 统计脚本见本节（对 plot_data/self_hugoniot_*.csv 插值）。

## 2026-08-30 BN 族换新表（work/zhanbin 邢展彬修正版）

用户指示以四张新表为准（`work/zhanbin/{hbn,cbn}{ele,ion}FPhighrou_roude`）：
hBNHub 同槽位换表（id 不变）、cBNHub 新增（id 21531304/305，ρ0=3.45）。
旧表/旧产物归档 `tables/_superseded_zhanbin20260830/` 与
`validation_cases/hBNHub/superseded_oldtable_20260830/`（永久保留）。

**换表前后差异定位（入库前必做）**：离子表逐值未变；电子表修正**全部在
ρ≲3.5 低密度区**（ρ<2 相对差中位 456% → 3–3.5 差 6% → **ρ>3.5 为 0**），
e0 仅低区平移；张力平台 −0.104→−0.165 Mbar。因此冲击 Hugoniot（采样
ρ>3.5）不受影响：hBN 自洽线 @2.04 vs ZhangHuan 旧 +2.69% → 新 +3.17%。

**两相共用高压缩分支**：cbn 与 hbn 新表离子表完全相同、电子表 ρ>3.5
完全相同——cBN/hBN 之别只由低密度冷区实现（高压缩冲击态物理上两相趋同，
邢表显式如此构造）。推论：cBNHub @3.45 自洽线与旧表（hBN 数据）@3.45
几乎重合（<0.1%）；引用对比必须知道此结构。

**quiet start 二轮结果**（12 档一次全过，inegpre=1 + dttevar=1e12，无修复）：

| 材料 | 点数/覆盖 | vs 表自洽 | vs 理论线 |
|---|---|---|---|
| hBNHub @2.04 | 82 点（T50–150），P 0.53–24.3 Mbar | **−0.20% 中位**（RH≤1% 子集 +0.26%） | ZhangHuan 同源 +2.48%；FEOS −3.15% |
| cBNHub @3.45 | 116 点（T50–200），P 0.72–61.3 Mbar | **−0.15% 中位**（RH≤1% 子集 +0.46%） | kang3.44 +8.9% / kang3.40 +10.5% / ZhangShuai +8.4% |

- hBN T200/300、cBN T300 提取失败：quiet start 下高档前驱吞没波前
  （可用记录 2/0/0）——方法极限非表问题；hBN 覆盖 P≤24 Mbar 已足。
- **cBN 偏硬 +8~10% 是表 vs 文献的固有分歧**（kang↔ZhangShuai 互差仅
  ~2%）：分段 Up<3 +2~7%、Up 7–12 最大 +15~17%、高 Up 收敛 +9%。
  模拟（116 点）与表自洽线分析一致 → 程序忠实实现表，偏硬属表数据本身，
  **待用户裁定**（若 kang 与邢展彬确同源，值得向提供方核实）。
- 新参考线：ZhangShuai cBN 3.45 P-CR（PRB 99.165103 同目录 xlsx）→
  `validation_cases/cBNHub/zhangshuai_prho_345.csv`（load_theory_csv_prho
  口径，P0=0 换算）。
