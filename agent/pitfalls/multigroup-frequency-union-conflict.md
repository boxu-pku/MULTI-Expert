# 多材料多群表频率并集冲突：opa "frequency not found in tables"

**日期**：2026-11-12（Quartz_SiC_CaO 战役首跑触发）
**场景**：1D m150304.f95 多材料算例，两种以上材料各挂真实多群 P/R 表

## 现象

`ERROR in subroutine opa / frequency not found in tables`，起步即崩。

## 根因

- `frequencies`（m150304.f95:L3496）把**所有材料** planck/ross/eps 表的群边界
  取**并集**生成统一群网格（灰体表 fa==fb 不参与并集）。
- `opa`（L2372）要求每个材料在**每个合并群的代表频率**都能命中自己某群的
  [fmin,fmax]——即**所有多群表的全局频率范围必须一致**（内部边界可不同，
  合并群代表点落在表内即可；全局范围不一致则范围窄的表必炸）。
- 实测冲突：CH_CELIA 20 群 [1,5000] eV vs AlHub(NG40) 40 群 [1,20000] eV
  → >5 keV 合并群 CH 查不到。

## 解法（preheat 系列先例）

Al 不透明度/Z 改挂**原生 `tables/Al`**（20 群，与 CH_CELIA 逐群同网格
[1,5000] eV，ids 10003000/10004000/Z 10002000），EOS 仍可用 AlHub
（SESAME 3717 e/i 拆分表）。Quartz_OPC 是灰体（表头 itype=3/4，无 fmin/fmax）
不参与并集，任意混搭安全。

## 通用规则

1. 多材料算例中**至多一族真实多群表**，其余材料用灰体（fa==fb 或 itype 3/4/5）；
2. 或确认各多群表全局范围一致（原生 MULTI 20 群 = CH_CELIA 网格是安全基准）；
3. 诊断工具：`cases/Quartz_SiC_CaO/check_groups.py` 按加载器逻辑逐表打印
   每群 fmin/fmax，混挂前先跑一遍。

## 相关

- 先例：`cases/preheat/CH-Al-SiO2_rad140-60`（灰体 SiO2 + 20 群 CH/Al）
- 反例首跑：`cases/Quartz_SiC_CaO`（README §3 有完整决策记录）
