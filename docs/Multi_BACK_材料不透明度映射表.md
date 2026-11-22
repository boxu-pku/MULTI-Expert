# Multi_BACK 材料 → 不透明度文件映射表

> **2026-08-14 更名注记**：本表按 Multi_BACK 原始命名记录；本库已纠正 SiO2 族命名——Multi_BACK 的 "Quartz"（2.204 熔石英玻璃）现名 **Silica**，"Silica"（2.65 α-石英）现名 **Quartz**。详见《MULTI-2D_材料库清单.md》§〇a。

> 来源：`$MULTI_LIBS/newmulti/Multi_BACK/matter++/material.base`（187 条记录）+ `material.user`（9 条）。
> 由 2026-08-11 系统解析生成。同一材料的多个 MID 变体只保留代表条目。
> 与 MULTI-2D.2026.3 迁移状态的对照见最右列。

## A. 多群不透明度表（真多群，辐射谱分辨）

### A1. CELIA 系列（mat_CELIA，1/20/100 群可选 + Zeff）

| 材料 | PLANCK/ROSSELAND | ZEFF | 备注 |
|---|---|---|---|
| C | C_1G / C_20G / C_100G (.PLANCK/.ROSS) | C.ZEFF | MID16-18 |
| DT | D_1G / D_20G / D_100G | D.ZEFF | MID19-21（借纯 D 表） |
| DD | D_1G / D_20G / D_100G | D.ZEFF | MID22-24（借纯 D 表） |
| H | H_1G（仅 1 群） | – | MID25 |
| C (SNOP 20群) | C_20GSNOP.PLANCK/.ROSS | C_20GSNOP.ZEFF | MID26 |
| DT (hyades EOS 版) | D_100G | D.ZEFF | MID1011 |

### A2. SNOP 系列

| 材料 | 文件 | 群数 | 备注 |
|---|---|---|---|
| Be | Be_40G.PLANCK/.ROSS/.ZEFF | 40 | MID27 |
| Be | opbe.Planck/.Rosseland/.Zeff | 40 | MID28（1997 老版） |
| Au | Au100PLANCK/ROSS/ZEFF(+EPS) | 100 | MID29/30（董云松计算） |
| Au | SNOP.PLANCK/.ROSS/.ZEFF/.EPS | 20 | MID100（MPQEOS 配套） |
| Ti | SNOP_LTE.Planck/.Ross/.ZEFF | 30 | MID309（**我们迁移的正是这套**） |
| Ti | SNOP_NLTE.Planck/.Ross/.ZEFF/.EPS | 30 | MID307（非 LTE） |
| Ti | Ti_Planck/Ti_Ross(+Ti_EPS) | 20 | MID303/305（张继彦 2011） |
| C | C_SNOPMPQeos/SNOP.* | 20 | material.user MID100001 |

### A3. Thermos 多群（MID4xxx 系列，43 元素）

统一命名 `X_Planck.dat / X_Rosseland.dat / X_Zeff.dat`（Thermos/mat_X/）：
H, He, Li, Be, B, C, N, O, F, Ne, Na, Mg, Al, Si, P, S, Cl, Ar, K, Ca, Sc, Ti, V, Cr, Fe, Co, Ni, Cu, Zn, Br, Kr, Mo, Pd, Ag, Xe, Nd, Sm, Gd, Dy, Ta, W, Pb, U
- W 另有细网格版 `W_Planck_Fine.dat/W_Rosseland_Fine.dat`（MID7074+）
- Au 另有多群版 `AuMG_*.dat`（MID7079+）
- 注：该系列部分条目 EOS 用理想气体或 hyades 表，迁移时我们统一用了真 EOS

### A4. 其他多群

| 材料 | 文件 | 备注 |
|---|---|---|
| Au | AU_op03p/r/z/e | MID9/10（0.3 μm 激光群结构，2026.3 自带） |
| Al | 1041_PLANCK/1041_ROSS | MID41（hyades 转换的单群均值文件，sgo） |
| Al | Al_PLANCK/ROSSELAND/ZEFF_multifs-1.2.dat | MID113 |
| Pb | Pb_Planck/Rosseland/Zeff.dat | MID1231（Thermos） |

## B. 单群平均不透明度（hyades opc 库，"One group"）

