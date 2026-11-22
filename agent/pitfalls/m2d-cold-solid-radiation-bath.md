# 陷阱：2D 辐射浴驱动冷固体靶的数值崩溃（两个体系都中招）

**日期**：2026-11-13  **场景**：MULTI-2D（r94）建"辐射浴+冷固体多层靶"算例

## 症状

辐射浴（external 边界源）照冷固体（室温 0.0253 eV，表格 EOS）：
- **m2d-core-9.1（MULTI-2D.2026.3，M20_Step 体系）**：Tmaxvar=50/80 时表面温度每步
  +Tmaxvar 单向漂移（远超浴温平衡值），密度膨胀出 EOS 表 → NaN → 死亡；
  Tmaxvar=1e6 一步冲出表顶直接死锁。
- **m2d-5.1（newmulti/r94-2009，MultiLoop 体系）**：transport 首步 dtemp ~1e236 eV
  爆发、geister energy 雪崩。

## 根因（两重叠加）

1. **表 EOS 冷端 Cv→0**：SSI 更新 dtemp=(dQ+βgE)/(dEdT-α·dt·der_depo) 分母→0，
   温度变化发散，被 Tmaxvar 钳成每步 +Tmaxvar 的线性漂移，最终冲出 EOS 表。
2. **冷端 λ→0 的黑体发射系数爆表**：κρ∝1/λ→∞，Sn 里 (发射-吸收) 灾难性相消，
   depo 出现非物理巨值。
3. 加 λ 下限（≥0.1µm）不够——根源在 Cv。

## 对照事实

| 配置 | 结果 |
|---|---|
| M2D_Radia（浴+Au 理想气体，**解析 Cv 恒定**） | ✅ 正常 |
| M2D_ThinFoil/XG151（**激光驱动**+表格 EOS 冷靶） | ✅ 正常（沉积温和） |
| 浴+表格 EOS 冷固体（两个体系） | ❌ 全崩 |
| 1D m150304 同物理（decay wave 系列） | ✅（iquiet 冻结 + 联立隐式） |

**1D 的 quiet-start（iquiet/tquiet 冻结冷物质）就是为此设计的，2D 两个体系都没有。**

## 规避/修复方向

- 立即可用：**激光驱动**（burn 波照样产生激波+侧向卸载；见
  newmulti/r94-2009/cases/M2D_DiaRelease385）。
- 浴方案修复候选（未做）：给 2D 移植 quiet-start（boundary 钩子双向钳温度 +
  冻结 T<tquiet 单元的输运更新）；或 SSI 里 dEdT 下限保护；或换用温度
  下限更高的表。**修改 r94 库源码前必须 git 备份（死命令）**。

## 相关

[[m2d-core91-offaxis-grid-hang]]（离轴网格在 hydro+transport 组合下卡死）
