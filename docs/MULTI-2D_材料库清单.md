# MULTI-2D.2026.3 材料库清单

> 当前项目可用材料数据的总清单（随迁移工作持续更新）。
> 格式规范见《MULTI-2D_材料库迁移指南.md》；验收流程见《材料迁移验证规范.md》。
> 最后更新：2026-11-19（新增 WaterSES 备选：Mancelli SESAME 直接导出表，见 §1.1 水条目与验收记录；此前 2026-08-14 Quartz↔Silica 更名纠正见 §〇a）

## 〇a、2026-08-14 Quartz↔Silica 更名（重要）

Multi_BACK 原始命名把两种 SiO2 弄反了，本库继承了这个错误，现已纠正：

| 现名（正确） | 密度 | 改名前 | 含义 |
|---|---|---|---|
| **Quartz** | 2.65 | Silica | α-石英 |
| **Silica** | 2.204 | Quartz | 熔石英玻璃（fused silica） |
| **QuartzFEOS** | 2.65 | SilicaFEOS | FEOS α-石英（mat 7387） |
| **SilicaFEOS** | 2.204 | QuartzFEOS | FEOS 熔石英（mat 7386） |

涉及的表文件、2D mat 目录、材料函数、validation_cases 目录、本文档全部
同步更名（MODINFO 与各 `材料表信息.md` 留有改名注记）。
**注意**：`cases/preheat/CH-Al-SiO2_*` 算例注释写 "alpha-quartz" 且 r0=2.65，
但一直实际使用 2.204 表——为不改变基线物理，该算例已重指到同字节的
Silica_* 表（内容不变）；如需修正为真 α-石英表请改用 `tables/Quartz_eos_*`
并重跑（基线会变）。

## 〇、2026-08-13 EOS 能量轴 ×1000 修复（重要）

**病因**：2026-08-10 批量迁移时，hyades→EOS-tools 手工构造链把能量轴放大
×1000（erg/g→J/g 应为 ×1e-7，误用 J/kg 的 ×1e-4；与当日压力单位事故同批）。
压力列转换正确，故**流体/密度/激波走时一直是对的，但温度响应不可用**
（压缩后能量低于表冷能 → T 钳 0；能量守恒查不出此错）。机制详见
`agent/pitfalls/migrated-eos-energy-scale-1000x.md`。

**修复**：用 EOS-tools 官方链（已补尾部零填充/浮点 Z 容差/分数 Z 支持三个
补丁，见 `EOS-tools/PATCHES_2026-08-13_hyades_reader.md`）从 hyades 源表重转，
电子通道 + 理想离子（`table_role='electron', allow_ideal_ion=True`），
批量脚本 `work/eos_opacity_tools/reconvert_hyades_batch.py`。
**逐张验收**：check_multi_file 通过；PdV 热力学一致性 0.62–1.08；
源表绝对值抽查（1/10/100 eV）多数 <1.4%。旧表备份 `tables/_bak_x1000_20260813/`。

**波及 41 种（已全部重转安装）**：§1.1 的 H/He/Li/N/O/Ne/Mg/Ar/V/Ni/Zn/Kr/Mo/Ag/
Xe/Gd/Ta/Pb/U/D 与 §1.2 全部 hyades 族（Glass/Quartz/Silica/Al2O3/WC/CD2/LiD/LiH/
Diamond/Cliquid/Cphenolic/SS/Sn/PE/PS/PU/Parylene/Mylar/Water/Air/Eu）。
网格列已更新为重转后值。**未受影响**：Fe/Cu/W（MPQ i301 路径）、Si（SI.INV）、
CH/DD（CELIA）、Ti（SNOP）、Be、全部 _wk 系、自带老表（Al/Carbon/DT/CPC88）。

**Check 算例已重跑两轮**（脚本 `rerun_fixed_cases.sh`；修复前产物归档
`work/validation_cases_prefix_20260813.tar.gz`）：第一轮重转后；**第二轮在 1D eeos
约定修正后**（见下"2D 侧 + 1D eeos 约定修正"）。41 种全部正常终止，40 种能量误差
<1e-4（多数 ≪1e-10），仅 Cliquid（3.2e-4）超阈。第二轮关键变化：D 由 2.2e-11 升至
8.5e-7（Z=1 离子贡献现在被正确扣除，误差上升但仍远低于阈值）、Air 由 7.5e-5 升至
9.4e-5（仍过）。例外与遗留：

| 材料 | 状况 | 说明 |
|---|---|---|
| **Ta** | 源表 eos_271 本身 T≤56 eV | TaCheck 已降为 40 eV 驱动，通过（7.5e-15）。**旧 100 eV Check 的"通过"是 ×1000 假象**（真实越界崩溃）。高温用途需换宽区 EOS 源 |
| **H、D** | 源表在 ρ≥544/1088 g/cc（≥6×10³ρ0）有 E(T) 折叠 | 已裁去不可达超高密度行（保留到 ~3000×ρ0），T 覆盖恢复至 31.9 keV；Check 通过（H 2.8e-9 / D 8.5e-7） |
| **Parylene** | 源表在 ρ≥7100 g/cc 有折叠 | 同上裁断，T 覆盖 100 keV；Check 通过（1.5e-14） |
| **Li** | 低能角 1 eV 点偏差 14–18%（10/100 eV 处 <1%） | 网格拐角插值误差，预热量级（≫eV）用途可接受 |
| **Glass** | 1 eV 点偏差 4.5%；另源表 T≤116 eV（§四-2） | 同上 |
| **Cphenolic** | 0.82 eV 点偏差 2.3% | 同上 |
| **Cliquid** | 修复后完成全程，能量误差 3.2e-4 超 1e-4 阈值 | 已知密度下限（0.23 g/cc）问题，维持 ⚠ |
| **Air** | 修复后误差 9.4e-5 | 1e-4 阈值下通过（旧值 9.1e-11 系 ×1000 膨胀下的假性微小） |
| **Diamond** | 修复后 Check 通过（1.6e-13） | ⚠ 已解除（用户确认） |

**2D 侧 + 1D eeos 约定修正（2026-08-13 完成）**：
1. **2D 总表**：`r94/mat_*-1.0/<X>_eos`（2D 运行时按路径经 `Mat2013_LoadIEOS` 读表，
   替换内容无需重编译）此前仍是 ×1000 病态（PdV≈1000）。脚本
   `work/eos_opacity_tools/rebuild_eos_2d1d.py` 把权威源
   `work/eos_rebuild_20260813/<X>_electron.multi`（reconvert 修正总量的持久副本，
   含 H/D/Parylene 折叠裁断）安装为 2D 总表（marker=1.0），旧表备份
   `mat_<X>-1.0/_bak_x1000/`。修复后 PdV 全部 0.6–1.1，check_multi_file 通过。
2. **1D eeos 约定回退修正**：reconvert 把 hyades **总量**写进电子槽（`hyades.py`
   table_role='electron' 时 `pe_mpa=raw_pressure`），而原始迁移走 `split_ieos_table`
   产出 total−ion。故之前安装的 `tables/<X>_eos_e` 实为总量（对 H/D 使 Te 偏低约 2×，
   金属 <5%；2D 不受影响，运行时 `Mat2013_EleTab` 自拆）。现对同一权威总量跑
   `split_ieos_table` 重派 `_eos_e`=total−ion / `_eos_i`=理想离子（id 沿用 `elem_ids(Z)`，
   data.in 无需改），旧表备份 `tables/_bak_totalconv_20260813/`。eeos==split(total) 复核到 5e-9。
3. **2D 迁移材料启用**：`Material_mig.r` 与 `Material.r` 在 `Material{CH,Cu,Fe,W}0`
   四处全局符号冲突。`gen_material_functions.py` 加 `SKIP_COLLISION` 跳过这 4 个
   （保留 Material.r 原生版；它们用非病态的 CHOQG/MPQEOS 源），重生成 52 个函数，
   `x.2.compile Material_mig.r` 增量重编 lib.a。链接测试同时引用 MaterialAl（原始）
   + MaterialTa（迁移）成功生成 multi2d，无冲突。**此前用到受影响 1D 表的算例
   （preheat CH-Al-SiO2_rad140-60、ICF3D_CH 基准）需重跑才能得到正确温度。**

## 一、快速总览

### 1.1 全套材料（2D EOS + 1D 电子/离子 EOS + 多群不透明度 + Zeff，均通过 1D 验证算例）

