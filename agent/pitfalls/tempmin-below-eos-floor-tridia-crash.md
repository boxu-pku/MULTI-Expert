# tempmin 低于 EOS 表 T 下限 → hydro tridia 奇异崩溃

**日期**：2026-08-19（cBN Decay wave 战役）
**状态**：已修复（m150304.f95 新增 tempmin namelist 参数；默认 1K 不变，旧算例比特级一致）

## 症状

cBNFEOS 样品层（Al|cBN 辐射驱动，Decay_wave cbn_shot* 系列）在激波于 cBN 内
传播途中（t≈7.3 ns，dt 已到 dtmax）崩溃：

```
ERROR in subroutine tridia
      singular matrix found in 1
```

注意 `1` 是**错误码**（前向消元零主元），不是行号。dtmax=1e-11→5e-12、
te0=0.026→0.03、tquiet=0.0345→0.05 都救不了。

## 根因链（调试定位，/tmp/cbn_dbg 仪器化复现）

1. 冷样品细胞在 LTE 发射（eps=-1）下向 T_rad≈0 辐射冷却，Te 一路跌破
   EOS 表 T 下限（cBNFEOS 为 300K=0.02585 eV），最终被程序的 1K 温度下限
   （`p%tempmin=8.617e-5 eV`，硬编码）钳住——比表下限低 **300 倍**。
   （VARDBG 打印可见：多细胞 Te 恒为 8.6100e-5 eV，即 1K 钳位值。）
2. EOS 表对低于 T 下限的查询做**外推**，返回垃圾 dP/dρ（c²~1e27 量级，
   正常冷 cBN c²~1e12）。
3. hydro 隐式矩阵系数 g∝c² 被放大到 ~1e10，前向消元发生灾难性抵消，
   某主元精确为 0.0 → tridia 停机。崩溃行 = 预热前沿到达处（Te 从 1K
   钳位一步跳 ~6 eV 的细胞界面）。

石英战役不崩纯属侥幸：QuartzFEOS 表下外推行为良性（或其灰体 OPC 冷端
冷却更弱，Te 未跌到 1K）。

## 修复

`m150304.f95`（备份 `.bak_tempmin_20260819`）把 tempmin 提升为 namelist
参数（同 iquiet/tquiet 模式）：

- 声明/namelist 表/默认赋值（`tempmin=0.0000861`，namelist 语句之后按
  spec 顺序）/`p%tempmin` 赋值/print echo 各一处。
- **旧算例不受影响**：不写 tempmin 即默认 1K，石英 shot385/x1.1 用新二进制
  重跑 fort.10 **比特级一致**（2026-08-19 验证）。

使用规则：**tempmin ≥ 所用 EOS 表的 T 下限**（把 Te/Ti 钳在表网格内，
杜绝表下外推）。cBN 算例统一 `tempmin=0.026`（恰好钉在 cBNFEOS 300K
下限网格行上）；这也是物理上更合理的"环境恒温器"（真实环境温度即 300K）。

## 排查备忘

- tridia 报 `singular matrix found in 1/2/3`：1=前向消元(i=1..n-1)、
  2=末行、3=回代——都是错误码非行号；要看行号需自行在调用点加守卫打印。
- 三个 tridia 调用点：fusion(L716)/heat(L835)/hydro(L1093)；heat 的
  第 1 行对角恒含 −1/dt 不会精确为 0，hydro 才可能。
- 相关先例：`degenerate-cold-electron-dttevar-collapse.md`（同为 cBNFEOS
  冷端病症，那次的处方是 dttevar=1e12；本次是更深一层的表下外推）。

## 涉及

- 源码：r94/MULTI-IFE-2015/m150304.f95（tempmin namelist 化）
- 算例：cases/Decay_wave/cbn_shot*/x*/data.in（tempmin=0.026）
- 生成器：cases/Decay_wave/make_case.py（--sample cbn 分支自动带上）
