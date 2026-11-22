---
title: IEOS 反演状态方程表 — 字节级规范、单位换算与电子/离子拆分
skill: multi-eos-format
category: internals
source_anchors:
  - r94/matter-3.1/Mat2013_LoadMF.r:L47-L50
  - r94/matter-3.1/Mat2013_LoadMF.r:L148-L156
  - r94/matter-3.1/Mat2013_LoadIEOS.r:L18-L28
  - r94/matter-3.1/Mat2013_EleTab.r:L47-L90
  - r94/matter-3.1/Mat2013_GasIEOS.r:L23
  - r94/MULTI-IFE-2015/m150304.f95:L2959-L2965
  - MULTI-2D_材料库迁移指南.md §1.2
doc_ref: "MULTI-2D_材料库迁移指南.md §1.2, §2"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - IEOS
  - 反演表
  - 单位换算
  - 能量主序
  - EleTab
  - GasIEOS
  - 双温
---

# IEOS 反演状态方程表

> **TL;DR**：IEOS = (ρ, ΔE) 网格上存 P、T 的"反演"EOS 表。五节数据：r[NR]、de[NE]、e0[NR]、p[NE×NR]、t[NE×NR]；**p/t 是能量主序 p[j*NR+i]**。文件单位 Mbar·cm³/g / Mbar / K，读入 ×1e12→cgs、÷11604.519→eV。

## 1. 原理 / 设计动机

辐射流体计算中，流体步给出 (ρ, 内能 E)，需要反查 P、T——所以 MULTI 的 EOS 表
直接以 (ρ, ΔE) 为自变量存 P、T（"反演表"，inverted EOS）。物理关系：

```
E(ρ, i) = E0(ρ) + ΔE(i)        （E0 = 每个密度的冷能）
P = p(ρ, ΔE),  T = t(ρ, ΔE)
```

RT（ρ,T 正演）→ RE（ρ,ΔE 反演）转换存在插值误差，低温/相变区尤其注意
（迁移指南 §8-3）；转换由 EOS-tools 完成并产出 audit 报告。

## 2. 字节级规范

```
表头:  id(任意, 2D 忽略; 1D 按它检索) | type(不匹配 mgo/sgo 即可, 习惯放 rho0) | NR | NE
数据:  r[NR]      密度网格, g/cm³, 线性值(非对数)
       de[NE]     能量增量网格 ΔE, Mbar·cm³/g
       e0[NR]     每个密度的冷能 E0, Mbar·cm³/g
       p[NE×NR]   压力, Mbar; 能量主序: 前 NR 个值对应第一个 ΔE
       t[NE×NR]   温度, K; 布局同上
```

- IEOS 兜底分支（type 不匹配 mgo/sgo 时）：`Mat2013_LoadMF.r:L148-L149`
- 布局文档注释："the first NR values correspond to the first energy increment"
  —— `Mat2013_LoadMF.r:L47-L50`（`Mat2013_LoadIEOS.r:L10-L11`、`Mat2013.r:L20-L21` 同述）
- 读取顺序（r→de→e0→p→t）：`Mat2013_LoadMF.r:L155-L156`；
  独立复刻：`split_ieos_table.py:L52-L61`
- 能量主序的 C 实现证据：`Mat2013_EleTab.r:L66-L67`（`tot_P[j*nr+i]`）

## 3. 单位换算链

| 量 | 文件单位 | → 程序内部 | 换算 |
|---|---|---|---|
| de / e0 | Mbar·cm³/g | erg/g (cgs) | ×1e12 |
| p | Mbar | dyn/cm² (cgs) | ×1e12 |
| t | K | eV | ÷11604.519（1D 代码用 11605） |

换算锚点（1D 端，2D 相同约定）：
```
r94/MULTI-IFE-2015/m150304.f95:L2959-L2965
   eostab%de = buffer(n+1:n+ne)*1.e12
   eostab%e0 = buffer(n+1:n+nr)*1.e12
   eostab%p  = buffer(n+1:n+ne*nr)*1.e12
   eostab%t  = buffer(n+1:n+ne*nr)/11605.
```

