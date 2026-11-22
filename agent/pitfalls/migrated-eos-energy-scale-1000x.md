---
title: 迁移 EOS 表能量轴整体膨胀 ×1000（J/g 与 J/kg 混淆），温度响应不可用
category: 表加载
severity: 严重（物理结果错误但能跑、能量守恒查不出）
first_seen: 2026-08-13
last_verified: 2026-08-13
verifier: claude
status: resolved（1D + 2D 全部修复 2026-08-13；2D 迁移材料已可链接）
tags:
  - EOS
  - IEOS
  - 单位换算
  - e0
  - 冷曲线
  - 热力学一致性
  - hyades
  - Thermos
source_anchors:
  - work/eos_opacity_tools/split_ieos_table.py:L148
  - MULTI-2D_材料库迁移指南.md §8-9（2026-08-10 压力单位事故）
---

# 迁移 EOS 表能量轴 ×1000 膨胀

## 现象

用受影响材料的 1D 算例中，**压缩/冲击后的物质温度恒为 ~0**（T 被钳在表冷点），
而密度、压力、激波走时完全正常。能量守恒误差也能通过（错误是表内自洽的标度，
不影响守恒律）——**验证算例的 B1-B6 全部查不出此问题**。

实例：CH-Al-SiO2 辐射驱动算例中 14 Mbar 压到 9.9 g/cc 的 SiO2 壳层 Te=Ti=0.000；
QuartzCheck 100 eV 驱动下全区 Te≈0.03 eV。

## 判定方法（热力学一致性检查，PdV 测试）

沿表自身的冷压列做 ∫P dV 梯形积分，与 e0 列的密度差比较：

```
比值 = |e0(3ρ0) − e0(ρ0)| / ∫[ρ0→3ρ0] P_cold dV
```

- 比值 ≈1：表正常（Fe 0.94、CH 1.00、Ti 0.92）
- 比值 ≈1000：能量轴膨胀 ×1000（病态）

## 根因

hyades/SESAME 源表（erg/g）→ MULTI IEOS（Mbar·cm³/g）的**手工构造转换链**
把能量放大了约 ×1000——erg/g→J/g 应为 ×1e-7，疑用了 erg/g→J/kg 的 ×1e-4
（每克/每千克混淆，恰差 1000）。与迁移指南 §8-9 记载的 2026-08-10 压力单位
事故（dyne/cm²→MPa ×1e-7 误为 ÷1e11）同批同性质。

证据（Quartz, SESAME #7386 = eos_23.dat）：
- 源表冷能 E(2.204 g/cc, Tmin) = -9.411e8 erg/g = -9.411e-4 Mbar·cm³/g
- 迁移表 e0 = **-0.9411** Mbar·cm³/g —— 尾数相同，恰好 ×1000
- 压力列转换正确（源 6.51 Mbar @3ρ0 = 迁移表 6.51 Mbar）
- 源表自身热力学自洽（PdV ≈ ΔE ✓，比热 ~0.1-0.4 Mbar·cm³/g/eV 合理）

## 影响范围（2026-08-13 全库 PdV 审计，tables/*_eos_e）

**病态（×650~1100）41 张**：Quartz、Silica、Glass、Water、PE、PS、PU、Mylar、
Parylene、Cphenolic、Diamond、Cliquid、CD2、LiD、LiH、Al2O3、WC、SS、
H、D、He、Li、N、O、Ne、Ar、Kr、Xe、Mg、V、Ni、Zn、Mo、Ag、Sn、Ta、Gd、Pb、U、Eu
（即 hyades 族 21 种 + 大部分 Thermos 迁移元素表）

**正常（比值 0.7~1.5）**：CH、DD、Ti、Fe、Cu、Si、W、BE、SiO2wk12、SiO2wk14、
及全部 _wk 系（BN/Be/C9H10/CH2/Fe/LiF/Si_wk）

**另行异常**：Air、C_wk、H_wk（冷压列整段为负，PdV<0）；C8H8_wk（比值 7，
e0 差为负——清单已标 ⚠）

**未受影响**：自带老表（Al、Carbon、DT、CPC88——2009 年前 R.Ramis 原生）。

