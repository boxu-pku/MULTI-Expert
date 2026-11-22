# FEOS/AQUA 水表 1D 算例崩溃：冷端负 Pe + 不透明度低温外推 → 辐射求解奇异

**日期**：2026-08-14
**状态**：已确认机制并修复（算例侧 inegpre=1 + 算例内 tempmin=0.02 eV）

## 症状

WaterFEOS / WaterAQUA 的 1D Hugoniot / 加热算例在早期或左边界自由膨胀区崩溃：

```
ERROR in subroutine tridia
      singular matrix found in            1 (或 2)
```

（m150304 solve3 → tridia，辐射-电子耦合 2×2 块求解零主元；
也有变体：dt 塌缩到 1e-20 爬行不死。）

## 根因（两个独立因素叠加）

1. **冷端电子压强为负是源生物理**：FEOS 水表在 (ρ=1 g/cc, T≤0.3 eV)
   Pe ≈ −1.95 GPa（分子成键能挂在电子通道，data.txt 实测 Pe=−1.95142 GPa @291 K，
   Pi=+1.91 GPa，Ptot≈0）；AQUA 拆分的 EleTab 电子表冷端同样为负。
   **`inegpre=0`（"force positive Pe"）把 Pe 钳到 0 造成拐折**，
   PdV 做功项把边界单元 Te 一路打到 tempmin(1 K)。
2. **借用不透明度表 opc 1311 的 T 下限 = 1 eV**：代码对 log10(κ) 做
   log-log 外推，T<1 eV 时 κ 按 ~T^5.4 暴跌，Te=8.6e-5 eV 时
   κ_ross→1e-18 cm²/g → 辐射扩散系数 →~1e33（实测矩阵元 ±5e33）→
   2×2 块 [[D,−D],[−D,D]] 精确奇异（零主元）。

旧 Water 表（eos_311）不崩的原因：其电子表 T 下限 0.025 eV
（Te 塌不到 κ 暴跌区），且冷端 Pe 仅 −0.37 GPa（钳正拐折小 5 倍，侥幸存活）。

## 修复（算例侧两步，缺一不可）

1. `inegpre = 1`（允许负 Pe——它是源生物理，转换已验证与 data.txt 一致）；
2. 算例内编译的 `multi.f95` 打 tempmin 补丁：
   `tempmin = 0.0000861` → `0.02`（232 K）。
   Te≥0.02 eV 时 κ≥6e-6 cm²/g，扩散刚度低于 1/dt 一个量级以上。
   **注意：RUN 里 `cp -s` 建的是符号链接，先 `rm multi.f95` 再 `cp` 真拷贝
   然后 sed，绝不要直接改符号链接**（见 [[case-multif95-symlink-contamination]]）。

已否决的替代方案：EOS 表 T 下限裁剪到 0.025 eV（T75/T5 仍崩，且损
AQUA 行星温区价值）；更高裁到 0.1 eV（E0 参考态过热，AQUA 失去意义）；
改共享 opc 表（伪造数据，禁）。

**物理论证**：tempmin=0.02 eV=232 K 远低于算例一切相关温度
（初始 300 K 即 0.0259 eV），只影响自由膨胀边缘的 negligible 能量区。

## 适用范围

任何**冷端 Pe<0 的 EOS 表**（FEOS 分子材料：水、可能其他化合物）
+ **借用灰体不透明度**的 1D 算例。FEOS 石英系（QuartzFEOS/SilicaFEOS）
未触发：其电子表 Cv 结构不同、且驱动下波后区域始终较热。
排查顺序：先看崩溃单元 Te 是否打到 1 K，再查 Pe 符号与 opc 外推。

## 相关

[[two-temperature-sloshing]]（另一时间步振荡问题，dttevar/dttivar 限幅）
[[case-multif95-symlink-contamination]]（算例内调试污染模块源码）
