# IONMIX4 铝表无冷曲线 → Hugoniot 不可用

> 日期：2026-08-14 ｜ 状态：已确认 ｜ 触发材料：AlFlash（FLASH al-imx-003.cn4）
> 关联：[[ionmix-preheat-shell-merger]]

## 症状

AlFlash 的 6 档 Hugoniot 算例全部正常完成并提取，采信点 Us 相对
SESAME/FEOS/Celliers 偏差 **~59%**；表自洽 Hugoniot 线对理论线 **~54% 偏软**。
而 AlFlashCheck（100 eV 辐射浴烧蚀）能量误差 1.5e-10，完全正常。

**决定性证据（2026-08-14 复核）**：直接读源 cn4 数据反解 Hugoniot（完全绕过
MULTI 转换与提取环节），同一工具对 AlFEOS（库内 FEOS 表，已知正确）得 ≈2.4%，
对 AlFlash 得 ~54% 偏软（同 Up=2.0 时 Us 3.65 vs SESAME 8.00 km/s）。
证明**工具无误、表真实偏软**。

## 根因

`al-imx-003.cn4` 的**温度网格从 1 eV 起**，不含铝的固体/液体冷曲线。
在 ρ0=2.7、T=1 eV 处 P=0.098 Mbar ≈ 纯理想离子热压（nkT = 9.6 GPa），
冷压贡献为零；1 eV 等温线声速 ≈1.9 km/s（真实铝 ≈5.3 km/s）。

冲击 Hugoniot 态需要刚性冷曲线提供压缩态压强。缺冷曲线 → 表 Hugoniot 波速
系统性低 ~54%。这是**源表适用范围**问题，不是转换错误：
S4 全网格对拍证明 MULTI 表对源 cn4 保真（P50~2e-4）。

> 注：初版记录"90% 偏软 + Us<Up"是 `compute_table_hugoniot.py` 用 T0=0.1 eV
> （表 T 下限 1 eV 之外）反演导致的假象；T0 改 1.0 eV 后 Us>Up 物理正常，
> 正确偏软量 54%。

## 与 PSFlash 的区别

PSFlash（聚苯乙烯）同为 IONMIX4、同样无冷曲线，但 PS 是聚合物、冷曲线弱，
Hugoniot 尚能压出（偏软 5–8%）；Al 是金属、冷曲线强，缺冷曲线直接失效。
**判定线索**：表 T 下限 ≥1 eV 且材料为金属 → 先算 1 eV 等温线声速，
远低于体声速即判定 Hugoniot 不可用。

## 判定方法

1. 读源表最低 T 行 (ρ, P)，看 ρ0 处 P 是否 ≈ nkT（纯热压、无冷压项）。
2. 从最低 T 等温线估声速 c=√(∂P/∂ρ)，对比材料体声速。
3. 用 `compute_table_hugoniot.py` 求表自洽线：若 Us<Up 或对理论线偏软 ≳50%，
   判定无冷曲线。

## 处理

- 本表**限用于热等离子体区**（T≳数 eV 的激光/辐射烧蚀），与 FLASH LaserSlab
  用途一致；固体冲击压缩场景不可用。
- 已在 `validation_cases/AlFlash/材料表信息.md` 记录为"⚠ Hugoniot 不可用"，
  不阻塞迁移（XCheck 辐射波路线验收通过）。

## 预防

- 迁移 IONMIX4/hyades 等表时，先查 T 网格下限是否 < 室温（含冷曲线）。
  T 下限 ≳1 eV 的金属表，Hugoniot 路线必先做表自洽线对理论线的预检。
- 冷曲线缺失不等于表坏——先确认目标物理场景是否落在表的有效域内。