| 材料 | 2D 模块 | EOS 网格 | 不透明度(群数) | Zeff | 验证算例 |
|---|---|---|---|---|---|
| **H** 氢 | mat_H-1.0 | 46×128 | Thermos 82 群 | ✔ | HCheck |
| **He** 氦 | mat_He-1.0 | 37×128 | 108 群 | ✔ | HeCheck |
| **Li** 锂 | mat_Li-1.0 | 91×128 | 74 群 | ✔ | LiCheck |
| **N** 氮 | mat_N-1.0 | 63×128 | 124 群 | ✔ | NCheck |
| **O** 氧 | mat_O-1.0 | 63×128 | 31 群 | ✔ | OCheck |
| **Ne** 氖 | mat_Ne-1.0 | 100×128 | 77 群（已删退化子表） | ✔ | NeCheck |
| **Mg** 镁 | mat_Mg-1.0 | 68×128 | 105 群 | ✔ | MgCheck |
| **Si** 硅 | mat_Si-1.0 | 127×100 | 110 群 | ✔ | SiCheck |
| **Ar** 氩 | mat_Ar-1.0 | 66×128 | 121 群 | ✔ | ArCheck |
| **V** 钒 | mat_V-1.0 | 67×128 | 106 群 | ✔ | VCheck |
| **Fe** 铁 | mat_2019 | 77×100 | 35 群 | ✔ | FeCheck |
| **Ni** 镍 | mat_Ni-1.0 | 100×128 | 109 群 | ✔ | NiCheck |
| **Cu** 铜 | mat_2019 | 71×100 | 129 群 | ✔ | CuCheck |
| **Zn** 锌 | mat_Zn-1.0 | 67×128 | 57 群 | ✔ | ZnCheck |
| **Kr** 氪 | mat_Kr-1.0 | 45×128 | 158 群 | ✔ | KrCheck（气体密度算例） |
| **Mo** 钼 | mat_Mo-1.0 | 100×128 | 25 群 | ✔ | MoCheck |
| **Ag** 银 | mat_Ag-1.0 | 68×128 | 40 群 | ✔ | AgCheck |
| **Xe** 氙 | mat_Xe-1.0 | 66×128 | 60 群 | ✔ | XeCheck |
| **Gd** 钆 | mat_Gd-1.0 | 69×128 | 124 群 | ✔ | GdCheck |
| **Ta** 钽 | mat_Ta-1.0 | 48×128 | 21 群 | ✔ | TaCheck |
| **W** 钨 | mat_2019 | 71×100 | 24 群 | ✔ | WCheck |
| **Pb** 铅 | mat_Pb-1.0 | 100×128 | 35 群 | ✔ | PbCheck |
| **U** 铀 | mat_U-1.0 | 100×128 | 20 群 | ✔ | UCheck |
| **Ti** 钛 | mat_Ti-1.0 | 45×100 | SNOP 30 群 | ✔ | TiCheck（首例，用户已人工确认 ✅） |
| **DD** 氘氘 | mat_DD-1.0 | 50×25 | CELIA 20 群 | ✔ | DDCheck |
| **D** 氘 | mat_D-1.0 | 46×128 | CELIA 20 群（借纯氘表） | ✔ | DCheck |
| **CH** 塑料 | mat_CH-1.0 | 101×100 | CELIA 20 群（借碳表） | ✔ | CHCheck |

已有全套（2026.3 自带）：**DT、C、Al、Be、Au**（tables/ 下 DT、Carbon、Al、CPC88、Be20keV、Mix20keV 等）。

### 1.2 单群不透明度材料（hyades opc 平均表，2D/1D 均可用；1D 验证已跑）

> 2026-08-11 补齐：opc 库按 Multi_BACK 原生映射（含借用规则）转换为 sgo 单群表
> （`tables/X_OPC.ROSS/.PLANCK`），1D 以单群模式验证。

| 材料 | EOS 网格 | opc 源 | 材料 | EOS 网格 | opc 源 |
|---|---|---|---|---|---|
| Glass 玻璃 | 43×256 | 1022 | CD2 氘代聚乙烯 | 64×128 | 1344（借C） |
| Quartz 石英(α-石英 2.65) | 72×128 | 1022 | Diamond 金刚石 ⚠ | 93×128 | 1344（借C） |
| Silica 熔石英玻璃(2.204) | 74×128 | 1022 | Cliquid 液态碳 ⚠ | 48×128 | 1344（借C） |
| PE 聚乙烯 | 64×128 | 1031 | Cphenolic 酚醛 | 55×128 | 1344（借C） |
| PS 聚苯乙烯 | 72×128 | 1032 | LiD 氘化锂 | 93×128 | 1071（借Li） |
| PU 聚氨酯 | 100×512 | 1033 | LiH 氢化锂 | 42×512 | 1071（借Li） |
| Parylene | 67×128 | 1035 | SS 不锈钢 | 72×128 | 1181（借Fe） |
| Mylar | 72×128 | 1036 | Water 水（2026-08-14 Hugoniot ✅） | 80×128 | 1311 |
| Al2O3 氧化铝 | 67×128 | 1161 | Air 空气 | 21×128 | 1301 |
| WC 碳化钨 | 99×128 | 1121（借W） | Sn 锡 | 67×128 | 1401 |
| Eu 铕 | 69×128 | 1461 | | | |

⚠ 标记（2026-08-13 修订）：**Cliquid** 维持 ⚠（修复后能跑完全程但能量误差 3.2e-4 超阈值，源表密度下限 0.23 g/cc 问题）；**Diamond** ⚠ 已解除（修复后 Check 通过 4.8e-13，用户确认）。

### 1.2b WeiKang 论文提取系列（_wk 后缀，独立 MID 不覆盖已有材料）

> 来源：`$MULTI_LIBS/newmulti/weikang状态方程表_汇总/`（北大 5 本博士论文 DFT/FPMD 表）。
> 评估详见《WeiKang状态方程表_评估.md》。2D 函数在 `Material_weikang.r`（13 个）。

| 材料 | 网格 | 覆盖 | 状态 | 说明 |
|---|---|---|---|---|
| **H_wk** 氢（刘兴 FPMD） | 20×128 | ρ0.002–1000, T1–981 eV* | ✅ H_wkCheck 9.0e-11 | 宽区高质量数据；*自适应网格截断了 5000 eV 高温尾 |
| **C_wk** 碳（刘兴 DFT） | 96×512 | ρ0.35–100, T0.026–1393 eV | ⚠ **冻结（2026-08-25 重建尝试：数据层通过、运行时未解）** | 用 Sheet1 修正数据（EOS_carbon_corrected.csv）重建：check_multi_file ✓、源点复现 ✓、自洽 Hugoniot 全单调且弱激波段与 Diamond 库表差 <1% ✓；但算例 dt 塌缩——半表判决矩阵**精确定位祸首为重建电子表×隐式辐射求解的相互作用**（CELIA/ZEFF/离子表/初温/角落取值全部洗清），九次修复未解（完整档案 `work/cwk_rebuild_20260825/DEBUG_LOG.md`，最小复现件 probe3）。**待 S1-S9 专项**（三条路径：求解器联合调试 / 向刘兴要原生长网格表或 .feos 源 / Diamond 骨架换芯）；生产用 MaterialC |
| **C8H8_wk** 聚苯乙烯 | 10×128 | ρ1.05–12.6 | ⚠ 1D 验证未通过 | 同上；生产用 MaterialCHOQG/PS |
| **C9H10_wk** 聚α-甲基苯乙烯 | 9×128 | ρ1.07–10.7, T1–1000 eV | ✔ EOS-only（新材料） | 无不透明度源 |
| **CH2_wk** 聚乙烯 | 8×128 | ρ1.91–9.6 | ✅ CH2_wkCheck 5.5e-12 | 收编 multi格式 半成品（修头/CRLF，核对源表 0.03% 内） |
| **Fe_wk** 铁 | 8×128 | ρ11.8–66.7（仅压缩态） | ✅ Fe_wkCheck 3.3e-15 | 同上收编；低密度区勿用 |
| **Be_wk** 铍（高畅 ext-FPMD） | 5×128 | ρ0.1–1000 | ✅ Be_wkCheck 1.8e-14 | 仅 19 源点，定性参考级 |
| **Si_wk** 硅（高畅 PBE） | 7×256 | ρ2.33–18.6 | ✅ Si_wkCheck 1.3e-15 | 4 泛函中取 PBE |
| **BN_wk** 氮化硼（杨雨桐） | 6×128 | ρ4.57–34.3 | ✔ EOS-only（**新材料**） | 6ρ×11T |
| **Pb_wk** 铅（杨雨桐） | 5×128 | ρ28.4–73.7（仅压缩态） | ⚠ 算例外推冒烟 | Pb_wkCheck 在表外运行（r0=11.34<28.36），仅格式冒烟意义；表内数据合格（3.7% 内） |
| **LiF_wk** 氟化锂（张肖涵） | 12×128 | ρ2.08–15.8, T4.3–1367 eV | ✅ 三轮复核后 ACCEPT（**新材料**） | 仅取 A.2 宽行（单一参考系，无合并无填充）；全量 76 源点对照 ≤0.77%；低温（<4.3 eV）与 ρ<2 区不在表内；EOS-only（无不透明度） |
| **SiO2wk12**（Si12 赝势） | 9×128 | ρ2.65–13.2, T0.5–10 eV* | ✅ SiO2wk12Check 1.9e-13 | 低温段；*T 上限实为 10 eV（申报时高估）；**Hugoniot 校验不可用**（辐射驱动烧蚀区 T≫13.5 eV 电子表上限，出表无激波，2026-08-13 记录在案） |
| **SiO2wk14**（Si14 赝势） | 14×512 | ρ2.65–13.2, T20–1137 eV* | ⚠ 算例误差 1.05e-5 | 高温段；初温需在表内；50–500 eV 陡段 P 系统性偏高 8–13%（源数据特性） |

