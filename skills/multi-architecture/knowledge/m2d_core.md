---
title: 2D 核心模块族 — hydro 数据结构、M20_Step 求解流程与各物理模块
skill: multi-architecture
category: internals
source_anchors:
  - r94/m2d-core-9.1/Hydro.r:L74-L141
  - r94/m2d-core-9.1/M20_Step.r:L63-L139
  - r94/m2d-core-9.1/M20_Hydrodynamics.r:L98-L153
  - r94/m2d-core-9.1/M20_Transport.r:L82-L176
  - MULTI-2D_梳理文档.md §4-§5
doc_ref: "MULTI-2D_梳理文档.md §4, §5"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - m2d-core
  - hydro
  - M20_Step
  - 物理模块
  - User.r
---

# 2D 核心模块族

> **TL;DR**：m2d-core-9.1 是总控制包，定义核心数据结构 `hydro` 与总驱动 `M20_Step()`；物理计算分散在 hydro2（流体）、radia（辐射）、heat（热传导）、ray（激光）、hib（重离子束）、ALE19（投影）、geometry（拓扑）、malla（网格）。

## 1. 模块清单（梳理文档 §4.1，info 取自各 MODINFO）

| 模块 | 作用 | 关键文件 |
|---|---|---|
| `m2d-core-9.1` | 总控制包；hydro 结构 + M20_Step 驱动 | `M20_Step.r`、`M20_Hydrodynamics.r`、`M20_Transport.r`、`M20_RayTracing.r`、`M20_HIB.r`、`M20_Project.r`、`Hydro.r`、`Material.r` |
| `m2d-hydro2-7.0.4` | MHD 拉格朗日流体（非结构网格） | `M19_HydroAcc.r`、`M19_LorentzF.r`、`M19_ThermalF.r` |
| `m2d-radia-8.0` | 辐射输运（扩散风格） | `M19_Radia.r`、`M19_I_mesh.r`、`M19_I_radia.r` |
| `m2d-heat-7.0` | 电子/离子热传导（Spitzer + 自由流限制） | `M19_Heat.r` |
| `m2d-ray-7.0` | 激光光追（含折射） | `M19_ray2d_init.r`、`M19_I_ray_trace.r` |
| `m2d-hib-7.0` | 重离子束沉积（无折射光追 + 射程表） | `M19_HIB.r`、`M19_I_Coral.r` |
| `m2d-ALE19-8.0` | ALE 投影（二阶保守） | `M19_ALE_main.r`、`M19_I_ALE_*.r` |
| `m2d-geometry-7.0` | 由 ma 三角剖分构建拓扑表（tn/tw/wn/wt/tt/bw） | `M19_Geometry.r`、`NewTopo.r` |
| `malla-6.0` + `triangle` | 网格生成（均匀/几何级数布点、弧线、自动三角剖分） | — |
| `matter-3.1` | 物态接口（Mat2013 族） | 见 multi-eos-format skill |

## 2. hydro 数据结构（`Hydro.r`）

`Hydro(topo,gmode,xsymmetry,ntemp)` 创建（`Hydro.r:L141`）：

- 几何：`topo`、`gmode`（1=平面XY，2=轴对称ZR）、`xsymmetry`、`ntemp`（1/2 温度模型）
- 状态量：`h.p`（节点位置 `L74`）、`h.v`（速度 `L77`）、`h.E` 或 `Ee+Ei`（内能 `L79`）、
  `h.mass`（每材料三角形质量 `L85`）
- 导出量：area/vol/rho/tmass/nmass
- EOS 量：`h.P`（`L108`）、`h.T`（`L109`）或 Pe/Te/Pi/Ti；c²/am/zm/zeff/ne/ecf
- 附加量：TR（辐射温度）、lambda（自由程）、depo（束沉积）、rays（光线轨迹）
- struct 赋值示例：p/v `L163-L164`、E `L166`、mass `L173`、P/T `L188-L189`

## 3. M20_Step 时间推进（`M20_Step.r:L63`）

```
M20_Step(control,hydro)                              L63
1. HydroEOS(hydro_save)                              L72
2. (control.plasma → HydroIonization/HydroCollfreq)
3. while(1) 重试循环:                                L79
   a. control.plasma → M20_Relax                      L84（电子-离子温度弛豫）
   b. control.fusion → control.fusion.f(...)            （用户热核反应包）
   c. control.hydro → M20_Hydrodynamics               L93
   d. control.hib → M20_HIB                          L101
   e. control.ray → M20_RayTracing                   L109（折射光追）
   f. control.transport → M20_Transport              L116（辐射+热传导）
   status 最大值 > 1 ⇒ dt 减半重试（hydro=copy(hydro_save)，L137-L139）；
   超 32 次减半 → STOP                               L132
```

各子步要点（梳理文档 §5.2）：
- **M20_Hydrodynamics**（`M20_Hydrodynamics.r:L146`）：调 hydro2 的加速度子程序；
  控制参数 max_cfl=0.5/max_var=0.5/kq1=1/kq2=0/qmode=3（默认 `L98-L102`，读取 `L151-L153`；
  CFL 判定 `L277-L278`）
- **M20_Transport**（`M20_Transport.r:L106`）：freepath 回调（`L161`）→ M19_Radia（`L163`）；
  heatcond 回调（`L172`）→ M19_Heat（`L176`）；nphis 角度离散（默认 `L84`）、
  Tmaxvar 温度变化限制（`L82`）
- **M20_Project** + ALE19：网格扭曲超阈值时二阶保守投影回参考网格

## 4. 典型 User.r 结构（梳理文档 §5.3）

```r
entry multi2d()
{
   hydro    = ...;      # malla + NewTopo + Hydro + HydroAdd 构造
   control  = struct();
   struct(control,<hydro>,    M20_Hydrodynamics_Control());
   struct(control,<transport>,M20_Transport_Control());   # 按需
   struct(control,<ray>/<hib>/<plasma>/<fusion>/<project>, ...);
   hydro1 = hydro;
   while( hydro1.time < tmax ){
      hydro2 = M20_Step(control,hydro1);
      if(M20_Project_Test(hydro2,hydro,control.project))   # 仅 Euler/ALE
         hydro2 = M20_Project(hydro2,hydro,control.project);
      HydroOutputAtTimes(hydro1,hydro2,times);
      hydro1 = hydro2;
   }
}
```

快照输出：`HydroOutput`/`HydroOutputAtTimes` 写二进制文件（命名为时间值，如 `0`、`1.2e-9`）
+ 同名 `.d` 描述文件。自定义输出：`m2d_write("name", array)` + `hydro.output='myoutput(1)'`
（梳理文档 §9-4）。

## 5. 常见错误

| 错误 | 原因 | 修复 |
|---|---|---|
| `M20_Step: more than 32 time step reductions` | 某子步持续失败（CFL/越界/沉积异常） | `M20_Step.r:L132`；查 output 定位子步 |
| dt 持续减半不前进 | 物理状态越出表范围/CFL 过严 | 查表覆盖；调 max_cfl/max_var |
| 快照变量看不到 | 变量未写入 .d 描述 | 用 m2d_write 注册（梳理文档 §9-4） |

## 6. 延伸阅读

- `MULTI-2D_梳理文档.md §4-§5`（模块与流程详述）
- `knowledge/compile_chain.md`、`knowledge/cases_and_gui.md`
- `multi-opacity/knowledge/freepath_mechanism.md`（输运回调细节）

## 7. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
