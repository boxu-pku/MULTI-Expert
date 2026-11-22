---
title: 转换与拆分工具 — split_ieos_table.py / opc2sgo.py / EOS-tools CLI / batch_migrate.py / migrate_opc_batch.py / gen_material_functions.py
skill: multi-table-tools
category: internals
source_anchors:
  - work/eos_opacity_tools/split_ieos_table.py:L18-L23
  - work/eos_opacity_tools/opc2sgo.py:L18-L20
  - work/eos_opacity_tools/batch_migrate.py:L17-L18
  - work/eos_opacity_tools/migrate_opc_batch.py:L1-L15
  - work/eos_opacity_tools/gen_material_functions.py:L1-L11
  - MULTI-2D_材料库迁移指南.md §6.1
doc_ref: "MULTI-2D_材料库迁移指南.md §6.1, §7.4"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - split_ieos_table
  - opc2sgo
  - EOS-tools
  - batch_migrate
  - 转换
  - 拆分
---

# 转换与拆分工具

## 1. split_ieos_table.py — 总 IEOS → 电子/离子表

**算法**：复刻 `Mat2013_EleTab`（电子=总表减理想离子；离子=理想气体 γ=5/3），
逐点一致（报头 L1-L16；split_electron L75-L109；make_ion_ideal L112-L124）。

**用法**（L18-L23）：
```bash
python3 $MULTI/work/eos_opacity_tools/split_ieos_table.py \
    <总表> <原子量A> <电子输出> <离子输出> [电子id 离子id]
# 例: python3 split_ieos_table.py Ti_eos 47.867 Ti_eos_e Ti_eos_i 22000304 22000305
```

**id 约定**：电子 int(Z)×10⁶+304、离子 +305（分数 Z：round(Z*100)×10⁴+304/305；
`batch_migrate.py:elem_ids` L164-L168）。

**自检输出**：源表 id/NR/NE + 高温端抽查（P_tot vs P_e+P_i；cgs 单位，L152-L157）。
**注意**：Pe+Pi 与 P_tot 的同索引偏差在高温端可达数倍属正常（能量网格不同，
迁移指南 §8-8）；合格判据 = 与官方 Be 表偏差同量级（验证规范 §S4）。

## 2. opc2sgo.py — hyades opc 平均表 → MULTI sgo 单群表

**语义**（报头 L1-L20）：读 opc（标题2行 + NR,NT,ρ(g/cc),T(keV),Rosseland(NT×NR),Planck）
→ 写两个 sgo 文件：`<前缀>.ROSS`（type ` 0.40000000E+01`）与 `<前缀>.PLANCK`
（` 0.70000000E+01`），双兼容 type 串；值 log10 化，T 由 keV→eV。
Planck 块全零时复制 Rosseland（源码规则，L40-L41）。

**用法**：
```bash
python3 $MULTI/work/eos_opacity_tools/opc2sgo.py <opc文件> <id> <输出前缀>
# 例: python3 opc2sgo.py .../opc_1022.dat 1022 tables/Glass_OPC
```

## 3. EOS-tools CLI — 外部格式转换主力（**唯一信任工具**）

> **铁律（CLAUDE.md/AGENTS.md §铁律 6；LESSONS_LEARNED L-008）**：EOS 格式转换
> **一律用 EOS-tools**（用户指定唯一信任工具），不手写转换链、不用第三方转换器。
> FEOS 项目自带 `feos2multi.py`/`feos2r94.py` 有布局+能量单位（×100）双 bug，**禁用**
> （唯一例外：2D 单温总表无 EOS-tools 路径，用后必须按
> `agent/pitfalls/feos-converter-layout-energyunit.md` 两步修复）。
> 若必须手工组装数据集（如 batch_migrate 定制流程），转换后**必须与源表做物理量
> 绝对值抽查对照 + PdV 热力学一致性检查**（`agent/pitfalls/migrated-eos-energy-scale-1000x.md`
> 的"判定方法"节）——2026-08-10 压强单位与 2026-08-13 能量 ×1000 两起事故都是手写链引入的。

位置：`$MULTI_LIBS/EOS_converter_xubo/EOS-tools`（迁移指南 §6.1）。
能力：读写 IONMIX4/SESAME(301/304/305)/Hyades/**MULTI**/FEOS；不透明度读写
IONMIX4/Hyades/MULTI、只读 TOPS。