### 1.2c FEOS 模型计算系列（2026-08-13/14，FEOS 后缀，独立 MID 不覆盖已有材料）

> 来源：`$MULTI_LIBS/FEOS/FEOS`（Thomas-Fermi + SoftSphere + Maxwell 模型计算，
> `./feos <mat>` 生成 `.feos`）。
> **1D 表经 EOS-tools 转换**（`eos_convert.py --from feos --to multi`，192×512 细网格）；
> 2D 总表用 FEOS 自带 feos2r94 + 两步修复（布局转置、能量 ÷100，
> 见 `agent/pitfalls/feos-converter-layout-energyunit.md`；上游代码未动，
> 其 hBN/Al/H2O 产物带同 bug 勿直接用）。
> 2D 函数在 `Material_feos.r`（QuartzFEOS/SilicaFEOS/AlFEOS 3 个 + WaterFEOS/WaterAQUA）；
> 不透明度：SiO2 族/水借 opc 1022/1311 拟合，**AlFEOS 借自带 tables/Al 的 SNOP 20 群（全套多群）**。

| 材料 | 网格 | 覆盖 | 状态 | 说明 |
|---|---|---|---|---|
| **QuartzFEOS**（α-石英 2.65，FEOS mat 7387） | 192×512 | 宽区 | ✅ **完全迁移（2026-08-17 人工确认）——石英族首选，优于自带 Quartz** | 反解 Hugoniot 对 FEOS 官方 .hug：**P≤3.5%、Us≤1.3%**；Hugoniot 算例 42/48 点 ≤1% 全程贴线（曾现 T≥100 双温振荡，dttevar/dttivar=0.5 限幅消除，见陷阱库），见 `validation_cases/QuartzFEOS/材料表信息.md` |
| **SilicaFEOS**（熔石英 2.204，FEOS mat 7386） | 192×512 | 宽区 | ✅ 自洽对照通过；✅ Hugoniot 全档压线 | 表自洽 Hugoniot 线对照通过；Hugoniot 算例 41/48 点 ≤1% 全档压自洽线（振荡已限幅消除）；表 id 73861000 |
| **AlFEOS**（铝 2.7，FEOS mat 3717，2026-08-14） | 电子 192×463（去重）/ 理想离子 192×495 / 2D 192×136 | 宽区 | ✅ 完全迁移（2026-08-17 人工确认） | **系列首个全套多群**：不透明度/Zeff 借自带 tables/Al（SNOP 20 群，id 10003000/10004000/10002000），eeos/ieos id 13000304/305，2D 表 id 37171000；离子表排障后换理想气体（FEOS 离子低ρ平台，`agent/pitfalls/eos-tools-dup-rows-ideal-ion.md`）；模拟点 vs 表自洽 Hugoniot Us P50=0.48%，表自洽线 vs FEOS .hug P50=2.42%/max 3.38%，5 档 60 点门禁全过（`validation_cases/AlFEOS/hugoniot_summary/`、`材料表信息.md`） |
| **WaterFEOS**（水 1.0，FEOS mat 7100/SESAME 7154，2026-08-14） | 192×512（e/i）/ 2D 192×136 | 宽区（T≤1e5 eV） | ✅ 完全迁移（2026-08-17 人工确认可用；水的高温/ICF 工况首选） | eeos/ieos id 3330304/305（对拍 data.txt 真值 P≤1.6%），2D 表 id 71001000（P≤0.6%）；Hugoniot T75/100/150 三档 67 点 RH≤1.2%、**Us 对 FEOS 源均值 +0.86%（63/67 ≤±3%）**，三重判据复检过（等温线污染✅ 剖面间断✅ 源对比✅），能量误差 ≤4.2e-11；算例需 **inegpre=1 + 算例内 tempmin=0.02 补丁**（冷端负 Pe + opc 低温外推奇异，`agent/pitfalls/water-cold-pe-and-opc-lowt-singular.md`）；T50 弱驱动提取不可用已搁置；不透明度借 Water opc 1311（`validation_cases/WaterFEOS/材料表信息.md`） |
| **WaterSES**（水 1.0，SESAME 7150/7153/7154 直接导出，Mancelli/LPB2021，2026-11-19） | 1D e/i 三对：80×44、68×37、66×37 | 宽区（7150 多相 ρ≤400；7153 ρ≤2e4；7154 ρ≤5e3 g/cc） | ✅ **正式备选（2026-11-19 用户裁定；基准仍 WaterHub=highrou）** | 表源 LPB2021 论文（DOI 10.1155/2021/4141522）作者方 MULTI 布局导出（非标头+16 字符定宽，重封装标准头 id 11111）；`tables/WSES{7150,7153,7154}_eos_{e,i}`；拆分 A=6.005；未走 S1-S9 完整门禁（以 12 例终解交叉验证替代：**7154≈highrou 三发 RMS 差 ≤0.03**，7150/7153 较软 t1 提前 0.13-0.4 ns；全模型水窗 P +3-4%、TE +20-40%（分子振动能入电子表）、状态仍超离子；与 WaterFEOS 同源 SESAME 7154 互证；验证细节 `cases/H2O_multi_layer/water_eos/README.md`、FEEDBACK §R4.33） |

### 1.2g FEOS+IONMIX 新算系列（2026-11-13，Quartz_SiC_CaO 战役，CaO/SiC 库内首例）

> 来源：本机 FEOS（`$MULTI_LIBS/FEOS/FEOS`，TF+SoftSphere+Maxwell，合成材料号
> 2011/2012，`EOS-Data/{CaO,SiC}/`）算 EOS；本机 IONMIX（MacFarlane ABJT v1，
> 化合物按原子数分解：CaO=Ca0.5+O0.5（isw(1)=1+atom20/atom08 NIST）、SiC=Si0.5+C0.5）
> 算 6 群不透明度（0.1–1e5 eV）→ cn4 → EOS-tools 单群折叠灰体（Ir 先例）。
> 1D 表经 EOS-tools API（convert+postprocess，Ir 同款）；Zeff 由 showeos 模式 6
> 逐点查平均电荷态（51×51）。**仅 1D 库**（无 2D 总表/材料函数，Ir300 先例）；
> 工作目录 `work/cao_sic_migration/`，验收 `validation_cases/{CaO,SiC}/`。

| 材料 | 网格 | 覆盖 | 状态 | 说明 |
|---|---|---|---|---|
| **CaOFEOS**（CaO 3.35，FEOS mat 2011） | e/i 185×512 + ZEFF 51×51 + 灰体 OPC 10×20 | 宽区 | ⏳ 待人工确认（2026-11-13 机器验收） | eeos/ieos id 20110304/20110305、ZEFF 20112017、CaOIONMIX.PLANCK/ROSS id 1081；Hugoniot Us≈5.9+1.29Up（Cs 对 B0=114 GPa 推算 5.83，s 对 MgO 类似物 1.24，TF 无 B1→B2 相变拐点为已知局限）；Check 误差 1.3e-7 |
| **SiCFEOS**（SiC 3.21，FEOS mat 2012） | e/i 185×512 + ZEFF 51×51 + 灰体 OPC 10×20 | 宽区 | ⏳ 待人工确认（2026-11-13 机器验收） | eeos/ieos id 20120304/20120305、ZEFF 20122017、SiCIONMIX.PLANCK/ROSS id 1082；Hugoniot Us≈8.4+1.17Up（文献 Marsh/LASL ≈8.0+1.2Up，Cs +5%）；Check 误差 3.8e-14 |

### 1.2d 外部数据表系列（AQUA）

> 来源：AQUA 水 EOS 合集（Haldemann et al. 2020，`aqua_eos_rhot_v1_0.dat`）。
> **EOS-tools 新增 AQUA 读取器转换**（`eoslib/formats/aqua.py`，
> 见 EOS-tools `PATCHES_2026-08-14_aqua_reader.md`）；总量源 → 2D 单张总表；
> 1D 双温表经 split_ieos_table.py 派生（EleTab+理想离子，S4 自洽 0.9999–1.0004）。

| 材料 | 网格 | 覆盖 | 状态 | 说明 |
|---|---|---|---|---|
| **WaterAQUA**（水 1.0，2026-08-14） | 200×512（e/i 全温区 T≥0.0086 eV；裁剪版存 .bak_T025crop）/ 2D 200×512 全温区 | **T≤8.6 eV、ρ≤100 g/cc（行星 EOS，ICF 高温不可用）** | ❌ **人工确认不可用（2026-08-17 用户裁定）**——行星 EOS 温区局限 + 1D 双温低温段拆分失真；产物保留备查，不标完全迁移 | eeos/ieos id 3330304/305，2D 表 id 20201000；`wcheck_T5`（5 eV 浴）能量误差 **5.48e-8 < 1e-6**、热图干净；**Hugoniot 验证走表级三方对比**；⚠ **1D 双温表低温段（≲1 eV）拆分失真**（总量 EOS 用理想气体离子拆分，300 K 处 P 符号反转，`agent/pitfalls/total-eos-ideal-ion-split-cold-condensed.md`）；**2D 总量表准确可用**；算例需 **inegpre=1 + 算例内 tempmin=0.02 补丁**（拆分冷端负 Pe + opc 低温外推奇异）；in-code 冲击算例物理不可行（窄压缩段+弱驱动前驱膨胀，`agent/pitfalls/planetary-eos-hugoniot-infeasible.md`）；不透明度借 Water opc 1311（`validation_cases/WaterAQUA/材料表信息.md`） |

