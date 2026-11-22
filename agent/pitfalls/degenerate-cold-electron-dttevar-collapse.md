# 冷简并电子区 Te 离散跳变导致 dt 塌缩（dttevar 限幅）

**日期**：2026-08-18（hBNFEOS 迁移）
**状态**：已确认并修复（hBNFEOS 6 档算例 dttevar/dttivar=1e12）

## 症状

Hugoniot 校验算例在固定时刻（与源强无关的波后某状态）出现 "var fail"
死循环：dt 反复减半至 1e-26 量级，模拟卡死。表面症状与
`feos-converter-layout-energyunit`（能量单位错 → RH 无解）不同：
能量守恒完好、无负密度，只是时间步崩溃。

## 根因

消融区/波前低温单元的电子处于**简并区**：Te 从表底板（≈1 K）到几十 K
对应的能量增量是无穷小量（dE/dT → 0），de 在数值噪声下于 0 附近变号，
IEOS 反演把 Te 钳在底板或跳到 ~15 K——**相对变化 ~27× 且与 dt 无关**。
`dttevar=0.5`（Hugoniot 模板默认）的相对变化限幅永远超限 → 死循环。

打桩方法：在 `m150304.f95` `variation()` 内给 `vmax>10` 加 maxloc 打印，
重编译单算例复现（work/hbn_feos_migration 流程记录见 材料表信息.md）。

## 修复

该材料算例设 `dttevar = 1e12, dttivar = 1e12`（关闭 Te/Ti 相对变化限幅，
与 Check 算例默认一致；密度限幅 dtrvar=0.9 保留即足以控制步长）。
修复后 6 档全部正常结束，能量误差 ≤2.2e-7，Hugoniot 主判据不受影响。

## 排查要点

- "var fail" 死循环 + 能量守恒正常 + 剖面无异常 → 先查温度相对变化限幅，
  打桩看是哪个变量、哪个 cell、跳变是否 dt 无关；
- FEOS 系材料（冷端简并电子）做冲击算例时预防性把 dttevar/dttivar 放开；
- 与 `ionmix-preheat-shell-merger`（辐射介导等温波）区分：那是物理形态
  问题（无间断），这是数值限幅问题（间断正常、步长崩溃）。

## 相关

[[feos-converter-layout-energyunit]]、[[total-eos-ideal-ion-split-cold-condensed]]

## 复现实例

- 2026-08-18 cBNFEOS（同日同机制第二次出现）：hugoniot_T50 在 t=0.89 ns
  dt 塌至 6e-28、3 万步不前；dttevar/dttivar=1e12 后 1401 步跑完。
  cBNFEOS 另需 T150+ 档 dtmax=5e-12（1e-11 时强辐射下 v_pre 巨大、
  波前检测 nan）——见 `validation_cases/cBNFEOS/材料表信息.md`。
