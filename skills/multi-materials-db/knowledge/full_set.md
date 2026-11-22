---
title: 全套材料明细（2D EOS + 1D 电子/离子 EOS + 多群不透明度 + Zeff + 1D 验证）
skill: multi-materials-db
category: reference
source_anchors:
  - MULTI-2D_材料库清单.md §1.1
  - MULTI-2D_材料库清单.md §三
doc_ref: "MULTI-2D_材料库清单.md §1.1"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 全套材料
  - 多群
  - 明细
---

# 全套材料明细

> **TL;DR**：全套 = 2D EOS（mat_X-1.0/X_eos + Material 函数）+ 1D 电子/离子拆分 EOS + 多群不透明度（Thermos/CELIA/SNOP）+ Zeff + 1D 验证算例（XCheck）。迁移 27+1 种 + 自带 5 种。

## 1. 迁移的全套材料（27+1 种，清单 §1.1）

| 材料 | 2D 模块 | EOS 网格 | 不透明度(群数) | Zeff | 验证算例 |
|---|---|---|---|---|---|
| H 氢 | mat_H-1.0 | 50×128 | Thermos 82 群 | ✔ | HCheck |
| He 氦 | mat_He-1.0 | 38×128 | 108 群 | ✔ | HeCheck |
| Li 锂 | mat_Li-1.0 | 50×128 | 74 群 | ✔ | LiCheck |
| N 氮 | mat_N-1.0 | 50×128 | 124 群 | ✔ | NCheck |
| O 氧 | mat_O-1.0 | 50×128 | 31 群 | ✔ | OCheck |
| Ne 氖 | mat_Ne-1.0 | 50×128 | 77 群（已删退化子表） | ✔ | NeCheck |
| Mg 镁 | mat_Mg-1.0 | 50×128 | 105 群 | ✔ | MgCheck |
| Si 硅 | mat_Si-1.0 | 127×100 | 110 群 | ✔ | SiCheck |
| Ar 氩 | mat_Ar-1.0 | 50×128 | 121 群 | ✔ | ArCheck |
| V 钒 | mat_V-1.0 | 50×128 | 106 群 | ✔ | VCheck |
| Fe 铁 | mat_2019 | 77×100 | 35 群 | ✔ | FeCheck |
| Ni 镍 | mat_Ni-1.0 | 50×128 | 109 群 | ✔ | NiCheck |
| Cu 铜 | mat_2019 | 71×100 | 129 群 | ✔ | CuCheck |
| Zn 锌 | mat_Zn-1.0 | 50×128 | 57 群 | ✔ | ZnCheck |
| Kr 氪 | mat_Kr-1.0 | 45×128 | 158 群 | ✔ | KrCheck（**气体密度**算例） |
| Mo 钼 | mat_Mo-1.0 | 101×128 | 25 群 | ✔ | MoCheck |
| Ag 银 | mat_Ag-1.0 | 69×128 | 40 群 | ✔ | AgCheck |
| Xe 氙 | mat_Xe-1.0 | 66×128 | 60 群 | ✔ | XeCheck |
| Gd 钆 | mat_Gd-1.0 | 70×128 | 124 群 | ✔ | GdCheck |
| Ta 钽 | mat_Ta-1.0 | 49×128 | 21 群 | ✔ | TaCheck |
| W 钨 | mat_2019 | 71×100 | 24 群 | ✔ | WCheck |
| Pb 铅 | mat_Pb-1.0 | 101×128 | 35 群 | ✔ | PbCheck |
| U 铀 | mat_U-1.0 | 101×128 | 20 群 | ✔ | UCheck |
| Ti 钛 | mat_Ti-1.0 | 45×100 | SNOP 30 群 | ✔ | TiCheck（首例，用户已确认 ✅） |
| DD 氘氘 | mat_DD-1.0 | 50×25 | CELIA 20 群 | ✔ | DDCheck |
| D 氘 | mat_D-1.0 | 50×128 | CELIA 20 群（借纯氘表） | ✔ | DCheck |
| CH 塑料 | mat_CH-1.0 | 101×100 | CELIA 20 群（借碳表） | ✔ | CHCheck |
| AlFEOS 铝(FEOS 3717) | mat_AlFEOS-1.0 | 电子192×463/理想离子192×495/2D 192×136 | 借 stock tables/Al SNOP 20 群（同元素） | ✔（stock 10002000） | AlFEOSHug_T{50..300}（Hugoniot 路线，非 XCheck；2026-08-14 机器 ACCEPT，待人工确认） |
| AlFlash 铝(FLASH IONMIX4 al-imx-003) | mat_AlFlash-1.0 | 电子25×128/离子25×64/2D 25×128 | 自带 IONMIX 6 群 + 发射表 | ✔（z_id 1） | AlFlashCheck（辐射波路线；Hugoniot 不可用，无冷曲线，仅热等离子体） |

## 2. 自带全套（2026.3 随发行）

**DT、C、Al、Be、Au**——`r94/MULTI-IFE-2015/tables/` 下的
DT、Carbon、Al、CPC88、Be20keV、Mix20keV 等（含电子/离子分离 IEOS + 多群不透明度 + EPS）。
DT 表源自 CELIA D_20G（`tables/README:L14-L18`）。

另有 2D EOS（1D 全套由迁移补齐）：Cu/Fe/W（mat_2019 MPQEOS .i301）、
Si（mat_Si-1.0 液/汽反演表）、CH（mat_C-1.0/CH_ieos 101×100）。

## 3. 1D 表文件命名约定（清单 §三）

| 命名 | 内容 | id |
|---|---|---|
| `X_eos_e` / `X_eos_i` | 电子/离子 IEOS（split_ieos_table.py 拆分） | int(Z)×10⁶+304/305（分数 Z：round(Z*100)×10⁴+304/305） |
| `X_Thermos.PLANCK/.ROSSELAND/.ZEFF` | Thermos 多群 | 0（输入卡 `*_id=0`） |
| `X_CELIA.PLANCK/.ROSS/.ZEFF` | CELIA 多群 | 源文件 id |
| `Ti_LTE.*` | Ti 的 SNOP 30 群 | 27003000/27004000/27002000 |

## 4. 2D 材料函数

- 自带 + MaterialTi：`r94/m2d-core-9.1/Material.r`（MaterialAl:43、MaterialAu:96-109、
  MaterialTi:418-431 等）
- 迁移 56 个：`r94/m2d-core-9.1/Material_mig.r`（MaterialH:14 … MaterialEu:1473；
  full 批次的 opafun 为对应多群 Rosseland 表平均自由程拟合式，注释含系数/rms/适用范围）
- Fe/Cu/W 与自带重复定义，**调用时后者（Material_mig.r）覆盖**（清单 §二注）

## 5. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
| 2026-08-14 | 新增 AlFEOS 行（FEOS 系列首个全套多群；离子表理想气体约定见 `agent/pitfalls/eos-tools-dup-rows-ideal-ion.md`） | claude |
| 2026-08-14 | 新增 AlFlash 行（FLASH IONMIX4 系列；无冷曲线，Hugoniot 不可用，仅热等离子体烧蚀） | claude |