### 1.2e FLASH IONMIX4 系列（2026-08-14，独立 MID 不覆盖已有材料）

> 来源：FLASH LaserSlab 算例的 IONMIX4 EOS+Opacity 合并表
> （`FLASH4.6.2/source/Simulation/SimulationMain/LaserSlab/*.cn4`；
> 与 FLASH4.8 / Sunliang_laser_CH / ICF*_CH 副本 md5 相同）。
> **1D/2D 表均经 EOS-tools 转换**（`eos_convert.py --from ionmix --to multi`）：
> IONMIX4 原生电子/离子分量 → eeos/ieos（不经 EleTab 拆分），原生 6 群不透明度
> + 平均电离度 → PLANCK/ROSS/EPS/ZEFF，2D 总表用 role=total 复合（Pe+Pi/Ee+Ei）。
> **本系列首个且唯一含原生 EPS 发射表**。2D 函数在 `Material_mig.r`（MaterialPSFlash）。

| 材料 | 网格 | 覆盖 | 状态 | 说明 |
|---|---|---|---|---|
| **PSFlash**（聚苯乙烯 ρ0=1.05，FLASH IONMIX4 polystyrene-imx-008，2026-08-14） | 51×31 源 → 1D 31×64（e/i）+ 31×51（z/6 群）+ 2D 31×128 | ρ 1.08e-7–108，T 2 eV–200 keV | ❌ **人工确认不可用（2026-08-17 用户裁定）**——QEOS 冷端近似 + 6 群透明窗（trad≥60 eV 预热吞没）+ Hugoniot 校验方法不可用；产物保留备查，不标完全迁移，CH 工况请用自带 CH | eeos/ieos id 3501304/305，z_id 1，planck/ross/eps id 10013000/10014000/10015000，2D 表 id 35081000；PSFlashCheck 能量误差 5.6e-12（挂 EPS）/ 3.4e-15（不挂）；**Hugoniot 方法校验不可用**（2026-08-14 复检：35–55 eV 全档为辐射介导等温压缩波——点贴 T=2 eV 等温线中位 -1.4~-5.7% 而非自洽 Hugoniot 线；≥60 eV 预热吞没；剖面上无冲击间断，判据与证据见 `hugoniot_T*/profiles_check.png` 与 pitfalls）；验证改依 PSFlashCheck + 源绝对值对照 + Te 剖面与 CHCheck 一致（76–78 vs 77 eV）；**trad≥60 eV 不可用**（6 群在 100–1000 eV 透明 → 预热吞没，`agent/pitfalls/ionmix-preheat-shell-merger.md`）；**ZEFF 表头 type 串改写**（1D 加载器兼容，`agent/pitfalls/eostools-zeff-type-string-1d.md`）；**QEOS 冷端近似**（ρ0 处 P(de=0)≈+0.3 Mbar）；详见 `validation_cases/PSFlash/材料表信息.md` |
| **AlFlash**（铝 ρ0=2.7，FLASH IONMIX4 al-imx-003.cn4，2026-08-14） | 21×25 源 → 1D 25×128（e）/ 25×64（i）+ 25×21（z/6 群）+ 2D 25×128 | ρ 4.48e-7–44.8，T 1 eV–100 keV | ❌ **人工确认不可用（2026-08-17，用户裁定）**——表无冷曲线致 Hugoniot 系统性偏软 ~54%，仅限热等离子体烧蚀场景，不作为可用库材料 | eeos/ieos id 13001304/305，z_id 1，planck/ross/eps id 10023000/10024000/10025000，2D 表 id 130011000；AlFlashCheck 能量误差 1.5e-10（挂 EPS）；**Hugoniot 系统性偏软 ~54%**：直接源 cn4 反解 Hugoniot（绕过转换/提取）证实表无冷曲线（ρ0 处 P(1eV)=0.098 Mbar≈纯离子热压、声速 1.9 vs 真实 5.3 km/s），同工具对 AlFEOS 得 2.4% 证明工具无误，`agent/pitfalls/ionmix-al-no-cold-curve.md`；源绝对值对拍 P50~2e-4、ZEFF 精确；详见 `validation_cases/AlFlash/材料表信息.md` |

### 1.2f EOS_hub / Tables-XuBo 系列（2026-08-17 起，Hub 后缀，独立 MID 不覆盖已有材料）

> 来源：`work/EOS_hub/`（徐博 Tables-XuBo 集合，Garching MULTI 生态原表库，
> 梳理报告见 `work/EOS_hub_梳理报告.md`）。可用性普查：104 文件直接可用、
> ~10 旧方言修复、~25 需转换。转换/拆分一律走 EOS-tools + split_ieos_table
> 正规路径（铁律 6）；不透明度/ZEFF 仅改写 id（数据逐值保真）。

| 材料 | 网格 | 覆盖 | 状态 | 说明 |
|---|---|---|---|---|
| **ParyleneHub**（聚苯乙烯 ρ0=1.29，SESAME 7770 + CEA CENS 40 群，2026-08-17） | 1D 71×37（e/i 拆分）+ 41×41（z/40 群）+ 2D 71×37 | ρ 1.42e-6–2.84e4，T 至 100 keV；群 1–20000 eV | 机器验收 15/16+复验，待人工确认 | eeos/ieos id 77700304/305，planck/ross id 77703000/77704000，z_id 1，2D 表 id 77701000；ParyleneHubCheck 能量误差 **9.4e-14**；Hugoniot 30–125 eV 五档 60 点（高置信 54）：三重判据全过（等温线✅ 剖面✅），**vs 库内 hyades Parylene 表交叉参照 dUs 中位 +0.3%，54/54 ≤±3%**；≥150 eV 预热吞没不可用（算例保留）；详见 `validation_cases/ParyleneHub/材料表信息.md` |

