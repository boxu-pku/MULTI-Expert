---
title: MULTI-2D 材料库构成总览（77 种，四分类）
skill: multi-materials-db
category: overview
source_anchors:
  - MULTI-2D_材料库清单.md §一
  - MULTI-2D_材料库清单.md §五
  - r94/m2d-core-9.1/Material_mig.r:L1-L4
doc_ref: "MULTI-2D_材料库清单.md（全文，一手总账）"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 材料库
  - 分类
  - 总账
  - 验收
---

# MULTI-2D 材料库构成总览

> **TL;DR**：79 种材料（2026-08-14）分四类：全套（2D EOS + 1D 电子/离子 EOS + 多群不透明度 + Zeff + 1D 验证算例）、单群 opc、仅 EOS、无法迁移。一手总账：`MULTI-2D_材料库清单.md`。

## 1. 四分类速览

| 分类 | 数量 | 能做什么 | 明细 |
|---|---|---|---|
| **全套** | 自带 5（DT/C/Al/Be/Au）+ 迁移 27+3（含 AlFEOS/AlFlash） | 2D 流体+辐射、1D 多群全套 | `knowledge/full_set.md` |
| **单群 opc** | 21 | 2D 流体+灰体辐射、1D 灰体 | `knowledge/single_group.md` |
| **仅 EOS** | 9 | 仅 2D 流体/EOS（无辐射输运） | `knowledge/eos_only.md` |
| **无法迁移** | 4（Ca/Nd/Ge/Se） | Multi_BACK 无 EOS 文件 | `knowledge/eos_only.md` |

> 自带材料中 Cu/Fe/W/Si/CH 有 2D EOS（mat_2019 MPQEOS / mat_Si-1.0 / mat_C-1.0），
> 迁移批次已为 Fe/Cu/W 补齐 1D 全套（清单 §1.1 注）。

## 2. 材料资产的存放位置

| 资产 | 位置 | 说明 |
|---|---|---|
| 2D EOS 表 | `r94/mat_<X>-1.0/<X>_eos`（自带在 mat_DT-1.0 等） | IEOS 单表文件 |
| 2D 材料函数 | `r94/m2d-core-9.1/Material.r`（自带+MaterialTi）、`Material_mig.r`（56 个迁移函数，`L1-L4` 注明自动生成） | User.r 中 `MaterialX()` 调用 |
| 1D 表 | `r94/MULTI-IFE-2015/tables/`：`X_eos_e/i`、`X_Thermos.PLANCK/.ROSSELAND/.ZEFF`、`X_CELIA.*`、`X_OPC.ROSS/.PLANCK`、`Ti_LTE.*` | 命名约定见清单 §三 |
| 1D 验证算例 | `validation_cases/<X>Check/`（output + density_heatmap.png + profiles_mid.png，**永久保留**） | 验证规范 §E |

## 3. 验收状态（清单 §五，两级）

| 材料组 | 机器验收 | 人工确认 |
|---|---|---|
| Ti（首例） | ACCEPT 16/16（2026-08-10） | ✅ 用户已确认 |
| 批次1 前 13 种（H~Kr） | ACCEPT 11 + Ne/Kr 修复复验 13/13 | ⏳ 待查看 |
| 批次1 后 13 种（Mo~CH） | ACCEPT 13/13 | ⏳ 待查看 |
| 批次2 EOS-only 30 种 | ACCEPT 30/30 | ⏳ 待抽查 |
| 单位修复复验（20 种） | ACCEPT 20/20（压强对源表 ≤3%） | ⏳ 待查看 |
| opc 单群批次（21 种） | ACCEPT 18 + CAVEAT 3（Diamond/Cliquid/Water——Water 已换宽表复验通过） | ⏳ 待查看（重点 Diamond/Cliquid） |
| AlFEOS（FEOS 铝，2026-08-14） | ACCEPT 17 项（5 档 60 点 Hugoniot 门禁全过；vs 表自洽线 Us P50=0.48%、vs FEOS .hug 2.42%） | ⏳ 待查看（`validation_cases/AlFEOS/hugoniot_summary/`） |
| AlFlash（FLASH IONMIX4 铝，2026-08-14） | ACCEPT 13/14（D1 已补）；AlFlashCheck 1.5e-10；Hugoniot 不可用（无冷曲线，仅热等离子体） | ⏳ 待查看（`validation_cases/AlFlash/`） |

**人工查看入口**：`validation_cases/<X>Check/`；用户确认后清单标"完全迁移 ✅"。

## 4. 已知注意事项（清单 §四，摘要）

1. **数据可靠性**：与自带表同警告——适合数值研究，定量科研换更精确数据库；
   hyades 源为 LANL SESAME/QEOS 老库；Thermos/CELIA/SNOP 来源见 material.base
2. **Water** 已换宽表源 eos_311（ρ 2e-6~400 g/cc）；**Glass** 低温区（<116 eV）依赖外推；
   **Diamond/Cliquid** 见 ⚠（`knowledge/pitfalls.md`）
3. **Ne** 已删退化子表（77 群）；**KrCheck** 用气体密度（3.749e-3 g/cc）
4. **Fe/Cu/W** 1D 拆分表初始电子能量含微小负偏移（官方表固有，不影响守恒）

## 5. 延伸阅读

- `MULTI-2D_材料库清单.md`（一手总账，随迁移持续更新）
- `Multi_BACK_材料不透明度映射表.md`（187+9 条源映射）

## 6. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
| 2026-08-14 | AlFEOS 入库（77→78；FEOS 系列首个全套多群） | claude |
| 2026-08-14 | AlFlash 入库（78→79；FLASH IONMIX4 系列，无冷曲线仅热等离子体） | claude |
