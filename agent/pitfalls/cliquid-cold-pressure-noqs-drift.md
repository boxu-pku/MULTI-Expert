# Cliquid 表冷压非零 + iquiet=0 的后表面漂移（2026-09-10，route 3 S3/S4）

## 现象

Cliquid（BACK 1342 液碳表）在 ρ=3.51 g/cc、0.0257 eV（298 K）下**冷压
非零**：iqiuet=0（强度算例口径）时整个碳靶从 t=0 被冷压推动，后界面
~1 km/s 漂移——叠加在前驱特征（dV1~1 km/s）同量级上。inegpre=1 治不了
（那是负压钳零路径，这里是正冷压）。100 μm 纯 Cliquid 板 20 秒内后界面
即到 1.02 km/s；H2O 多层靶表现为 +0.7 → 回拉 −0.5 → 前驱 → 主升的
复合早期曲线。

## 规则

1. 需要干净冷固体的算例（前驱测量、单元测试）用 **Diamond 表**
   （BACK 1341，3.51/298K 冷压≈0，Vrear<3e-4 km/s 直到波到达）。
2. 必须用 Cliquid 世系时（忠实 BACK 对照），特征检测**锚局部基线**
   （前驱起点前的回拉平台），不用曲线开头的全局中位。
3. Diamond 表冷态 c_b≈16.1 km/s（实测），比 validation Hugoniot 拟合
   截距 c0=9.69 硬 ~60%——**c_b 不要引 Hugoniot 截距**，用弱驱动无强度
   例实测（slab_test/A_weak_nostrength 范式）。

## 关联

`work/visar_precursor_program/FEEDBACK.md` §R3.2/§R3.3；
无 QS 对末速的系统性影响（−1.6 km/s，归因对照 13.08 vs QS 15.64）。