| **LiFHub**（LiF ρ0=2.64，SESAME 7270 三分量拆分 + CEA CENS 40 群，2026-08-17） | 1D 66×37（e/i）+ 41×41（z/40 群）+ 2D 66×37 | T 至 100 keV；群 1–20000 eV | ✅ 完全迁移（2026-08-17 人工确认） | eeos/ieos id 72700304/305，planck/ross id 72703000/72704000，2D 表 id 72701000；LiFHubCheck 能量误差 **1.1e-14**；split 电子表 vs 源原生 ELECRO 加验（高温 <1%）；Hugoniot 30–200 eV 七档 83 点（高置信 66）三重判据全过，**交叉参照 LiF_wk 有效段（Up≥40）dUs −2.4%~+0.6%**（低 Up 段分歧系 LiF_wk 冷区编造失效）；Hawreliak 2023 PRB 理论线（≥150 eV 档 dUs −1.0%~+1.6%）；详见 `validation_cases/LiFHub/材料表信息.md` |
| **hBNHub**（hBN ρ0=2.04，邢展彬 FP 原生 e/i 对 200×500；**2026-08-30 换新表** work/zhanbin 修正版——离子表逐值未变、电子表修正全在 ρ<3.5 低密度区（ρ≥3.5 与旧表逐值一致）、张力平台 −0.104→−0.165 Mbar；旧表归档 `tables/_superseded_zhanbin20260830/`、旧产物归档 `superseded_oldtable_20260830/`；换表后复验：Check 2.0e-14 + Hugoniot（quiet start）4 档 82 点 **vs 表自洽 dUs −0.20%、vs ZhangHuan +2.48%**（与旧表期一致，冲击段不受修正影响）。2026-08-17 入库、2026-08-18 **身份翻案**） | 1D 200×500（e/i 原生对，无拆分） | ρ 0–40（0.02 dex 细网格），T≤1.6 keV | 机器验收（换表后复验），待人工确认 | eeos/ieos id 21521304/305（2152 材料号派生）；**原误判 cBN（ρ0=3.45）经用户质疑翻案为 hBN**：表自洽线 @2.04 与 ZhangHuan 同源 hBN 线 ≤3% 贴合、模拟 36 点 +2.4%、@3.45 反证 +39~54%——误判期产物收纳 `mistaken_cBN_rho3.45/`，"+15% vs kang2025"系 hBN 表当 cBN 用所致（kang 线自身 RH 自洽，含 P₀=−176.2 kbar）；翻案后 @2.04 重验：hBNHubCheck 1.7e-14（inegpre=1，@2.04 张力平台 −0.099 MBar）；Hugoniot 5 档 60 点（质控 58）：**vs 表自洽 dUs +0.46%/max 2.90%，vs ZhangHuan 同源线 +2.39%/4.52%**，vs 用户 FEOS hBN 线 −2.4%（跨模型）；T300 出表、dttevar=1e12 必要；**借 N_Thermos 不透明度（验证用）**、无 2D 函数（e/i de 网格不同待合成）；详见 `validation_cases/hBNHub/材料表信息.md` |
| **cBNHub**（cBN ρ0=3.45，邢展彬 2026-08-30 新 FP 原生 e/i 对 200×500，work/zhanbin 批次——首个原生 FP cBN 表） | 1D 200×500（e/i 原生对，无拆分） | ρ 0–40（0.02 dex 细网格） | 机器验收，待人工确认 | eeos/ieos id 21531304/305（2153 接续 2152 派生）；**与 hBNHub 新表共用 ρ>3.5 数据分支**（离子表完全相同、电子表 ρ>3.5 完全相同，两相之别只在低密度冷区）——@3.45 自洽线与旧表（hBN 数据）几乎重合；quiet start 二轮 5 档 **116 点 vs 表自洽 dUs 中位 −0.15%**（RH≤1% 子集 +0.46%）、P 0.72–61.3 Mbar；**vs kang2025 3.44 +8.9% / 3.40 +10.5%、vs ZhangShuai 3.45（PRB 99.165103）+8.4% 系统偏硬**——两文献线互差仅 ~2%，偏硬为表固有属性（Up 7–12 km/s 段最大 +15~17%，高 Up 收敛 +9%），**待用户裁定**；借 N_Thermos 不透明度（验证用）、无 2D 函数；详见 `validation_cases/cBNHub/材料表信息.md` |
| **hBNFEOS**（hBN ρ0=2.04，用户 FEOS 重算 hBN.feos 主表，2026-08-18） | 1D 54×128/54×64 + z 46×51（showeos 自建）+ 2D 54×96 | T ≤4.6 keV | 机器验收，待人工确认 | eeos/ieos id 77770304/305（EOS-tools --from feos），z id 77772004，2D id 77771000（feos2r94+两步修复，P(2.04,1eV)=0.4379 精确）；**无不透明度**（2D opafun=*，验证借 N_Thermos）；hBNFEOSCheck 4.7e-15；Hugoniot 4 档 48 点，**vs showeos .hug 源线 dUs 中位 +0.77%（46/48 ≤3%）**；dt 塌缩修复（dttevar=1e12，pitfall degenerate-cold-electron-dttevar-collapse）；详见 `validation_cases/hBNFEOS/材料表信息.md`（含 FEOS 冷曲线复核：低压段偏硬系 FEOS 冷曲线压缩支曲率+缺 hBN→纤锌矿相变，非转换问题；**≥14 km/s 与 ZhangHuan <1% 一致，低压段偏硬 30-36%**） |
| **cBNFEOS**（cBN ρ0=3.4，用户 FEOS 重算 cBN.feos 主表 mat 7780，2026-08-18） | 1D 54×512/54×64 + z 46×51（showeos 自建）+ 2D 54×96 | 宽区 T≤86 keV；ρ 3.4e-4–2145（54 点粗网格 ×1.37） | 机器验收，待人工确认 | eeos/ieos id 77800304/305（EOS-tools --from feos，电子能量轴自动加密 512），z id 77802004，2D id 77801000（feos2r94+两步修复，P(3.4,1eV)=0.7424 精确）；**无不透明度**（2D opafun=*，验证借 N_Thermos）；cBNFEOSCheck 2.5e-14；单点对源 ≤0.75%，表自洽线 vs .hug dUs +1.55%（粗 ρ 网格插值残余）；Hugoniot 四档 45 点（T100–200，质控 25 点 vs 表自洽 **dUs 中位 +1.65%/max 3.72%**，T30–75 驱动太弱被预热流吞没、T300 失稳）；dttevar=1e12 必要（同 hBNFEOS pitfall）+ T150 以上 dtmax=5e-12；**2D 表单行写出事故已修复**（重排 2644 行，复验 ✓）；cBN 库内唯一代表（cBNHub 已翻案为 hBNHub）；详见 `validation_cases/cBNFEOS/材料表信息.md` |
| **cBNCpx**（cBN 碳代理 ρ0=3.45：**Diamond 表字节副本仅改 id 与算例 r0**，2026-09-10；导师提议 C/BN 性质类似，立方↔立方同构、密度差 1.9%） | 1D 93×128（e/i，源 Diamond_eos_{e,i} 同网格） | ρ 0.352–352.4，T 至 36.98 keV（装载器口径） | 机器验收，待人工确认 | eeos/ieos id **21541304/305**（除首 token id 外与源逐字节一致，含子 agent 9 字节定位复验）；"仅改初密度"=表数据零改动、ρ0 只在算例 layer 卡；初态 1.9% 拉伸（P0≈−0.075 Mbar，inegpre=1）；借 N_Thermos 不透明度（与 cBNHub 同配置单变量对比）、2D 直接用 mat_Diamond-1.0（数据全同）；cBNCpxCheck 5.6e-15；quiet start 二轮 5 档 **96 点（高置信 26）vs 表自洽 dUs −0.39%（子集 +0.28%）**；**vs ZhangShuai 3.45（同初密度）−2.74%（高置信 −2.87%）、vs kang2025 3.44 +2.91%——落在两文献线（互差 ~2%）之间，显著优于 cBNHub 的 +8~10% 偏硬（交叉比对代理比邢表软 ~9.8%）**；低 Up 段辐射介导偏低同 Diamond 已知；详见 `validation_cases/cBNCpx/材料表信息.md` |
| **hBNCpx**（hBN 碳代理 ρ0=2.04：**Cliquid 表字节副本仅改 id 与算例 r0**，2026-09-10；六方层状↔石墨对应，库内 1D 可用碳表仅液态碳，**固相冷曲线缺失为固有局限**） | 1D 48×256（e/i，源 Cliquid_eos_{e,i} 同网格） | ρ 0.23–100，T 至 848.3 eV（装载器口径；驱动 ≤150 eV 稳妥） | 机器验收，待人工确认 | eeos/ieos id **21551304/305**（逐字节副本）；借 N_Thermos、2D 用 mat_Cliquid-1.0；hBNCpxCheck 2.8e-15；二轮 4 档 96 点（高置信 42）vs 表自洽 +0.06%（子集 +0.16%）；**vs ZhangHuan 2.04 +2.94%（高置信 +2.14%）——与 hBNHub 本尊（+2.48%）同级，hBN 侧换代理无收益**；弱激波段（低 Up）本就不可信（液碳无冷曲线）；T150 两次 dt 塌缩（tempmin 无效，失败 output 三份备查）、T200 提取失败；详见 `validation_cases/hBNCpx/材料表信息.md` |
| **CHHub**（CH ρ0=1.044，SESAME 7592 总表拆分 + LANL C1H1 30 群，2026-08-18） | 1D 73×41（e/i）+ 20×46（z/30 群）+ 2D 73×41 | T 1 eV–100 keV；群 1 eV–100 keV | 机器验收，待人工确认 | eeos/ieos id 75921304/305（split_ieos_table，**源 7592.ieos.multi 实为总表勿当离子表配对**），z/planck/ross id 75922004/75923004/75924004，2D 表 id 75921000；CHHubCheck 能量误差 **3.3e-13**；split 电子表 vs 原生 ELECRO 高温中位 **0.81%**；Hugoniot 4 档 48 点三重判据全过（T200/300 预热吞没），**vs 表自洽中位 +0.1%（46/48 ≤±3%）**，vs LiuXing PBE ~±3% 内，vs SESAME 7592 线 +10.2%（多孔初态差异，与库内 CH 表 +9.1% 同特征）；灰体拟合 T<1keV rms 2.5 dex（LANL 低 T 非幂律，定量走 1D 30 群）；详见 `validation_cases/CHHub/材料表信息.md` |
| **AlHub**（Al ρ0=2.7，SESAME 3717 原生 e/i 对 + NG 40 群含 EPS，2026-08-17） | 1D 67×37 + 81×50（原生对）+ 41×41（z/40 群）+ 2D 83×50 | 群 1–20000 eV | ✅ 完全迁移（2026-08-18 人工确认，优先级排在 stock Al 之后） | eeos/ieos id 37171304/305（**源 elec.multi/ieos.multi 按名配 MULTI 槽位**，教训见流程文档），planck/ross/eps id 37173017/37174017/37175017，z id 37172017，2D 表 id 37171000；AlHubCheck 能量误差 **3.6e-15**（挂 EPS）；Hugoniot 5 档 60 点（高置信 56）三重判据全过，**对四条理论线 dUs 中位 +2.6~+4.2%**（与 stock Al ≤1% 同量级）；详见 `validation_cases/AlHub/材料表信息.md` |
### 1.3 仅 EOS 材料（Multi_BACK 中也不透明度；2D 流体/EOS 可用）

| 材料 | 网格 | 材料 | 网格 |
|---|---|---|---|
| Lucite 有机玻璃 | 73×256 | BeO 氧化铍 | 76×128 |
| PVA | 73×128 | Teflon 特氟隆 | 64×128 |
| Pt 铂 | 101×128 | HE 炸药 | 100×128 |
| C8H7Br 溴代塑料 | 64×128 | PBX9502 炸药 | 100×128 |
| Epoxy 环氧 | 66×256 | | |

### 1.4 无法迁移（Multi_BACK 中无 EOS 文件）

**Ca、Nd、Ge、Se** —— hyades 库中对应文件缺失（仅有 Thermos 不透明度）。如需这四种，可后续用 FEOS 生成 EOS 再经 EOS-tools 转换。

