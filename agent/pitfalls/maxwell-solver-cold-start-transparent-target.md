# pulse_maxwell 冷固体靶启动：碰撞频率爆炸 → 靶"透明" → 深部伪沉积 → 辐射矩阵奇异

**日期**：2026-08-20（H2O_multi_layer 战役）
**状态**：已确认机制，算例侧规避（改用 pulse_wkb）

## 症状

C(5μm)/C(25μm)/Au(1.8μm)/Water(30μm)/C(50μm) 五层冷靶（te0≈0.025 eV，
quiet start），351 nm 激光从左入射，`&pulse_maxwell` 全波求解器 +
表格脉冲，开辐射（iradia=1）：

```
     1  0.00000E+00  0.10000E-09  0.27816E+01 var fail
 VARDBG mode1 cell  546 xi 2.53E-02 xf 2.3657     <- Water 第 2 个单元
     3  0.19545E-10 ... 
 ERROR in subroutine tridia
      singular matrix found in            1
```

第 3 步即崩；iwctrl=0/1 无差别。消融定位：iradia=0（激光直沉）不崩
但首步同样出现 546/547 单元加热（0.0253→0.29 eV）；关激光开辐射不崩。
→ 崩溃需要 **Maxwell 沉积 × 辐射群耦合** 同时在场。

## 根因链

1. 冷态 Te=0.025 eV 下 Spitzer 型碰撞频率 ∝ Te^-1.5 天文级巨大，
   `collfreq` 归一化 ab=ν/ω ~ 1e6。
2. `depos()` 特征矩阵法里复折射率 ep = 1 − ro/(1+i·ab)：ab 巨大时
   ro/(1+i·ab)→0，等离子体响应被屏蔽，**超密冷固体近乎透明**
   （物理图像：ν≫ω 时电导率 σ=ne²/mν → 0）。
3. 波穿过整个 30 μm C 层直抵 Au/Water 界面，阻抗突变处反射成驻波，
   flux(l)−flux(l+1) 在界面单元（~546）产生伪沉积。
4. 伪沉积经 qe=d·wa(kgroup) 注入辐射群方程；冷靶灰体 OPC 在 T<1 eV
   的 log-log 外推 κ~1e-4 cm⁻¹ 近乎透明（见
   [[water-cold-pe-and-opc-lowt-singular]] 同一外推），辐射矩阵元
   ~1e18 量级，前向消元灾难性抵消 → solve3/tridia 零主元。

## 规避（已验证）

**冷固体靶激光算例用 `&pulse_wkb` 不用 `&pulse_maxwell`**：
WKB (`atenua`) 从真空侧找临界面，全程超临界时全部能量沉在最前沿
单元，冷启动安全；2015CPC 用同套 Au CPC88 表 + wkb + iwctrl=1 对照
Ramis 1988 验证通过。H2O_multi_layer 换 wkb 后 25 ns 完整跑通
（error=5e-10）。

pulse_maxwell 仅在**已热的欠密等离子体**（临界面已形成、ν/ω 正常）
场景可信；BACK 的 FSPULSE 有自己的低温修正开关
（IsIncludeLowTemperatureCorrection），m150304 无对应物。

## 排查备忘

- Maxwell 路径冷启动的可疑指纹：VARDBG 加热单元出现在**深层材料
  界面**而非前表面冕区。
- 消融实验顺序：iradia=0（隔离辐射）→ 关激光（隔离激光）→ 换激光模型。
- pulse_shape 表 ttab/ptab 上限 100 点；分段线性表用拐点压缩
  （161 点 → 8 拐点精确复现）。
- itype=4 表格脉冲在最后一点之后**保持末值**（`power=ptab(ntab)`），
  需要截止就在表尾补一个降到 0 的点。

## 涉及

- 源码：r94/MULTI-IFE-2015/m150304.f95 `laser_maxwell`(L1617)/
  `depos`/`collfreq`
- 算例：cases/H2O_multi_layer/（data.in 头部注释记录了完整转换映射）
- 源配置：cases/H2O_multi_layer/milot_laser_h2o_30um_quiet_start.case

## 相关

[[water-cold-pe-and-opc-lowt-singular]]（OPC 低 T 外推 κ 暴跌的另一引爆路径）
[[tempmin-below-eos-floor-tridia-crash]]（tridia 奇异的 EOS 侧根因）
