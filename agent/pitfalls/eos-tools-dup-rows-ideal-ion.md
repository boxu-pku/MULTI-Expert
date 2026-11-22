# EOS-tools 自适应网格重复行 + FEOS 离子低ρ平台（AlFEOS 迁移排障）

> 日期：2026-08-14 ｜ 状态：已确认 ｜ 触发材料：AlFEOS（FEOS mat 3717）
> 关联：[[feos-converter-layout-energyunit]]、[[multi-table-continuous-stream-format]]

## 症状

EOS-tools 转换的 1D 表跑 Hugoniot 算例时，t≈0.8 ns 处 **dt 坍缩卡死**：
output 中 `var fail` 反复出现且**不恢复**，dt→1e-17、时间冻结
（与 FEOS 双温 sloshing 的区别：sloshing 的 var fail 会自行恢复并推进）。

## 根因（两条独立缺陷）

1. **FEOS 离子表低 ρ 平台（致命）**：EOS-tools 直出的 FEOS 离子分量表在
   ρ≲0.1 g/cc、T≲0.35 eV 区 T(de) 呈平台（dlogT/dloge≈1e-6）——FEOS
   SoftSphere 离子模型在低密度低温下参考系非物理（Ei 为负且非理想气体行为）。
   自由膨胀区单元冷却落入该平台 → 温度反演失效 → dt 无关的 var fail → 卡死。
2. **EOS-tools 自适应能量网格重复行**：转换在 T=1e-3~0.1 eV 区产生几十处
   **完全相同的 (de, T, P) 行**（电子 49/离子 17 处；QuartzFEOS/SilicaFEOS 也有
   37/40 处但未致命）。零宽区间使相邻行导数 0/0，单元状态恰落于此时 var fail。

## 判定方法

- **双构型对拍**快速定位坏表：同一算例分别换 (a) 新电子表+stock 离子表、
  (b) stock 电子表+新离子表，前台跑 60 s 看 var fail 是否恢复/完成
  （`work/alfeos_migration/bisect_A|B/` 为模板）。
- 探针：读表画 (de, T) 逐密度响应，查 dlogT/dloge≈0 平台与 diff(e)==0 重复行。

## 修复（AlFEOS 实例）

1. **离子表换理想气体表**（库内标准约定，split_ieos_table.py 同款）：
   `T=de/((γ-1)·cte)`、`P=ρ·de/1.5`、`e0=0`，γ=5/3、cte=kB·Na/A（表单位 1e12 erg/g）。
   原表备份 `tables/AlFEOS_eos_i.bak_eostools_ion`。
   代价量化：表自洽 Hugoniot 对 FEOS 官方 .hug 偏差 0.09%→2.42%（P50），
   在原表致命（353% 离群+不可运行）与理想离子 2.42%（≤先例 3.5% 容差）之间，
   取理想离子。**注意**：FEOS 离子模型在高 ρ/高温区与理想气体几乎一致，
   代价集中在近冷曲线低压缩端。
2. **电子表去重**：删完全相同行（NE 512→463，零信息损失），
   备份 `tables/AlFEOS_eos_e.bak_dedup`；去重后 T(de) 全密度严格单调。
   近重复行（de 差非零、T 平）保留——先例同级可运行，试验确认步 1 var fail 自愈。

## 预防

- EOS-tools 转换 1D 表后**必做**：(1) `np.diff(e)==0` 重复行扫描+去重；
  (2) 逐密度 dlogT/dloge 平台扫描（尤其 FEOS 离子表低 ρ 区）；
  (3) Hugoniot 算例前排 60 s 烟测（单档前台，看 var fail 是否自愈）。
- FEOS 离子表默认可疑：FEOS 系列后续材料（hBN、H2O 等）迁移时先查低 ρ 平台，
  有则直接换理想离子表（库内通行约定，不视为降级）。
- var fail 计数本身不是病（QuartzFEOS 592 次仍完成），**是否自愈**才是判据。