## 二、2D 材料函数索引（r94/m2d-core-9.1/）

- **Material.r**（自带）：MaterialAl/Al_MPQEOS/Au/Be/C/CH/CHOQG/Cu/DT/Fe/HGas/Plastic/PlasticGas/W + **MaterialTi**（首个迁移材料，函数内嵌于此）
- **Material_mig.r**（批量迁移，58 个函数）：MaterialH/He/Li/N/O/Ne/Mg/Si/Ar/V/Ni/Zn/Kr/Mo/Ag/Xe/Gd/Ta/Pb/U/Fe/Cu/W（注：Fe/Cu/W 与自带重复定义，调用时后者覆盖）+ MaterialDD/D/CH + MaterialPSFlash + MaterialAlFlash + 30 种 EOS-only/单群材料函数
  - full 批次（Thermos/CELIA 多群）：`opafun` 为对应多群 Rosseland 表的平均自由程拟合式
  - opc 单群批次（21 种）：`opafun` 为 opc 平均 Rosseland 表拟合式（注释含系数与误差）
  - 仅 9 种真正无不透明度的（Lucite/PVA/Pt/Teflon/HE/PBX9502/Epoxy/BeO/C8H7Br）`opafun=*`

## 三、1D 表库（r94/MULTI-IFE-2015/tables/）新增文件命名约定

| 命名 | 内容 |
|---|---|
| `X_eos_e` / `X_eos_i` | 电子/离子 IEOS（split_ieos_table.py 拆分，id=int(Z)×10⁶+304/305，分数 Z 见规范） |
| `X_Thermos.PLANCK/.ROSSELAND/.ZEFF` | Thermos 多群不透明度/电离度（id=0，输入卡用 *_id=0 匹配） |
| `X_CELIA.PLANCK/.ROSS/.ZEFF` | CELIA 多群表（D/C 系） |
| `X_OPC.ROSS/.PLANCK` | hyades opc 单群平均表（sgo 格式，id=opc 表号；opc2sgo.py 转换） |
| `Ti_LTE.*` | Ti 的 SNOP 30 群表 |
| `PSFlash_eos_e/.eos_i/.ZEFF/.PLANCK/.ROSS/.EPS` | FLASH IONMIX4 系列（§1.2e，EOS-tools 转换，自带 6 群 + 发射） |
| `AlFlash_eos_e/.eos_i/.ZEFF/.PLANCK/.ROSS/.EPS` | FLASH IONMIX4 系列（§1.2e，EOS-tools 转换，自带 6 群 + 发射；无冷曲线，仅热等离子体） |

## 四、已知注意事项

1. **数据可靠性**：与自带表相同警告——适合数值研究，定量科研请换更精确数据库。hyades 源表为 LANL SESAME/QEOS 老库；Thermos/CELIA/SNOP 来源见 Multi_BACK material.base。
2. **Water** EOS 已于 2026-08-11 换用宽表源 eos_311（ρ 2e-6~400 g/cc、T≤15 keV，与 material.base MID1311 一致），此前误用的 eos_312 是窄表（T≤0.345 eV，旧注释"T≤4 keV"系 K/eV 误读）；**Glass** 低温区（<116 eV）依赖外推；**Diamond/Cliquid** 见 §1.2 的 ⚠ 说明。
3. **hyades/Opacity（opc_*）库**：经 Multi_BACK C++ 源码确认，是 (ρ,T) 网格的 **Rosseland/Planck 平均不透明度**（非多群；部分材料 Planck 块全零 = 仅 Rosseland）。**已于 2026-08-11 完成转换（opc2sgo.py）并配给 21 种材料**（§1.2），Multi1D 原生用法即如此（material.base 注 "One group"）。
4. **单位事故记录**：2026-08-10 首次批量转换时压强单位错误（小 1e4 倍），已修复并经源表数值对照复验通过。教训记入指南 §8。
5. **Ne 不透明度**：源文件含退化子表（1200~1200 eV），已删除（77 群）；`batch_migrate.py` 已内置自动删除逻辑。
6. **KrCheck 算例**：用气体密度（3.749e-3 g/cc）；固体密度版本会辐射坍缩超出表范围（物理预期，非表格缺陷）。
7. Fe/Cu/W 的 1D 拆分表来自 mat_2019 MPQEOS 总表（2026.3 自带），拆分后初始电子能量含微小负偏移（官方表固有，不影响守恒）。

## 五、验收记录

