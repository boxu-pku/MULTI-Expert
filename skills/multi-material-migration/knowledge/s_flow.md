---
title: S1-S9 迁移流程逐步详解
skill: multi-material-migration
category: internals
source_anchors:
  - 材料迁移验证规范.md §2
  - work/eos_opacity_tools/batch_migrate.py:L17-L18
  - work/eos_opacity_tools/split_ieos_table.py:L18-L23
doc_ref: "材料迁移验证规范.md §2（迁移执行步骤）"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - S1-S9
  - 迁移流程
  - 步骤
---

# S1-S9 迁移流程逐步详解

> 本体：《材料迁移验证规范.md §2》。本条目是执行视角的逐步操作 + 命令。
> **优先用 batch_migrate.py 清单驱动**（自动完成 S1-S7），手工步骤用于工具未覆盖的新源类型。

## S1 源文件复制与修复

- 2D 总表 → `r94/mat_<X>-1.0/`；1D 表 → `r94/MULTI-IFE-2015/tables/`
- 修复：`$MULTI/work/eos_opacity_tools/fix_multi_file.sh <文件>`（CRLF + -1.#INF）
- batch 内等价物：`dos2unix_file(src, dst, fix_inf=...)`（`batch_migrate.py:L51-L55`）

> **EOS 转换铁律（L-008 / CLAUDE.md 铁律 6）**：源格式转换（hyades/SESAME/FEOS →
> MULTI IEOS）**一律用 EOS-tools**（`cli/eos_convert.py`，用户指定唯一信任工具），
> 不手写转换链；FEOS 自带 `feos2multi.py`/`feos2r94.py` **禁用**（双 bug，
> `agent/pitfalls/feos-converter-layout-energyunit.md`）。
> 两起手写链事故：2026-08-10 压强（`pressure-unit-confusion.md`）、
> 2026-08-13 能量 ×1000（`migrated-eos-energy-scale-1000x.md`）。
> 若只能走 batch_migrate 的手工组装路径，S3 之外**必须加做**：
> 与源表绝对值对照 + PdV 热力学一致性检查（§S4a）。

> **FEOS 源迁移规约（2026-08-18 用户定版）**：
> 1. **一律从 `.feos` 主表迁移**（如 `FEOS/EOS-Data/<材料>/<材料>.feos`），
>    不用目录里现成的 `_feosele/_feosion/.301/.multi` 等派生产物
>    （feos2multi 系产物带双 bug；其余派生口径不一）；
> 2. 开工前**先读 FEOS 项目的相关 skill**（`$MULTI_LIBS/FEOS/FEOS/.zcode/skills/`
>    的 `feos-converter`〔转换约定〕与 `feos-visualizer`〔showeos〕）；
> 3. 用 **showeos 生成 Hugoniot 参考线**：检查 `<材料>.par` 的 Hugoniot 段
>    （Rho0/T0 初态、Pmax），`cd FEOS/EOS-Data/<材料> && ../showeos <材料> 5`
>    → `<材料>.hug`（列 ρ,T,P,E,Us,Up），**拷贝到
>    `validation_cases/<X>/` 备用**——这是二轮检验的源级理论线
>    （比 IM_tool 通用参考线更权威，因为是同一 FEOS 表自解的 RH 线）。

## S2 总 IEOS 拆分（1D 需要电子/离子分离表）

```bash
python3 $MULTI/work/eos_opacity_tools/split_ieos_table.py \
    <总表> <A> tables/<X>_eos_e tables/<X>_eos_i <e_id> <i_id>
```
- id 约定：电子 int(Z)×10⁶+304、离子 +305（分数 Z：round(Z*100)×10⁴+304/305；
  `batch_migrate.py:L164-L168`）
- 算法：EleTab 复刻（减理想离子）+ 理想气体离子表（multi-eos-format/knowledge/ieos_format.md §5）

## S3 逐文件格式验证

```bash
python3 $MULTI/work/eos_opacity_tools/check_multi_file.py <每个迁移文件>
# 全 ✓ 且退出码 0 才算过；核对 NR/NE 与记录一致、mgo 子表数=群数、sgo type 正确
```

## S4 拆分自洽性抽查

比较 Pe+Pi vs P_tot：按各自能量网格反查（同索引直接相加在高温端有系统性偏差，
可达数倍，属正常——迁移指南 §8-8）；**与官方 Be 表偏差同量级（~20% 内）即合格**。
脚本可仿指南 §7.4 写法自写。

## S4a 转换正确性加验（2026-08-13 起，手写链转换必做）

凡 EOS 转换未经 EOS-tools CLI 已审计路径（如 batch_migrate 手工组装）：

1. **与源表物理量绝对值对照**（P/E 各取若干 (ρ,T) 状态点，dP/P ≤3%——
   压强单位事故的复验口径）
2. **PdV 热力学一致性检查**（`agent/pitfalls/migrated-eos-energy-scale-1000x.md`"判定方法"）：
   沿表冷压列做 ∫P dV 梯形积分与 e0 密度差比较，比值应 ≈1（≈1000 即能量轴病态）
3. EOS-tools audit 报告无超阈值误差（若走 CLI）

## S5 2D 材料函数 + 重编译

- 单种手工：`r94/m2d-core-9.1/Material.r` 仿 `MaterialAu()`（`Material.r:L96-L109`）添加
  `Material<X>()`（模板见迁移指南 §7.1）
- 批量：`gen_material_functions.py` 生成 `Material_mig.r`（含 Rosseland 拟合 opafun）
- 重编译：`cd $MULTI/r94/m2d-core-9.1 && x.2.library`
- 验证：`grep -c "Material<X>" Material.c` ≥ 1 且 Material.c 新于/同日于 Material.r（规范 §C3）

## S6 建 1D 验收算例

`validation_cases/<X>Check/`（**独立目录，与 cases/ 官方算例分离，永久保留**）。
设计模板见 `knowledge/case_design.md`；生成器：`batch_migrate.py:make_case()`（L246-L261，
克隆 TiCheck 的 RUN/CLEAR + 写 data.in/FILELIST）。

## S7 运行算例

```bash
cd $MULTI/validation_cases/<X>Check && ./RUN
# ktag 消失后查 output（判读见 multi-case-runner/knowledge/output_reading.md）
```

## S7b 可视化

```bash
python3 $MULTI/work/eos_opacity_tools/plot_1d_validation.py $MULTI/validation_cases/<X>Check
# 产物: density_heatmap.png + profiles_mid.png（存算例目录）
```

## S8 子 agent 独立验收

- **必须新起子 agent**（不带迁移者上下文），提示词模板见 `knowledge/acceptance.md §4`
- 检查 A1-A2、B1-B6、C1-C3、D1、E1-E4（D2 与 F 节不在子 agent 范围）
- REJECT → 修复后重新验收（可同一子 agent 复验，说明修复点）

## S9 登记与人工确认

1. 更新《MULTI-2D_材料库清单.md》：材料行（分类/网格/群数/验证算例）+ §五验收记录，
   状态 = "**机器验收通过，待人工确认**"
2. 向用户报告：清单行 + 查看入口（`validation_cases/<X>Check/` 的 output 与两张 PNG）
3. **用户明确确认后**标"完全迁移 ✅"（规范 §F；在此之前任何情况下不得标 ✅）

## 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
