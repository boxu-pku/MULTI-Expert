# Recipe: 为仅 EOS 材料配 hyades opc 单群不透明度（升级为单群材料）

> 场景：材料已有 EOS（批次2 仅 EOS 材料），Multi_BACK 中有对应 opc 平均表
> （直接或借用），升级为"单群 opc 材料"（2D/1D 灰体辐射可用 + 1D 验证算例）。
> 已完成 21 种的参照：2026-08-11 opc 批次（`migrate_opc_batch.py`）。

## 0. 查映射

`Multi_BACK_材料不透明度映射表.md §B` 或 `migrate_opc_batch.py:L31-L43` 的 OPC_MAP：

```
SiO2 族→1022, PE→1031, PS→1032, PU→1033, Parylene→1035, Mylar→1036,
Al2O3→1161, WC→1121(借W), 碳族→1344(借C), LiD/LiH→1071(借Li),
SS→1181(借Fe), Water→1311, Air→1301, Sn→1401, Eu→1461 ...
```

新材料不在表中 → 查 Multi_BACK `material.base` 的 MID 注释确定对应 opc 表号。

## 1. 转换（opc → sgo）

```bash
M=$MULTI_ROOT
OPC=$MULTI_LIBS/newmulti/Multi_BACK/matter++/hyades/Opacity
python3 $M/work/eos_opacity_tools/opc2sgo.py $OPC/opc_<n>.dat <n> \
    $M/r94/MULTI-IFE-2015/tables/<X>_OPC
# 产物: <X>_OPC.ROSS + <X>_OPC.PLANCK（sgo 单群表, id=<n>, 双兼容 type 串）
```

注意：Planck 块全零的源（如 Au 的 opc_1051/1052）自动复制 Rosseland（源码规则）。

## 2. 验证

```bash
python3 $M/work/eos_opacity_tools/check_multi_file.py \
    $M/r94/MULTI-IFE-2015/tables/<X>_OPC.ROSS $M/r94/MULTI-IFE-2015/tables/<X>_OPC.PLANCK
# 应: sgo[type=0.40000000E+01] / [0.70000000E+01]，NR×NT 与源一致
```

## 3. 建算例 + 运行 + 出图

挂表方式（z_id=-1 用常数 zi；planck/ross id=opc 表号）：
参照 `migrate_opc_batch.py:L73-L75` 的 make_case 调用。
其后与全套材料相同（RUN → 判读 → plot_1d_validation.py）。

## 4. 2D opafun

拟合 Rosseland 平均自由程（`migrate_opc_batch.py:fit_freepath` L46-L56；
结果写 /tmp/opc_fits.txt），再跑 `gen_material_functions.py` 更新 Material_mig.r，
`x.2.library` 重编译。

## 5. 验收与登记

同全套流程（S8 子 agent + S9 登记）；清单 §1.2 加行（注明 opc 源表号与借用说明）。
已知 CAVEAT 参照：Diamond/Cliquid（表范围局限）。

## 6. 相关

- opc 表真实结构：`multi-opacity/knowledge/data_sources.md §3`
- 借用规则总表：`Multi_BACK_材料不透明度映射表.md §B`
