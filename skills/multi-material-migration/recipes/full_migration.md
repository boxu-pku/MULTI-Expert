# Recipe: 全套材料迁移（hyades EOS + Thermos 不透明度，清单驱动）

> 场景：迁移一种单质元素（Multi_BACK 中有 hyades EOS + Thermos 多群不透明度），
> 目标是"全套"（2D EOS + 1D 五表 + 验证算例 + 验收登记）。
> 以假想的新元素 `Xx`（A=xx.xx, Z=nn, ρ0=s.ss）为例。

## 0. 开工前确认

1. **查重**：`MULTI-2D_材料库清单.md` 确认未迁移
2. **查源**：
   - EOS：`$MULTI_LIBS/newmulti/Multi_BACK/matter++/hyades/EOS.list` 找文件号
     （eos_<n>.dat）与 A/Z/ρ0
   - 不透明度：`Multi_BACK_材料不透明度映射表.md` 确认 Thermos `Xx_Planck.dat` 等存在
   - Zeff：Thermos `Xx_Zeff.dat`
3. **查表覆盖**（防 Kr/Diamond 类失败）：转换后先跑 check_multi_file.py 看网格范围，
   确认 ρ 上限 ≥10×ρ0、T 下限 ≤0.03 eV

## 1. 清单驱动迁移（推荐）

把条目加入 `work/eos_opacity_tools/migrate_manifest.py` 的 `BATCH_FULL`：

```python
("Xx", xx.xx, nn, s.ss, f"{HYADES}/eos_<n>.dat", "Xx"),
```

执行：

```bash
cd $MULTI_ROOT/work/eos_opacity_tools
python3 batch_migrate.py Xx
```

自动完成（对应 S1-S6）：hyades→EOS-tools 转换（自适应 ΔE 网格）→ 拆分 1D 电子/离子表
（id 自动）→ Thermos 三表去 CR+修-INF+删退化子表 → check_multi_file 全量验证 →
生成 `validation_cases/XxCheck/`。看输出的 `格式验证=PASS` 与 id 摘要。

## 2. 2D 材料函数

```bash
python3 gen_material_functions.py     # 重新生成 Material_mig.r（含 Xx 的拟合 opafun）
cd $MULTI_ROOT/r94/m2d-core-9.1 && x.2.library
grep -c "MaterialXx" Material.c        # ≥1 且 .c 新于 .r
```

## 3. 运行 + 可视化（S7/S7b）

```bash
cd $MULTI_ROOT/validation_cases/XxCheck && ./RUN
for i in $(seq 1 60); do [ ! -f ktag ] && break; sleep 2; done
grep -c "normal program termination" output    # 应 1
grep "relative error in energy" output          # 应 <1e-6
python3 ../../work/eos_opacity_tools/plot_1d_validation.py .
```

若 ρ0 为固体且材料可压缩性强（稀有气体尤甚），警惕辐射坍缩越界——
必要时改气体密度（参照 KrCheck）。

## 4. 子 agent 验收（S8）

用《材料迁移验证规范.md §5》模板新起子 agent（本 skill `knowledge/acceptance.md §4`
有副本）。迁移记录写明：源文件、各步骤实际情况、batch 输出摘要。
REJECT → 修复 → 复验。

## 5. 登记（S9）

1. 《MULTI-2D_材料库清单.md》§1.1 加行（材料/模块/网格/群数/Zeff/验证算例），
   §五验收记录加行，状态"机器验收通过，待人工确认"
2. 报告用户查看入口：`validation_cases/XxCheck/`（output + 两张 PNG）
3. 用户确认 → 标"完全迁移 ✅"

## 6. 相关

- 流程逐步详解：`../knowledge/s_flow.md`
- 历史事故（必读）：`../knowledge/pitfalls.md`
- 范例：`../examples/ti_migration.md`