```bash
cd $MULTI_LIBS/EOS_converter_xubo/EOS-tools
# EOS: Hyades → MULTI（单温总 EOS 走 electron 通道；离子由理想气体推导）
python3 cli/eos_convert.py --from hyades --to multi \
    --electron-file <源.dat> --zeff-file none --atom-a <A> --atom-z <Z> \
    --name <X> --output <输出前缀>
# 产物: <X>_electron.multi / <X>_ion.multi / <X>_zeff.multi + *.conversion-audit.json/csv

# EOS: FEOS → MULTI（feos2multi/feos2r94 的正确替代，无其双 bug）
python3 cli/eos_convert.py --from feos --to multi --electron-file <源.feos> ...

# 不透明度重分群（=1 即聚合成单群；Rosseland 用 dB/dT 调和矩、Planck 用 B 算术矩）
python3 cli/opacity_convert.py ... --opacity-groups 1
```

**必查**：audit 报告的 P95/最大相对误差与覆盖率（迁移指南 §7.4-1）。
**三个已知注意**：
- 代码注释把能量单位标 "MJ/kg"，实际数值对应 Mbar·cm³/g（换算系数 1e-5 正确，仅注释误导）
- 其 zeff 表头 type 串（` 6.00000000e+00`）1D 不认——给 1D 用改 ` 0.60000000E+01`
  （agent/pitfalls/zeff-type-string-variants.md）
- `basefunctions/read_hyades.py` 严格长度校验拒读个别源文件（如 eos_23.dat 含
  0 填充多 4 个值），需容忍补丁（见 agent/pitfalls/migrated-eos-energy-scale-1000x.md"修复方向"）

查询网格覆盖：`cli/eos_query.py`；GUI（含裁切/诊断/审计）：`launcher.py`。

## 4. batch_migrate.py + migrate_manifest.py — 清单驱动批量迁移

**语义**（报头 L1-L18）：对清单每种材料执行 full 批次（EOS 转换→拆分→Thermos/CELIA
表修复→验证→建算例）/ celia 批次 / eos_only 批次。

**用法**：
```bash
cd $MULTI/work/eos_opacity_tools
python3 batch_migrate.py              # 全部
python3 batch_migrate.py Ta Gd        # 指定材料
```

**清单编辑**（`migrate_manifest.py`）：BATCH_FULL（name, A, Z, rho0, eos_src, thermos符号）/
BATCH_CELIA / BATCH_EOS_ONLY；数据源路径常量在 L14-L18。

**内置自动处理**：
- `dos2unix_file(..., fix_inf=True)`（L51-L55）：去 CR + 修 -1.#INF
- `fix_missing_e_fields()`（L99-L128）：Fortran 缺 e 指数修复（临时文件）
- `drop_degenerate_groups()`（L71-L95）：删 f1==f2 退化子表（防 1D 加载截断）
- hyades 换算（L137-L138）：P ×1e-7→MPa、E ÷1e4→J/g（**单位事故已修复，勿再改错**）
- 算例生成 `make_case()`（L246-L261）：克隆 TiCheck 的 RUN/CLEAR
- 汇总报告：每材料 PASS/FAIL + 总计

## 5. migrate_opc_batch.py — 为 EOS-only 材料配 opc 单群不透明度

按 Multi_BACK 原生映射（`OPC_MAP` L31-L43，含借用规则）：opc→sgo（2 个文件）→
check 验证 → 生成 1D 验证算例 → 拟合 Rosseland 自由程（写 /tmp/opc_fits.txt 供
gen_material_functions 使用）。用法：`python3 migrate_opc_batch.py`（无参数，全量）。

## 6. gen_material_functions.py — 生成 2D 材料函数 Material_mig.r

对 full/celia 批次：Rosseland 多群表→dB/dT 权重群间平均→λ(ρ,T)→log 空间最小二乘拟合
`log10 λ = a + s·logT + r·logρ`（L53-L79），写入 `r94/m2d-core-9.1/Material_mig.r`
（含系数/rms/适用范围注释）。eos_only 无拟合者 `opafun=*`。
**生成后必须重编译**：`cd $MULTI/r94/m2d-core-9.1 && x.2.library`。

## 7. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
