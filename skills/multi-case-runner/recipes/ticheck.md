# Recipe: 跑 TiCheck 验证算例（+ 出图）

> 场景：用户说"跑一下 TiCheck"。TiCheck 是首个迁移材料（Ti）的 1D 验证算例，
> 已通过完整验收（2026-08-10，用户人工确认 ✅）。
> 注意：**TiCheck 的产物（output/fort.10/PNG）是验收档案，永久保留**。
> 如只想"验证环境能跑"，建议克隆一个临时目录跑，避免覆盖档案产物。

## 1. 直接重跑（会覆盖 output/fort.10 —— 不推荐用于档案算例）

```bash
export MULTI=$MULTI_ROOT
export PATH=$PATH:$MULTI/r94/boot-3.2:.
cd $MULTI/validation_cases/TiCheck
rm -f ktag
./RUN
# 等待（约 10 秒，121 步）
for i in $(seq 1 60); do [ ! -f ktag ] && break; sleep 2; done
```

## 2. 判读（预期值）

```bash
grep -c "normal program termination" output   # 预期 1
grep "relative error in energy" output         # 预期 |error| < 1e-6
```

表加载摘要预期（`data.in` 五表）：
- `Ti_eos_e`（id 22000304，45×100）/ `Ti_eos_i`（22000305）
- `Ti_LTE.ZEFF`（27002000）/ `Ti_LTE.PLANCK`（27003000，**30 群**）/ `Ti_LTE.ROSS`（27004000）

## 3. 出图

```bash
python3 $MULTI/work/eos_opacity_tools/plot_1d_validation.py $MULTI/validation_cases/TiCheck
# 产物: density_heatmap.png + profiles_mid.png（存算例目录）
```

判读：记录数 ≥50（ns_bout=1，约 121 条）；热图显示 100 eV 辐射波从右侧
（x≈2 μm 处）烧入 Ti 平板、密度前沿随时间推进；剖面（t≈0.6 ns）ρ/Te/Ti/Ptot/Pe 光滑。

## 4. 物理预期（辐射浴算例模板，材料迁移验证规范 §3）

- 平面（igeo=1）Ti 平板 2 μm、20 单元、固体密度 4.54 g/cc
- 右侧 100 eV 恒定辐射浴（betar=1, itype=2, trad=100, tau=1e-9）
- texit=1.2e-9，dt=1e-11；激发 EOS+不透明度+电离三张表

## 5. 相关

- 算例设计原理：`multi-1d-ife/knowledge/input_cards.md`
- 结果判读细节：`../knowledge/output_reading.md`
