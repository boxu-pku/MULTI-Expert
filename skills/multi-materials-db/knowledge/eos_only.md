---
title: 仅 EOS 材料（9 种）与无法迁移材料（4 种）
skill: multi-materials-db
category: reference
source_anchors:
  - MULTI-2D_材料库清单.md §1.3-§1.4
  - Multi_BACK_材料不透明度映射表.md §C
doc_ref: "MULTI-2D_材料库清单.md §1.3, §1.4"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 仅EOS
  - 无法迁移
  - 明细
---

# 仅 EOS 材料（9 种）与无法迁移材料（4 种）

## 1. 仅 EOS 材料（清单 §1.3）

Multi_BACK 中也无不透明度（"Only EOS"，映射表 §C）；**2D 流体/EOS 可用，辐射输运不可用**
（`Material_mig.r` 中这些函数 `opafun=*`）。按约定无 1D 验证算例（批次2 机器验收 ACCEPT 30/30：格式+注册）。

| 材料 | 网格 | 材料 | 网格 |
|---|---|---|---|
| Lucite 有机玻璃 | 73×256 | BeO 氧化铍 | 76×128 |
| PVA | 73×128 | Teflon 特氟隆 | 64×128 |
| Pt 铂 | 101×128 | HE 炸药 | 100×128 |
| C8H7Br 溴代塑料 | 64×128 | PBX9502 炸药 | 100×128 |
| Epoxy 环氧 | 66×256 | | |

文件：`r94/mat_<X>-1.0/<X>_eos`；2D 函数 `Material<X>()`（Material_mig.r）。
B4C 在 Multi_BACK 也是 Only EOS（映射表 §C），本项目未单列。

## 2. 无法迁移材料（清单 §1.4）

**Ca、Nd、Ge、Se** —— hyades 库中对应 EOS 文件缺失（仅有 Thermos 不透明度）。
如需这四种：可用 FEOS 生成 EOS 再经 EOS-tools 转换（清单 §1.4 注）。
（注意：映射表 §C 中 Se/Ge 也列为 Only EOS——即其不透明度在 Thermos 有、EOS 无。）

## 3. 使用建议

- 仅 EOS 材料做**纯流体**或外挂自定义不透明度模型
- 辐射输运需求优先考虑全套材料或单群 opc 材料
- 新材料需求走 `multi-material-migration`（先查 Multi_BACK 资源分级，迁移指南 §4）

## 4. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