`opc_1xxx.dat` = (ρ,T) 网格 Rosseland+Planck 平均值（Planck 块全零=仅 Rosseland）：

| 文件 | 服务材料（MID） |
|---|---|
| opc_1022 | **Glass / Quartz / Silica**（1021-1024，SiO2 族共用） |
| opc_1031 | Polyethylene（1031） |
| opc_1032 | Polystyrene（1032/2032） |
| opc_1033 | Polyurethane（1033） |
| opc_1035 | Parylene（1035） |
| opc_1036 | Mylar（1036） |
| opc_1041 | Aluminum（1041-1044） |
| opc_1051 / opc_1052 | Gold（1051/2051/1052，均仅 Rosseland 块） |
| opc_1061 | Hydrogen（1061） |
| opc_1071 | Lithium（1071）；**6LiD（1211-1213）、LiH（1241）借用 Li 表** |
| opc_1081 | Beryllium（1081） |
| opc_1091 | Argon（1091/1092） |
| opc_1101 | Neon（1101） |
| opc_1111 | Copper（1111-1115） |
| opc_1121 | Tungsten（1121/2121）；**WC（1141）借用 W 表** |
| opc_1151 | Deuterium（1151） |
| opc_1161 | Alumina/Al2O3（1161/1162） |
| opc_1181 | Iron（1181）；**Stainless Steel（1362）借用 Fe 表** |
| opc_1191 | Helium（1191） |
| opc_1201 | Krypton（1201） |
| opc_1221 | Oxygen（1221） |
| opc_1251 | Nitrogen（1251） |
| opc_1281 | Molybdenum（1281） |
| opc_1291 | Nickel（1291） |
| opc_1301 | Dry-air（1301） |
| opc_1311 | Water（1311-1314） |
| opc_1344 | Carbon（1344）；**CD2（1171）、Diamond（1341）、液态碳（1342）、酚醛碳（1343）借用碳表** |
| opc_1371 | Xenon（1371） |
| opc_1391 | Silicon（1391/1392） |
| opc_1401 | Tin（1401/2401/1402） |
| opc_1422 | Titanium（1422） |
| opc_1451 | Magnesium（1451） |
| opc_1461 | Europium（1461） |
| opc_1481 | Calcium（1481） |
| opc_1491 | Silver（1491/2491） |

## C. 无不透明度（"Only EOS"）

Lucite（1034）、PVA（1037）、Pt（1261）、Teflon（1321）、HE（1331）、PBX-9502（1332）、Se（1381）、Ge（1411）、C8H7Br（1431）、BeO（1441）、Gd-hyades版（1471）、Epoxy（1501/1502）、B4C（1511）
——这些材料在 Multi_BACK 中也不能做辐射输运（与我们迁移状态一致）。

## D. 解析公式/简单表（理想气体配套）

`*_SIMPLE_PLANCK / *_SIMPLE_ROSSELAND`（AL/AU/DT/C/BE 等，MID1-8/12-15/301-302）、AU_WorkOp_Ross（WorkOp 拟合单群）、Vacuum_Opacity.dat（真空占位）。

## 与我们 MULTI-2D.2026.3 迁移的对照

| Multi_BACK 用法 | 我们的迁移 | 一致性 |
|---|---|---|
| Ti → SNOP_LTE 30 群 | 同（Ti_LTE.*） | ✔ 完全一致 |
| 元素 → Thermos 多群 | 同（X_Thermos.*） | ✔ 完全一致 |
| DD/DT → 借 CELIA 纯 D 表 | 同（DD/D 均借 D_20G） | ✔ 一致 |
| CH → 借 CELIA 碳表 | 同（CH_CELIA = C_20G） | ✔ 一致 |
| SiO2 族/聚合物/水等 → opc 单群平均 | **未迁移**（当时误判为 T-only） | ⚠ 可补齐（opc→sgo 转换） |
| LiD/LiH 借 Li 表、SS 借 Fe 表、WC 借 W 表、碳族借 C 表 | 未做借用 | ⚠ 可按同样借用策略补齐 |
| Lucite/PVA/Pt/Teflon/HE/PBX/Se/Ge/C8H7Br/BeO/Epoxy/B4C 仅 EOS | 同（EOS-only 登记） | ✔ 一致 |