| 材料组 | 机器验收 | 人工确认 |
|---|---|---|
| Ti（首例） | ACCEPT 16/16（2026-08-10，两轮子 agent） | ✅ 用户已确认 |
| 批次1 前 13 种（H~Kr） | ACCEPT 11 + Ne/Kr 修复后复验 ACCEPT（13/13） | ⏳ 待用户查看各 XCheck 图 |
| 批次1 后 13 种（Mo~CH） | ACCEPT 13/13 | ⏳ 待用户查看 |
| 批次2 EOS-only 30 种 | ACCEPT 30/30（格式+注册；按约定无 1D 算例） | ⏳ 待用户抽查 |
| 单位修复复验（20 种 hyades 源） | ACCEPT 20/20（压强对照源表 ≤3%） | ⏳ 待用户查看 |
| opc 单群批次（21 种，2026-08-11） | ACCEPT 18 + CAVEAT 3（Diamond/Cliquid 表范围局限、Water 已换宽表复验通过 2.4e-9） | ⏳ 待用户查看（重点 Diamond/Cliquid） |
| **WeiKang 批次（13 种，2026-08-11）** | ACCEPT 9（H_wk/CH2_wk/Fe_wk/Be_wk/Si_wk/SiO2wk12/BN_wk/C9H10_wk/LiF_wk）+ CAVEAT 4（C_wk/C8H8_wk 1D 未通过、Pb_wk 算例外推冒烟、SiO2wk14 1.05e-5）；LiF 经 3 轮复核修复后 ACCEPT | ⏳ 待用户查看 |
| **CaO/SiC FEOS+IONMIX（2026-11-13，1D-only）** | 子 agent 验收 **ACCEPT 17/17**（C3 N/A-1D-only）；本机 FEOS 新算（合成 mat 2011/2012）+ 本机 IONMIX 灰体 OPC（1081/1082）；10 表全过 check_multi_file；CaOCheck/SiCCheck 正常终止（误差 1.3e-7 / 3.8e-14）；FEOS e+i=total 加和性精确；EOS-tools 转换 forward audit 全 pass | ⏳ 待用户查看（`validation_cases/{CaO,SiC}/`） |
| **Hugoniot 二轮核验：Al（2026-08-13）** | 5 强度档 ×12 点，1% 阈值 41 点全程贴 SESAME 3717/3720、Celliers 2005、FEOS（见 `validation_cases/Al/hugoniot_summary/`） | ✅ 人工确认通过（2026-08-17） |
| **Hugoniot 二轮核验：Quartz（α-石英 2.65，2026-08-13）** | 4 强度档 ×12 点，1% 阈值 27 点全程贴线，P-ρ 压 SESAME 7385（见 `validation_cases/Quartz/hugoniot_summary/`）；SiO2wk12 不可用（表 T 上限） | ✅ 人工确认通过（2026-08-17） |
| **Hugoniot 二轮核验：Silica（熔石英 2.204，2026-08-13）** | 4 强度档 ×12 点，P-ρ 精确压表自洽线（compute_table_hugoniot），Us-Up 落 α-石英理论散布带内（见 `validation_cases/Silica/hugoniot_summary/`） | ⏳ 待用户查看 |
| **Hugoniot 二轮核验：CH（2026-08-14 加密重跑）** | 3 强度档 ×24 点 = 72 点（高置信 70），压表自洽线 + PS 交叉参照线（互差 ≲3%）+ SESAME 7592 参考带（重叠段 Us 中位 +9.1%，7592 系多孔 CH 非同一初态）；T150 预热吞没不可用（见 `validation_cases/CH/hugoniot_summary/`） | ⏳ 待用户查看 |
| **FEOS 批次（2 种，2026-08-13/14）** | 1D 表经 EOS-tools 转换（无 bug）；QuartzFEOS 基准对照 FEOS .hug（P≤3.5%、Us≤1.3%）+ SilicaFEOS 自洽对照通过；Hugoniot 算例全档贴线（T≥100 双温振荡经 dttevar/dttivar=0.5 限幅消除） | QuartzFEOS ✅ 人工确认通过且**标记比自带 Quartz 更优**（2026-08-17，用户裁定：宽区 192×512 网格 + 同源 .hug 基准直接验证）；SilicaFEOS ⏳ 待人工确认 |
| **AlFEOS（2026-08-14）** | 子 agent 验收 17 项 PASS（A2/B6/C3/D1/E4 全过）：5 档 ×12 点门禁全过，能量误差 ≤2.1e-12；模拟点 vs 表自洽 Hugoniot Us P50=0.48%（≤1% 39/60）、表自洽线 vs FEOS .hug P50=2.42%/max 3.38%；排障 3 项（理想离子/去重/连续流格式）记录于 `validation_cases/AlFEOS/材料表信息.md` + 陷阱库×2 | ✅ **完全迁移**（2026-08-17 用户人工确认，`validation_cases/AlFEOS/`） |
| **WaterFEOS（2026-08-14）** | 子 agent 验收 **ACCEPT 17/17**（A1-A2/B1-B6/C1-C3/D1/E1-E4 全 PASS）；转换对拍 P≤1.6%；Hugoniot T75/100/150 三档 36 点 RH≤1.2%、Us 对 FEOS 源 +0.92%（33/36 ≤3%）、能量误差 ≤4.2e-11；算例 inegpre=1 + tempmin 补丁（披露见 `validation_cases/WaterFEOS/材料表信息.md`）；非阻塞观察：电子表冷端 tmin=0.1259 eV 略高于 0.03 eV 指引（冷态轻微外推，已披露） | ✅ **完全迁移**（2026-08-17 用户人工确认可用） |
| **WaterAQUA（2026-08-14）** | 子 agent 验收 **ACCEPT 17/17**（A1-A2/B1-B6/C1-C3/D1/E1-E4 全 PASS）。EOS-tools 新 AQUA 读取器（PATCHES_2026-08-14）；`wcheck_T5` 能量误差 5.48e-8；**覆盖警告：T≤8.6 eV 行星 EOS**；算例 inegpre=1 + tempmin=0.02 补丁（文档已按子 agent 三处更正）；**Hugoniot 验证走表级三方对比（用户 2026-08-14 定版）**：in-code 冲击算例物理不可行（`agent/pitfalls/planetary-eos-hugoniot-infeasible.md`）；**复核发现（2026-08-14）**：1D 双温表低温段拆分失真（理想气体离子近似失效，300 K 处 P 符号反转，`agent/pitfalls/total-eos-ideal-ion-split-cold-condensed.md`），此前"拆分自洽 0.9999"是数值恒等式不背书物理——**2D 总量表准确，1D 双温低温段不可信** | ❌ **人工确认不可用**（2026-08-17 用户裁定；产物保留备查，`validation_cases/WaterAQUA/`） |
| **Hugoniot 二轮核验：Water（Multi_BACK，2026-08-14）** | 8 源强档（30–300 eV），可用 6 档 68 点（高置信 47 上图），Up 13–130 km/P 0.5–230 Mbar 全程贴源：**同 Up 下 dUs 对 Multi_BACK 源分档中位 −0.4%~+1.8%，46/47 ≤±3%**；三重判据过（等温线✅ 剖面间断✅ 源对比✅）；T30/T50 弱档方法不可用（见 `validation_cases/Water/hugoniot_summary/`、`材料表信息.md`） | ✅ 人工确认通过（2026-08-17） |
| **WaterSES（2026-11-19，Mancelli SESAME 直接导出）** | 格式验证（check_multi_file×6 全过，emit_multi.py 重封装+split A=6.005）；以 VISAR 战役 12 例交叉验证替代 S1-S9 门禁：**SESAME 7154 与现役 highrou 表三发 RMS 差 ≤0.03、t1 ≤0.05 ns（终解独立 EOS 交叉确认）**；7150/7153 多相较软（054/051 t1 提前 0.13-0.4、RMS 1.7-2.3；052 不动）；全模型水窗压强 +3-4%、TE +20-40%（总表含分子振动能、减理想离子后入电子表）、状态点全部仍在超离子区 （sesame_rerun_compare.png / sesame_PT_states.png） | ✅ **正式备选**（2026-11-19 用户裁定；基准仍 WaterHub， WaterSES 供独立校验/对比工况） |
| **AlHub（2026-08-17，EOS_hub 批次）** | 子 agent 验收 ACCEPT 17/17。原生 e/i 对（**按文件名配槽位**，教训入流程文档）+ NG 40 群含 EPS；Check 5.7e-15；Hugoniot 5 档 60 点（高置信 56）三重判据过，修正配对后对四条理论线 dUs 中位 **+2.6~+4.2%**；P-ρ 高压段偏差分解：几何放大为主（3% ρ→13-18% P）+ 表代差 ~3%（真实）+ 线外点（假象），Garching ρ 网格粗（14-17% 步长）；高压 P-ρ 精度需求高时建议用 stock Al 或 EOS-tools 细网格重转 | ✅ **完全迁移**（2026-08-18 用户人工确认可用；**优先级排在 stock Al 等现有 Al 材料之后**，`validation_cases/AlHub/`） |
| **CHHub（2026-08-18，EOS_hub 批次）** | 子 agent 验收 **ACCEPT 15/15**（独立复算自洽 +0.13%、7592 线 +10.2% 精确重现）。SESAME 7592 拆分 + LANL C1H1 30 群；Check 3.3e-13；Hugoniot 4 档 48 点三重判据过（等温线 5-6 量级✅/剖面间断✅/自洽 +0.1%✅），vs LiuXing PBE 29/48 ≤±3%；T200/300 预热吞没 | ⏳ 待用户查看（`validation_cases/CHHub/`） |
| **hBNFEOS（2026-08-18，FEOS 重算批次）** | 子 agent 验收 **ACCEPT 14/14**（dUs +0.77%/46/48、P(2.04,1eV)=0.4379 均独立复算）。EOS-tools 从 hBN.feos 主表转 + showeos 自建 ZEFF + feos2r94 例外路径 2D 总表；Check 4.7e-15；Hugoniot 4 档 48 点三重判据过；**dt 塌缩事故已修复并沉淀 pitfall**（冷简并电子 Te 跳变 vs dttevar 限幅）；EOS_hub 的 FEOS_dm 候选弃用（疑双 bug）；BNeleFP/BNionFP 对 2026-08-18 翻案为 hBNHub（当时误判为 cBN 而弃用） | ⏳ 待用户查看（`validation_cases/hBNFEOS/`） |
| **cBNFEOS（2026-08-18，FEOS 重算批次）** | 子 agent 首验 REJECT 2 项（2D 表单行写出 + 未登记）→ **修复后复验 ACCEPT 16/16**。EOS-tools 从 cBN.feos 主表转 + showeos 自建 ZEFF + feos2r94 例外路径 2D 总表；Check 2.5e-14；单点对源 ≤0.75%、表自洽线 vs .hug +1.55%；Hugoniot 四档 45 点（T100–200）质控 25 点 vs 表自洽 dUs 中位 +1.65%/max 3.72%（细网格表对照：hBNHub 翻案期数据 +0.46%，差距属 ρ 网格密度）；T30–75 弱档预热吞没、T300 失稳、dttevar=1e12 必要（同 hBNFEOS pitfall）均记录在案 | ⏳ 待用户查看（`validation_cases/cBNFEOS/`） |
| **hBNHub（2026-08-17 入库 / 08-18 身份翻案，EOS_hub 批次）** | 误判期验收（当 cBNHub @3.45）：ACCEPT，Check 7.1e-15、模拟 vs 表自洽 ≤±2.2%（该结论与身份无关仍有效）；vs kang2025 +15% 之谜由用户质疑解开——**表实为 hBN（ρ0=2.04）**，三层证据（自洽线/模拟/反证）翻案，表改名 hBNHub、产物重组；@2.04 重验 5 档 60 点 vs 同源 ZhangHuan 线 +2.39%、vs 表自洽 +0.46%；教训入 pitfall material-identity-cold-pressure-plateau（冷压过零判身份对张力平台表失效） | ⏳ 待用户查看（`validation_cases/hBNHub/`） |
| **hBNHub 换新表 + cBNHub 新增（2026-08-30，work/zhanbin 邢展彬修正版批次）** | 子 agent 验收 **ACCEPT（两材料全项 PASS）**，含 200904 token 源/库逐值独立对比。换表差异定位：离子表未变、电子表修正全在 ρ≲3.5（ρ>3.5 逐值同旧表）；**两相共用 ρ>3.5 分支**（cBNHub 离子表与 hBNHub 完全相同）。quiet start 二轮 12 档一次全过：hBN 82 点 vs 自洽线 −0.20%/vs ZhangHuan +2.48%，cBN 116 点 vs 自洽线 −0.15%/**vs kang/ZhangShuai +8.4~10.5% 系统偏硬（表固有，待用户裁定）**；附记：电子表冷行名义温度在 ρ≥31 角域抬升（算例未触及）；旧表归档 `tables/_superseded_zhanbin20260830/`、旧产物归档 `validation_cases/hBNHub/superseded_oldtable_20260830/`；pitfall bn-zhanbin-tables-shared-branch | ⏳ 待用户查看（`validation_cases/{hBNHub,cBNHub}/`） |
| **碳表代理 BN：cBNCpx + hBNCpx（2026-09-10，导师提议"用碳表仅改初密度作 BN EOS"专项验证）** | cBNCpx=Diamond 表、hBNCpx=Cliquid 表的**字节级副本**（仅改 id 21541304/305、21551304/305，零转换零拆分），算例与 cBNHub/hBNHub 完全同配置（借 N_Thermos、quiet start、inegpre=1）保证 EOS 单变量对比。Check 5.6e-15/2.8e-15；二轮 96+96 点 vs 表自洽 −0.39%/+0.06%（程序忠实）；**核心结论：cBNCpx vs ZhangShuai 3.45（同初密度）−2.7%、vs kang 3.44 +2.9%——落在两文献线之间，显著优于邢表 +8~10% 偏硬；hBNCpx vs ZhangHuan +2.9% 与 hBNHub（+2.5%）同级无增益**。子 agent 首验 REJECT 2 文档项（未登记 + T150 产物引用不实）→ 登记/修正/残留进程清理后**复验 ACCEPT**（含 C2 替代裁定逐字节 9 字节定位与源三元组拆分自洽独立复算）；hBN T150 两次 dt 塌缩（tempmin 无效）、T200/T300 提取失败均记录；T150 残留 multi 进程事故（pkill 按名匹配杀不掉）已清理，pitfall 待补 | ⏳ 待用户裁定（cBNCpx 是否采纳为 cBN 生产 EOS；`validation_cases/{cBNCpx,hBNCpx}/`） |
| **LiFHub（2026-08-17，EOS_hub 批次）** | 子 agent 验收 ACCEPT 16/16。六表+2D 全 ✓；Check 能量误差 1.1e-14（40 群）；Hugoniot 7 档 83 点三重判据全过，交叉参照 LiF_wk 有效段 dUs ≤±2.4%；T300 预热吞没；Hawreliak 2023 PRB 理论线 Us=5.144+1.355Up 已叠加（≥150 eV 档 dUs −1.0%~+1.6%，低档偏硬趋势与阻抗参考一致，覆盖不足处虚线外推） | ✅ **完全迁移**（2026-08-17 用户人工确认，`validation_cases/LiFHub/`） |
| **ParyleneHub（2026-08-17，EOS_hub 批次首例）** | 子 agent 验收 15/16 PASS + D1 复验（补登记后）。六表+2D 全 ✓；Check 能量误差 9.4e-14（40 群）；Hugoniot 5 档 60 点三重判据全过，交叉参照 hyades 表 dUs +0.3%（54/54 ≤3%）；≥150 eV 档预热吞没 | ⏳ 待用户查看（`validation_cases/ParyleneHub/ParyleneHubCheck/` 两张 PNG + `hugoniot_summary/`） |
| **PSFlash（2026-08-14）** | 子 agent 验收 ACCEPT 16/16（A1-A2/B1-B6/C1-C3/D1/E1-E4 全过）。EOS-tools ionmix→multi 六表 + 2D 总表全 ✓；PSFlashCheck 能量误差 5.6e-12（挂 EPS）/ 3.4e-15（不挂）；Hugoniot 复检结论：**方法不可用**——35–55 eV 等温压缩波（点贴 T=2 eV 等温线，非自洽线，先前"压线"判断已推翻更正）、≥60 eV 预热吞没；新增等温线判据（COLD_LOCUS）与剖面检验工具（profiles_check.png）入流程与陷阱库；ZEFF type 串 + mgo 重打包两个新坑记陷阱库 | ❌ **人工确认不可用**（2026-08-17 用户裁定；产物保留备查，`validation_cases/PSFlash/`） |
| **AlFlash（2026-08-14）** | 子 agent 验收 13/14 PASS（D1 清单登记已补）：EOS-tools ionmix→multi 六表 + 2D 总表全 ✓；AlFlashCheck 能量误差 1.5e-10（挂 EPS）、6 群加载正常；源绝对值对拍 P50~2e-4、ZEFF 精确；Hugoniot 系统性偏软 ~54% 已归因（直接源 cn4 反解 Hugoniot 证实表无冷曲线，同工具对 AlFEOS 得 2.4% 证明工具无误，`agent/pitfalls/ionmix-al-no-cold-curve.md` + COLD_LOCUS 判据）；仅限热等离子体烧蚀场景 | ❌ **人工确认不可用**（2026-08-17 用户裁定：偏软 ~54% 不可接受，不标完全迁移；文件与 validation_cases 产物保留备查，`validation_cases/AlFlash/`） |

| **二轮 Hugoniot 批量补验（2026-08-20，44 种库内材料全覆盖）** | 此前的 20 种之外，其余全部有六表配置的材料（Thermos/opc/wk/CELIA 族 47 种可跑 + Air/N/O 崩溃待查）统一生成 hugoniot_T50/100/200/300（quiet start 标准配置，配置自动解析自各 XCheck 并注册 MAT_TABLES/SELF_HUG），批量运行+门禁 A-E 提取+表自洽线判据（无独立理论线）。**41 种有采信点、33 种 dUs 中位 |med|≤1%**：贴线优（≤±3% 占比高、med≤0.6%）：Kr/Ar/Ne/SS/V/Sn/Ag/Cu/Fe/Gd/Eu/Pb/Zn/Ti/W/WC/Mo/Mg/Si/Glass/CD2/PS/PE/Al2O3/U/Li/LiD/Ni/Cliquid/Parylene/Mylar/Cphenolic/Diamond/D/PU（D 仅 T50、PU/Ni 经 dttevar=1e12 修复 dt 塌缩后 23/26 点）。**方法不可用/异常待查**：H/He/H_wk/CH2_wk/Fe_wk/Pb_wk（气体或表 ρ 域不含初态→门禁 A 全剔）、Be_wk（dUs −38%，源 19 点定性参考级已知）、SiO2wk14（−2.9% 已知 CAVEAT）、Xe（+2.4% 偏高待复核）、Air（tridia 奇异 inegpre/tempmin 无效）、N/O（首步非确定性 NaN 段错误，8-10 旧二进制同现、历史 NCheck 第三跑同崩，非源码回归，待专项排查）。排障修复沉淀：inegpre=1（CD2/Cliquid/Cphenolic/D-T50 tridia）、tempmin=0.02（CH2_wk/H/PE/Mylar）、dttevar=1e12（D/PU/Ni dt 塌缩）。每材料 `validation_cases/<X>/hugoniot_summary/` + `材料表信息.md` 二轮章节 | ⏳ 待用户查看（重点：Xe 偏高、N/O 崩溃、Be_wk） |

| **Diamond 二轮深化：独立 DFT 理论线 + 算例加密（2026-08-24）** | ① Romero&Mattsson 2007（PRB 76,214113）四张附录表提取（固/液 EOS+Hugoniot，RH 能量闭合交叉校验中位残差 0.009 eV/atom）并作为**独立理论线**登记入 `hugoniot_report.py` THEORY_TXT（IM-tool 线文件 Diamond_Romero2007_{solid,liquid}.txt）；对拍结论：**库表与 DFT 一致到百分之几、系统性偏硬 ~2%**（液相 EOS 面 40 点 dP 中位 −1.1%；此前 Katagiri 转引拟合偏高 1–4% 不可作基准）。② 算例梯 3→16 档（补 T30/45/60/75/120/160/170/180/210/240/280 + 替补 T120/T160；T30 零采信、**T130/T140 tridia 奇异崩溃**为该区间数值病），`HUG_NPOINTS=96` 提密采样后 **695 采信/61 高置信上图（Up 6.2–86.9 km/s）**。③ **方法物理极限查明**：trad≤120 eV 冷金刚石透明（光子峰 <K 边 284 eV）→辐射介导波前，dUs 偏低 −1.7~−8.5% 且内残差 4~25%（外不贴线，正确被上图过滤剔除）；内符合 ≤1% 仅 trad≥230 段出现；Up<44 km/s 段上图仍只有理论线（如需该段力学点需换活塞驱动等方法，超出辐射浴管线）。产物 `validation_cases/Diamond/hugoniot_summary/`（旧图存 `_archive_preswap/`） | ⏳ 待用户查看 |

| **刘兴 A.2 碳表 P 列根因终局：Excel 摘取公式错误，源数据已获救（2026-08-24 晚）** | 用户提供刘兴本人 Excel（work/liuxing/EOS_carbon.xlsx）：Sheet2（附表源）P 列公式为 **`=E/100`**（232/232 行中招，未引用压强列）；**Sheet1（刘兴指定正确源）核验全过**——理想气体渐近 N_P 2.25→6.99 教科书级、D 支冷压在（ρ=6 低 T 原始 P 6.3–6.9 Mbar）、修正量级正常。正确表已重建 `work/liuxing/EOS_carbon_corrected.csv`（232 行）。**C_wk 由"弃用"更新为"具备重建条件"**（待用户决定是否走 S1-S9 重迁移）；低 T 固相行（ρ≤4、T≲0.65 eV）16 原子 MD 固相采样局限低置信。前次 ❌ 冻结结论中"P 不可修复"作废，其余（weikang2multi 混构型插值问题）仍成立。**附：六附表全量复筛（同晚）——A.1/A.3/A.4/A.5/A.6 五表 E/100 零中招、N_P 渐近与 ρ 单调全部健康（A.1 中位恰 2.00=氢全电离），仅 A.2 一张坏，需反馈刘兴的只有它**；库内 H_wk/C8H8_wk/C9H10_wk/CH2_wk/Fe_wk 源数据均确认无恙 | ⏳ 待用户决定 C_wk 是否重建 |

**人工查看入口**：`validation_cases/<X>/<X>Check/`（output + density_heatmap.png + profiles_mid.png）；二轮 Hugoniot 见 `validation_cases/<X>/hugoniot_summary/`。
确认无误的材料请告诉我，我在上表标记"完全迁移 ✅"；有问题集中反馈即可。