## 修复方向

1. 源数据是好的（SESAME/QEOS 等），重新转换即可：当前 EOS-tools 原生
   读-写链（erg/g→J/g ×1e-7、J/g→Mbar·cm³/g ×1e-5）书面正确，但
   `basefunctions/read_hyades.py` 的严格长度校验拒读 eos_23.dat
   （声明 5966 实得 5970，含 4-5 个 0 填充），需加容忍补丁后重转。
2. 应急：受影响表的 de/e0 两列同除以 1000 可近似修复（反演重网格引入的
   残差在低能端 ~×1.5 量级，高能端好）——正式修复仍应走源表重转。
3. 修复后必须重跑对应 Check 算例并用**物理量绝对值抽查**（如激波温度
   vs Hugoniot 数据）验收——能量守恒查不出此类错误。

## 2D 侧 + 1D eeos 约定修正（2026-08-13 完整收尾）

**2D 总表（mat_\<X\>-1.0/\<X\>_eos）此前从未被修复**，仍是 ×1000 病态（PdV≈1000）。
2D 经 `Mat2013_LoadIEOS(eosfile)` 按路径运行时读表，故**替换文件内容无需重编译**。
修复：`work/eos_opacity_tools/rebuild_eos_2d1d.py` 把权威源
`work/eos_rebuild_20260813/<X>_electron.multi`（= reconvert 修正总量的持久副本，
含 H/D/Parylene 折叠裁断）安装为 2D 总表（marker=1.0），旧表备份到
`mat_<X>-1.0/_bak_x1000/`。修复后 PdV 全部回到 0.6–1.1。

**附带发现并修正的 1D eeos 约定回退**：reconvert 把 hyades **总量**写进了电子槽
（`hyades.py` table_role='electron' 时 `pe_mpa=raw_pressure`，`multi.save` 原样写出），
而原始迁移走 `split_ieos_table` 产出 total−ion。故 reconvert 安装的 `tables/<X>_eos_e`
= 总量（非 total−ion）。对 H/D（离子能 ≈ 电子能）使 1D Te 偏低约 2×，CH/聚合物
20–30%，金属 <5%；2D 不受影响（运行时 `Mat2013_EleTab` 自己拆分）。
修正：对同一权威总量跑 `split_ieos_table`，重派 `_eos_e`=total−ion、`_eos_i`=理想离子
（id 沿用 `elem_ids(Z)`，data.in 无需改），旧表备份到 `tables/_bak_totalconv_20260813/`。
重跑 41 Check：39/41 <1e-4（Cliquid 3.2e-4 维持 ⚠，Air 9.4e-5 过）。

**2D 迁移材料启用**：`Material_mig.r` 与 `Material.r` 在 `Material{CH,Cu,Fe,W}0`
四处全局符号冲突（CH=CHOQG、Cu/Fe/W=MPQEOS.i301，均非病态源；迁移批次本意
只是为它们补 1D 表）。`gen_material_functions.py` 加 `SKIP_COLLISION` 跳过这 4 个
（保留 Material.r 原生版），重生成后 `x.2.compile Material_mig.r` 增量重编 lib.a。
链接测试：同时引用 MaterialAl（原始）+ MaterialTa（迁移）成功生成 multi2d，无冲突。


## 锚点

- 审计脚本逻辑：本文件"判定方法"节（PdV 测试）
- `work/eos_opacity_tools/split_ieos_table.py:L148` — e0 原样复制（拆分工无责）
- 源表：`Multi_BACK/matter++/hyades/sesame/eos_23.dat`（QUARTZ SESAME #7386）

## 预防

- 新材料/重转表验收增加 PdV 一致性检查（本文件"判定方法"）与激波温度抽查。
- 相关踩坑：`pressure-unit-confusion.md`（2026-08-10 压力单位事故）

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-13 | 初始创建 | claude |
| 2026-08-13 | 2D 总表修复（rebuild_eos_2d1d.py，41 张）+ 1D eeos 约定修正回 total−ion + Material_mig.r 冲突解除并链接验证 | claude |