参考：1 Mbar·cm³/g = 10¹² erg/g = 10⁵ J/g（迁移指南 §1.2）。
`split_ieos_table.py:L27-L30` 有同一组常数（EV_K=11604.519、E12=1e12）。

## 4. 两个程序的消费方式差异

| | 2D（r94） | 1D（MULTI-IFE-2015） |
|---|---|---|
| 入口 | `Mat2013_LoadIEOS(file)`（`Mat2013_LoadIEOS.r:L18`） | `load_table_eos`（`m150304.f95:L2928`） |
| 表数限制 | **恰好 1 张**（多表报错 "bad number of tables"，`L26-L28`） | 按 id 从多表文件挑表（`m150304.f95:L2944`） |
| 电子/离子 | `ieos`(总表) + EleTab/GasIEOS 派生；或双温直接挂 `ieose`/`ieosi` | `eeos_file`/`ieos_file` 两张分离表 |

## 5. 电子/离子表拆分（EleTab / GasIEOS）

1D 需要电子、离子分离的 IEOS。从总表派生：

**电子表（Mat2013_EleTab）**——从总表减去理想离子贡献：
```
cte = k_B / (A·m_u)  [erg/(g·eV)]          Mat2013_EleTab.r:L47
P_e(ρ,ΔE) = P_tot − ρ·cte·T_tot            Mat2013_EleTab.r:L67
ΔE_e      = ΔE − 1.5·cte·T_tot (截断为 0)   Mat2013_EleTab.r:L68
再按 ΔE 方向线性插值回原 de 网格             Mat2013_EleTab.r:L89-L90
```

**离子表（Mat2013_GasIEOS）**——理想气体 γ=5/3：`Mat2013_GasIEOS.r:L23`
```
T = ΔE/(1.5·cte),  P = ρ·ΔE/1.5,  E0 = 0
```

独立 Python 复刻：`work/eos_opacity_tools/split_ieos_table.py`
（`split_electron` L75-L109、`make_ion_ideal` L112-L124），CLI：
```bash
python3 split_ieos_table.py <总表> <A> <e输出> <i输出> [e_id i_id]
```

**自洽性抽查要点**：比较 Pe+Pi vs P_tot 必须按各自能量网格反查（E_e(T)、E_i(T) 不同），
同索引直接相加在高温端有系统性偏差（可达数倍），不是拆分错误（迁移指南 §8-8）。

## 6. 双温模拟（ieose / ieosi）

2D 双温算例可直接分别挂电子/离子表：
```r
material.ieose = Mat2013_LoadIEOS(电子表);
material.ieosi = Mat2013_LoadIEOS(离子表);
```
（迁移指南 §7.1；Mat2013 结构体字段 `ieose`/`ieosi` 定义于 `Mat2013.r:L64-L65`）
现成分离表示例：Multi_BACK `mat_Al-1.0/Al_ELECTRONEOS/Al_IONEOS_multifs-1.2.dat`（123×100）。

## 7. 常见错误

| 错误 | 原因 | 修复 |
|---|---|---|
| reshape 后与源表大偏差 | 能量主序读反（应 reshape(NE,NR)） | agent/pitfalls/ieos-layout-order.md |
| `bad number of tables` | 2D 遇多表文件 | 拆单表或按 id 自取 |
| 压强整体差 1e4 倍 | dyne/cm²→MPa 误用 ÷1e11（应 ×1e-7） | agent/pitfalls/pressure-unit-confusion.md |
| 低温区 T(ΔE) 非单调被截断 | 温度回折，EOS-tools 记录 multi_temperature_trims | 迁移指南 §8-4，属正常但需知晓覆盖损失 |
| 负 P/T | 老表冷区外推负值；2D 由 HydroEOS 的 positive_P 控制，1D 由输入卡 inegpre 控制 | 迁移指南 §8-5 |

## 8. 延伸阅读

- `knowledge/overview.md`（容器格式）、`knowledge/mgo_sgo_format.md`
- `MULTI-2D_材料库迁移指南.md §1.2、§2.1、§7.1、§8`

## 9. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
