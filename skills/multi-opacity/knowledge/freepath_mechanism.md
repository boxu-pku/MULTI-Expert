---
title: 2D freepath/opafun 机制 — 调用链、解析拟合与查表两条路
skill: multi-opacity
category: internals
source_anchors:
  - r94/m2d-core-9.1/M20_Transport.r:L116-L176
  - r94/m2d-core-9.1/Material.r:L596-L605
  - r94/m2d-core-9.1/Material.r:L432-L437
  - r94/m2d-core-9.1/Material_mig.r:L11-L32
  - work/eos_opacity_tools/gen_material_functions.py:L53-L79
  - MULTI-2D_材料库迁移指南.md §7.3
doc_ref: "MULTI-2D_材料库迁移指南.md §2.1, §7.1, §7.3"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - freepath
  - opafun
  - 自由程
  - 拟合
  - Rosseland平均
  - Material.r
---

# 2D freepath/opafun 机制

> **TL;DR**：2D 辐射输运通过 `control.transport.freepath` 回调拿自由程 λ(ρ,T)[cm]；标准实现 `Material_Freepath` 逐材料执行 `mat.opafun`（r94 例程引用，如 `'freepath_Ti(2)'`）。两条供给路线：解析拟合式（标准）或 LoadMF 读单群表自写插值。

## 1. 调用链

```
M20_Step → M20_Transport(control.transport)          M20_Transport.r:L106
  freepath = control.freepath                        L116
  if(?freepath)  lambda = exec(freepath,[hydro,mid,rho,tmed])   L157-L161
  res = M19_Radia(...,nphis,lambda,external)         L163-L164
  （热传导另路：heatcond 回调 → M19_Heat              L172-L176）
```

标准 freepath 实现是 `Material_Freepath`（`Material.r:L596`），逐材料执行 opafun：
```
Material.r:L605
   l[index]=exec(mat.opafun,[r[index],t[index]]);
```

`nphis`/`Tmaxvar` 等控制参数：`M20_Transport.r:L82-L84`（默认）、`L113-L119`（解包）。

## 2. opafun 约定

- r94 例程引用写法 `'name(N)'`（单引号 + 参数个数）：`material.opafun = 'freepath_Ti(2)';`
- 函数签名 `(r, t)`：r=密度 g/cc，t=温度 eV，返回 λ [cm]
- λ = 1/(κ·ρ)，κ 单位 cm²/g（迁移指南 §7.3）
- 无不透明度的材料：`material.opafun = *`（辐射输运不可用；`Material_mig.r` 中 9 种 EOS-only 材料如此）

## 3. 路线一：解析拟合（标准做法）

形式：`λ = 10^a · T^s · ρ^r`（log10 λ = a + s·log10 T + r·log10 ρ）。

自带材料示例（`Material.r`）：
- Al：`L57-L61` — `l = 8.7e-09*t^2.5/rho^1.5;`
- Ti（首个迁移材料）：`L432-L437` — `l=10^(-10.0058)*t^2.4209/r^1.9189;`

迁移材料（`Material_mig.r`，56 个函数）的拟合式由
`gen_material_functions.py:L53-L79` 自动完成：
1. 读 Thermos/CELIA Rosseland **多群**表
2. 用 dB/dT 权重（`dBdT_group`，L46-L50）做群间 Rosseland 平均：
   `λ(T,ρ) = Σw / Σ(κ·w) / ρ`（L59-L68）
3. 对 log10 λ 做关于 (logT, logρ) 的最小二乘拟合（L69-L79）
4. 拟合系数与 rms（dex）写进函数注释，例 `Material_mig.r:L11-L13`：
   ```
   $$   log10(lambda[cm]) = -5.2312 + 1.0367*log10(T[eV]) + -1.4826*log10(rho[g/cm3])
   $$   fit rms 1.80 dex over T=[0.04,1e+05]eV, rho=[1e-06,1e+04]
   ```

**注意拟合误差**：rms 可达 ~1-2 dex（十倍级），只适合做灰体估算；精度敏感问题用路线二或 1D 校核。

## 4. 路线二：查表插值（高级）

迁移指南 §7.3：
1. 用 EOS-tools 把多群表聚合到 1 群（`--opacity-groups 1`；Rosseland 用 dB/dT 调和矩、
   Planck 用 B 算术矩），得 sgo 单群表
2. User.r 里：
   ```r
   data  = Mat2013_LoadMF(getenv("MULTI"):"/r94/mat_X/opac_1g.ROSS");
   tab   = data#2;          $ sgo 表: tab.lr, tab.lt, tab.lo (log10)
   $ 自写双对数双线性插值 my_opafun(r,t), 返回 10^interp 后 λ=1/(κρ)
   material.opafun = 'my_opafun(2)';
   ```
3. hyades opc 单群平均表（`tables/X_OPC.ROSS`）可直接这样用——
   它们本来就是 (ρ,T) 网格的平均不透明度（见 `knowledge/data_sources.md §3`）。

## 5. 常见错误

| 错误 | 原因 | 修复 |
|---|---|---|
| 辐射输运不生效 | opafun=* 或 freepath 回调未挂 | 检查 control.transport.freepath 与 material.opafun |
| λ 量级离谱 | 把 κ（cm²/g）当 λ 返回，忘除 ρ | λ=1/(κ·ρ)，迁移指南 §7.3 |
| 拟合式外推区结果错 | 拟合范围有限（注释里写了 T/ρ 区间） | 查看 `Material_mig.r` 函数注释的适用范围 |
| 想直接用多群表 | 2D 无多群消费者 | 走路线一/二 |

## 6. 延伸阅读

- `knowledge/overview.md`（模型对比）、`knowledge/data_sources.md`（表从哪来）
- `MULTI-2D_材料库迁移指南.md §2.1、§7.3`

## 7. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
