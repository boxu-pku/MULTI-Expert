# iquiet=1 闸死电介质样品的激波传入 + FEOS 表冷态不稳定支（2026-09-15，double_shock 立项试点）

## 现象一：quiet start 闸死冷电介质传波

`iquiet=1` 的判据是"界面两侧细胞 Te/Ti 均未超过 tquiet 才冻结"，解冻为
单向闩锁（m150304.f95:985/1096）。**冷压缩几乎不升温的材料**（石英、hBN
等电介质：电子简并 + 声子大热容，Mbar 级冷压缩下 Te 仍 ~0.05 eV）被激波
压着也解不了冻：Al/CH/Quartz(hBN) 激光靶里 base 侧 6–12 Mbar 压在界面上
~5 ns，样品 ρ/P 纹丝不动，7.6 ns 后才靠辐射/传导缓慢"解冻波"传入。
visar 系列早有记载（"QS would gate the precursor"），对透波类问题是硬伤。

## 现象二：QuartzFEOS 离子表冷态附近负模量支

`iquiet=0` 后暴露：QuartzFEOS_eos_i 在 ρ<2.65、Te~0.03 eV 区域
P_ion 随膨胀上升（dP/dρ<0）。界面初始 ±0.005 Mbar 失配 → 第一格微膨胀 →
PI 反增至 ~0.15 Mbar → 粘性耗散自热（TE→1.8 eV 是后果）→ 假前驱波
（0.1–0.2 Mbar 量级）射入冷样品，把冷石英压到 ρ=3.3 而 TE 仍 0.05
（表冷压缩支 P 异常平坦）。hBNHub 的张力平台是构造性稳定（有界振荡
~0.1 Mbar 量级），无此失控，但 iquiet=0 下同样产生假波。

## 规则

1. 透波/冷介质传入类算例一律 `iquiet=0`；激波判据用 **PT > 0.25 Mbar**
   阈值（假波 ~0.2 Mbar 以下、真激波 ≥1 Mbar，干净分离）。
2. QuartzFEOS / hBNHub 冷态初值用 **te0=ti0=0.1 eV**（两表 Hugoniot 验收
   基线值，1160 K 对 Mbar 激波物理可忽略），避开不稳定支。
3. 多材料混装时 N_Thermos 多群与 CELIA/SNOP 群结构并集冲突
   （`opa: frequency not found in tables`）——hBN 不透明度改借灰体
   （Diamond_OPC 1344，Z/A 同构 6/12，碳代理先例），Al/CH 保持
   preheat 已验证组合不动。
4. 探测波前用**阈值穿越 foot**（对平坦极大值稳定）；追及时刻 t1 用
   **foot 轨迹拐点**（波速突增 ≥1.5× 持续 3 帧），argmax 脊线在平坦
   压力平台上抖动会假触发。
