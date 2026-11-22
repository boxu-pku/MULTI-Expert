---
title: "eos_convert --from feos 报 composition must not contain duplicate atom_z（同位素混合物被阻塞）"
category: 表加载
severity: 阻塞（不能跑）
first_seen: 2026-08-31
last_verified: 2026-08-31
verifier: claude
status: stable
tags:
  - eos-tools
  - feos
  - isotope
  - DT
  - duplicate-atom-z
  - sesame-route
source_anchors:
  - EOS-tools eoslib/model.py:L156
  - EOS-tools eoslib/formats/multi.py:L88-L89,L1354-L1470
  - FEOS Code/FE-01_TABTOOLS.C:L601-L606
---

# eos_convert --from feos 报 duplicate atom_z（同位素混合物）

> 触发材料：DTFEOS（FEOS mat 5271，等摩尔 D+T，D/T 均 Z=1）
> 关联：[[feos-converter-layout-energyunit]]、[[eos-tools-multi-monotonic-postfix]]

## 错误信息

```
ValueError: composition must not contain duplicate atom_z values.
  (eoslib/model.py L156，经 eoslib/formats/feos.py load → _to_eos_dataset)
```

## 原因

EOS-tools 的 `MaterialComposition` 以 `atom_z` 为唯一键，禁止重复 Z。
`.feos` 主表头存储 NE=2 的成分数组（D: A=2.014 Z=1；T: A=3.016 Z=1），
同位素混合物（同 Z 不同 A）必然撞键。**根因分类：源码行为（EOS-tools 设计限制）**，
不是数据错误——FEOS 侧的混合物表本身完全正常。

## 修复 / 绕开

不走 `--from feos`，改走 **SESAME 分表路线**（feos 工具链对任意材料都会输出
`.304`（电子）/`.305`（离子），SESAME 路线无成分校验）：

```bash
cd $MULTI_LIBS/EOS_converter_xubo/EOS-tools
python cli/eos_convert.py --from sesame --to multi \
  --electron-file <mat>.304 --ion-file <mat>.305 \
  --output <prefix> --atom-a <A_mean> --atom-z <Z_mean> --energy-points 96
```

单位链已核实一致：FEOS 写 SESAME 301 族用 GPa/MJ/kg/K
（`FE-01_TABTOOLS.C:L601-606`），EOS-tools 读入转 MPa/J/g，MULTI 写出
`MBAR_TO_MPA=1e5`、`JPG_TO_MULTI_ENERGY=1e-5`（= P-09 格式卡的文件能量单位
1e12 erg/g，与 feos2multi.py 的 ×100 bug 相反，**EOS-tools 的 MULTI 写器是对的**：
能量外层布局 `(NE,NR).ravel()`、de[0]=0、头行第二字段 0.0 合法——MULTI
`load_table_heading` 的 itype 默认 1，只有 6/7 才判为 opacity）。

## 判定 / 校验（DTFEOS 实测）

- 与源 `DT.data.txt` 在表内 T(rho,de) 处交叉对拍：P 中位偏差 0.02–0.03%，
  p95 ≤0.26%（>1 MJ/kg 区）；dE 在 de>1 MJ/kg 区 ≤0.08%
- `check_multi_file.py` 全 ✓（exit 0）
- 1D 算例 DTFEOSCheck（100 eV 辐射浴烧蚀液态 DT）normal termination，
  能量误差 3.7e-10；与 SESAME 52711/52712 对照末态 te 中位 +2.5%

## 关联风险提示

L-009（[[eos-tools-dup-rows-ideal-ion]]）的 FEOS 离子表低 ρ（≲0.1）低 T（≲0.35 eV）
平台风险对 DT 同样存在（核对显示 DT 离子在 T<2 eV 偏差可达数倍）；DTFEOSCheck
未穿越该区故未触发。若后续 DT 算例出现不自愈的 var fail，按 L-009 双构型对拍排查，
必要时按房子约定换理想气体离子表（DT 离子在 ρ≤0.1 本就与理想气体一致到 0.5%）。
