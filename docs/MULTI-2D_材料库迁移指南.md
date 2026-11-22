# MULTI-2D 材料库迁移指南（状态方程与不透明度）

> 用途：向 MULTI-2D.2026.3 迁移 / 新增材料时的格式规范、资源清单、工具位置与操作流程参考。
> 所有结论均经过**源码级核对 + 严格解析器实测**（2026-08）。
> 相关文档：`MULTI-2D_梳理文档.md`（软件总体架构）。

---

## 目录

1. [MULTI 数据文件格式规范（精确到字节）](#1-multi-数据文件格式规范)
2. [MULTI-2D.2026.3 的数据消费路径](#2-multi-2d20263-的数据消费路径)
3. [现有材料库（2026.3 自带）](#3-现有材料库20263-自带)
4. [Multi_BACK 资源盘点与可用性分级](#4-multi_back-资源盘点与可用性分级)
5. [已知问题文件清单](#5-已知问题文件清单)
6. [工具清单与位置](#6-工具清单与位置)
7. [操作手册（Recipes）](#7-操作手册recipes)
8. [物理注意事项](#8-物理注意事项)

---

## 1. MULTI 数据文件格式规范

所有 MULTI 材料数据文件共享同一容器格式（"traditional MULTI format"，见 `r94/matter-3.1/Mat2013_LoadMF.r`）。一个文件可含多个子表（子表顺序拼接）。

### 1.1 通用结构

```
表头行:  恰好 60 字符 = 4 个 15 字符定宽字段
         [id 15字符][type 15字符][NR 15字符][NT/NE 15字符]
数据体:  15 字符定宽科学计数（典型 "%15.8e"），每行最多 4 个值
         各节之间连续打包（上一节在某行中间结束，下一节从同一行继续）
特殊值:  "           -INF" → 读为 -40（log 截断）；"            NAN" → 读为 0
```

**type 字段决定表的类别**（字符串精确匹配）：

| type 字符串 | 类别 | 含义 |
|---|---|---|
| `PLANCK M       ` / `ROSSELAND M    ` / `EPS M          ` | **mgo** | 多群不透明度/发射率 |
| `PLANCK 1       ` / ` 0.70000000E+01` / ` 7.00000000e+00` | **sgo** | 单群 Planck 平均 |
| `ROSSELAND 1    ` / ` 0.40000000E+01` / ` 4.00000000e+00` | **sgo** | 单群 Rosseland 平均 |
| `EPS 1          ` | **sgo** | 单群发射率 |
| ` 0.60000000E+01` / ` 6.00000000e+00`（r94）；` 0.60000000e+01`（1D Fortran） | **sgo** | **Zeff 电离度表** |
| 其他任何字符串 | **IEOS** | 反演状态方程表（兜底分支） |

> ⚠️ Zeff 的 type 串两个读取器接受的变体不同（见 §2.3 注意点）。

### 1.2 IEOS（反演状态方程）表

```
表头:  id(任意, MULTI 忽略) | type(不匹配上行类型即可, 习惯放 rho0) | NR | NE
数据:  r[NR]      密度网格, g/cm³, 线性值(非对数)
       de[NE]     能量增量网格 ΔE, Mbar·cm³/g
       e0[NR]     每个密度的冷能 E0, Mbar·cm³/g
       p[NE×NR]   压力, Mbar; E 行 rho 列(前 NR 个值对应第一个 ΔE)
       t[NE×NR]   温度, K; 布局同上
物理关系: E(rho,i) = E0(rho) + ΔE(i)
```

单位换算链（读入端）：`de/e0/p × 1e12 → erg/g 或 dyn/cm² (cgs)`；`t ÷ 11604.519 → eV`。
（1 Mbar·cm³/g = 10¹² erg/g = 10⁵ J/g。）

### 1.3 mgo（多群不透明度）表

每个光子能群一个子表，NG 个子表连续存放（同 id）：

```
表头:      id | "PLANCK M       "(或 ROSSELAND M / EPS M) | NR | NT
第二行:    f1 f2  —— 本群光子能量下/上界, eV (两个 15 字符字段, 独占一行)
数据:      lr[NR]    log10(密度 g/cm³)
           lt[NT]    log10(温度 eV)
           lo[NT×NR] log10(不透明度 cm²/g); T 行 rho 列(前 NR 个值对应第一个 T)
```

### 1.4 sgo（单群平均/Zeff）表

```
表头:  id | type(见 §1.1) | NR | NT
数据:  lr[NR] lt[NT] lo[NT×NR]   (无 f1/f2 行, 全部 log10)
```

> ⚠️ **Zeff 表温度单位**：`Mat2013.r` 注释写 eV，但实际文件（如 `AU_op03z` 网格 -3~+2）只有按 **keV** 解释才有物理意义（1 eV~100 keV，与同族不透明度表覆盖一致）。EOS-tools 按 keV 处理，与实际文件一致。当前 2D 代码不读外部 Zeff 表（见 §2.1），此差异暂无实际影响。

---

## 2. MULTI-2D.2026.3 的数据消费路径

### 2.1 二维程序（m2d-core-9.1）

**EOS**：`Mat2013_LoadIEOS(file)`（`r94/matter-3.1/Mat2013_LoadIEOS.r`）
- 要求文件**恰好 1 张 IEOS 表**（多表文件报错）
- 材料定义在 `r94/m2d-core-9.1/Material.r`，模式：`ieos`(总表) + `Mat2013_EleTab`（减理想离子得电子表）+ `Mat2013_GasIEOS`（理想气体离子表）
- 双温模拟可直接分别挂 `ieose`/`ieosi`（电子/离子分离表）

**不透明度**：辐射输运是**单群（灰体）模型**——
`M20_Transport` → `Material_Freepath` → 逐材料调用 `mat.opafun`（**解析公式** `l=f(rho,t)`，cm）
→ `M19_Radia`（lambda 每单元 1 个值，`nphis` 是角度离散非光子群）。
**多群表在 2D 没有消费者**；`Mat2013_LoadOpa`/`Mat2013_LoadTab` 被作者禁用（`error("not tested software")`）。
但 `Mat2013_LoadMF` 本体的 mgo/sgo 解析分支是好的，User.r 可直接调它读表后自写插值回调。

### 2.2 一维程序（MULTI-IFE-2015，多群非 LTE）

`r94/MULTI-IFE-2015/m150304.f95`（自包含 Fortran，`gfortran` 直接编译）：

| 输入卡条目 | 表 | 备注 |
|---|---|---|
| `eeos_file/eeos_id` | 电子 IEOS | 单位换算同 r94 版 |
| `ieos_file/ieos_id` | 离子 IEOS | |
| `z_file/z_id` | Zeff (sgo, type=6) | `z_id=-1` 用常数 zi |
| `planck_file/planck_id` | Planck 多群 (mgo) | |
| `ross_file/ross_id` | Rosseland 多群 (mgo) | |
| `eps_file/eps_id` | 发射率 (非 LTE) | `eps_id=-1` 用 LTE |

- **群结构自动推导**（`frequencies` 子程序）：合并所有材料各表的 fmin/fmax 边界排序成统一网格；多材料群结构不同时取**并集**（群数膨胀，注意算力）
- id 匹配：输入卡的 `*_id` 必须等于文件头第 1 字段的整数值
- Fortran 顺序格式读按记录换行，**对 CRLF 天然容忍**（已编译实测）；仍建议统一转 LF
- 自带表库 `r94/MULTI-IFE-2015/tables/`（DT、Be20keV、Mix20keV、Al、Carbon、CPC88 等；README 记载 DT 多群表直接复制自 CELIA——与 Multi_BACK 同源）

### 2.3 注意点（两个读取器的差异）

1. Zeff type 串：r94 认 ` 0.60000000E+01`/` 6.00000000e+00`；1D Fortran 认 ` 0.60000000E+01`/` 0.60000000e+01`。**EOS-tools 写出的 zeff 用 ` 6.00000000e+00`，1D 会误读为 IEOS**——给 1D 用需把头行第 2 字段改成 ` 0.60000000E+01`。
2. r94 版 C 解析器**不容忍 CRLF**（`head line size != 60`）；1D Fortran 容忍。
3. IEOS 在 2D 每文件限 1 表；1D 按 id 从多表文件中挑表。

---

## 3. 现有材料库（2026.3 自带）

| 目录 | 内容 |
|---|---|
| `r94/mat_DT-1.0` | DT_EOS（SESAME，50×25）+ 理想气体/简单不透明度 |
| `r94/mat_Au-1.0` | AU_eos（101×23）、AU_eosd（**损坏**，勿用）、AU_op03 多群系列（2D 不用）、WorkOp |
| `r94/mat_Al-1.0` | AL_eos（66×74） |
| `r94/mat_Be-1.0` | BE_eos（101×50） |
| `r94/mat_C-1.0` | C_EOS（101×23） |
| `r94/mat_Si-1.0` | Si 液/汽反演表 |
| `r94/mat_W-1.0` | Tungsten2015 系列 |
| `r94/mat_CPC` | AU.INV、BE.INV（123×100 大表）、WorkOp |
| `r94/mat_2019` | MPQEOS 表：Al、CHOQG(塑料)、Cu、Fe、Plastic、W（.i301 = IEOS 格式） |
| `r94/MULTI-IFE-2015/tables` | 1D 用：电子/离子分离 IEOS + 多群不透明度 + EPS |

2D 标准算例全部使用解析 `opafun` 自由程公式（`Material.r` 中的 `freepath_Au` 等）。

---

## 4. Multi_BACK 资源盘点与可用性分级

源目录：`$MULTI_LIBS/newmulti/Multi_BACK/matter++/`（Windows 版 Multi1D 的材料库）。
材料索引：`material.base`（187 条材料记录，注释含来源说明）。

### 4.1 EOS（IEOS）——A 类：直接可读（LF，实测通过）

| 文件 | 网格 | 相对 2026.3 |
|---|---|---|
| `mat_CELIA/DD_ieos` | 50×25 | **新增**（氘氘） |
| `mat_CELIA/CH_ieos`、`mat_C-1.0/CH_ieos` | 101×100 | **新增**（CH 塑料细网格） |
| `mat_CELIA/DT_ieos` | 50×25 | 与 DT_EOS 同源 |
| `mat_Al-1.0/AL_LV.INV.data` | 123×100 | **新增**（Al 液-汽） |
| `mat_Au-1.0/AU_eos`、`mat_Al-1.0/AL_eos`、`mat_Be-1.0/BE_eos`、`mat_C-1.0/C_EOS`、`mat_DT-1.0/DT_EOS`、`mat_CPC/AU.INV`、`mat_CPC/BE.INV` | — | 与 2026.3 重复 |

### 4.2 EOS——B 类：dos2unix 后可读（CRLF，去 CR 后实测通过）

| 文件 | 说明 |
|---|---|
| `mat_Ti/Ti_eos`（45×100）、`mat_Ti/422_ieos`（43×22） | **钛，全新材料** |
| `mat_Al-1.0/Al_ELECTRONEOS_multifs-1.2.dat` + `Al_IONEOS_multifs-1.2.dat` | **Al 电子/离子分离表（双温直接可用）**，123×100 |
| `mat_Al-1.0/41_ieos`、`42_ieos` | Al 变体 |
| `mat_C-1.0/511_ieos` | 低密度碳（ρ≤3.2） |
| `Thermos/mat_U/U_IdealGas_EOS` | 2×2 占位，价值低 |

### 4.3 EOS——C 类：需 EOS-tools 转换（转换链已实测打通）

| 源 | 规模 | 实测 |
|---|---|---|
| `hyades/sesame/eos_*.dat`（94 个）+ `hyades/qeos/`（14 个） | **约 60 种材料**：Pb、Ta、Mo、Ni、Pt、U、Ag、Sn、Ge、Se、Xe、Kr、Ar、Ne、Li、LiD/LiH、BeO、B₄C、WC、金刚石、液态碳、SiO₂/玻璃/石英、Al₂O₃、水、空气、聚乙烯/聚苯乙烯/聚氨酯/有机玻璃/Parylene/Mylar/PVA/特氟隆/环氧、炸药、不锈钢、Mg、Ca、Eu、Nd、Gd…（清单见 `hyades/EOS.list`） | Pb → MULTI ✓ |
| SESAME 301/304/305：`mat_P/RedP.*`、`mat_Au-1.0/Au.301`、`ColdOpacity/C.30*`、`mat_Al-1.0/FEOS/Al.feos.30*` | 红磷/Au/C/Al | RedP → MULTI ✓ |
| FEOS：`mat_Others/SiO2.feos`、`mat_Al-1.0/Al.feos` | SiO₂、Al | SiO₂ → MULTI ✓ |

### 4.4 不透明度（267 个候选全扫描）

| 类别 | 数量 | 内容 |
|---|---|---|
| A. 直接可读 | 35 | **CELIA 全系列**（C/D/DT/H 的 1G/20G/100G/AN 多群 + Zeff）、Be_40G、各 SIMPLE/WorkOp 单群表 |
| B. dos2unix 后可读 | 211 | **Thermos 全系列（约 50 元素 × Planck/Rosseland/Zeff）**、SNOP 系列（Ti LTE/NLTE 30 群、Au、He、C）、Au100 群（30×50 细网格）、multifs Al、opbe 40 群 |
| C. 有问题 | 见 §5 | |

群边界范围示例：CELIA 20G = 1~5000 eV；W_Planck_Fine = 69 群 1~80 keV；Thermos 多数 = 1~6000 eV。

**另有**：`hyades/Opacity/opc_*.dat`（36 个，Hyades 库格式）。**已按 Multi_BACK 的 C++ 源码（CHYADES_Tab.h/CHYADES_Opacity.h）确认真实结构**：`[NR, NT, rho网格(g/cc), T网格(keV), Rosseland平均表(NR×NT), Planck平均表(NR×NT)]`——是 (ρ,T) 双网格上的**平均值**不透明度（非多群），Planck 块全零表示"仅 Rosseland"（读取端复制 Rosseland 代替）。这正是 2D 单群输运所需的形式，也可作为 1D 的单群（sgo）表使用；`ColdOpacity/*.coldopacity`（约 90 元素的 Eph–μ 文本表，冷边照相用，不进输运）。

---

## 5. 已知问题文件清单

| 文件 | 问题 | 处置 |
|---|---|---|
| `mat_Au-1.0/AU_eosd`（两个发行版都有） | 双表文件且首表缺 101 个值；无加载器引用 | **勿用** |
| `mat_Au-1.0/AU_SIMPLE_PLANCK_MG`（两个发行版都有） | f1/f2 行仅 24 字符（<30 被拒） | 遗留坏文件，勿用 |
| `mat_Ti/Ti_Ross` | 头行 59 字符（NR 字段少 1 前导空格） | 补 1 空格可修；`SNOP_LTE.ROSS` 已覆盖同数据 |
| `mat_He/Untitled.30*` | .305 混入 16 字符 3 位指数字段，EOS-tools 也读不了 | 用 `hyades/sesame/eos_191.dat`（He）替代 |
| `Thermos/{AuMG_Z,C_Z,Ne_Planck,Ne_Rosseland,V_Z}.dat` | 含 Windows `-1.#INF000e+000` | `fix_multi_file.sh` 修复（→ MULTI 标准 `-INF`） |
| `mat_Sn/Cu/Fe/U/W/Mo/Pb/Xe/Ar/Ba/Eu/Ne` 等空目录 | 只有目录没有文件 | EOS 在 hyades 库中，不透明度在 Thermos 中 |
| `C_SNOPMPQeos/SNOP.*`、`*.SNOP`、`*.INHALT`、`*.INPUT` | SNOP 程序输入卡片 | 非数据文件 |

---

## 6. 工具清单与位置

### 6.1 EOS-tools（格式转换主力）

**位置**：`$MULTI_LIBS/EOS_converter_xubo/EOS-tools`

| 项 | 内容 |
|---|---|
| 能力 | 读写 IONMIX4 / SESAME(301/304/305) / Hyades / **MULTI** / FEOS(.feos)；不透明度读写 IONMIX4/Hyades/MULTI、只读 TOPS |
| CLI | `cli/eos_convert.py`（EOS）、`cli/opacity_convert.py`（不透明度）、`cli/eos_query.py`、`cli/eos_generate.py` |
| GUI | `launcher.py`（Qt 界面，含裁切/诊断/数值审计） |
| 文档 | `docs/eos_format_guide.zh-CN.md`（格式说明书） |
| 关键参数 | `--energy-points`（默认 128，自适应可扩到 512）、`--opacity-groups`（重分群；**=1 即聚合成单群**，Rosseland 用 dB/dT 调和矩、Planck 用 B 算术矩） |
| 审计 | 转换后自动生成 `*.conversion-audit.json/csv`（P95/最大相对误差、覆盖率等） |

转换示例：

```bash
cd $MULTI_LIBS/EOS_converter_xubo/EOS-tools
# Hyades → MULTI (单温总 EOS 走 electron 通道; 离子由理想气体推导)
python3 cli/eos_convert.py --from hyades --to multi \
    --electron-file $MULTI_LIBS/newmulti/Multi_BACK/matter++/hyades/sesame/eos_231.dat \
    --zeff-file none --atom-a 207.19 --atom-z 82 --name Pb \
    --output /path/to/out/Pb
# 产物: Pb_electron.multi / Pb_ion.multi / Pb_zeff.multi
```

> ⚠️ EOS-tools 代码注释把文件能量单位标为 "MJ/kg"，实际数值对应 **Mbar·cm³/g**（换算系数 1e-5 正确，仅注释误导）。
> ⚠️ 其 zeff 表头 type 串（` 6.00000000e+00`）1D Fortran 不认，见 §2.3。

### 6.2 本次固化的验证/修复工具

**位置**：`$MULTI_ROOT/work/eos_opacity_tools/`

| 工具 | 用途 |
|---|---|
| `check_multi_file.py` | **新增材料后必跑**：严格复现 `Mat2013_LoadMF` C 语义的验证器，IEOS/mgo/sgo 通吃，通过即保证 2D 可读。`python3 check_multi_file.py <文件...>` |
| `fix_multi_file.sh` | 修复 CRLF 行尾 + Windows `-1.#INF000e+000`（自动备份 .bak）。`./fix_multi_file.sh <文件>` 或 `-d <目录>` |
| `strict_binary_test.py` / `strict_opacity_test.py` | 批量测试脚本（IEOS / 不透明度），含 Multi_BACK 全量清单 |
| `verify_multi_eos.py` | 双向验证脚本：严格解析器 vs EOS-tools 解析器逐值对比 |
| `tread.f95` | 复刻 1D Fortran 表头读取 `(e15.0,a,2e15.8)` 的测试程序，`gfortran` 编译后验证 1D 可读性 |

### 6.3 系统工具

`dos2unix` 或 `sed -i 's/\r$//'`（行尾）；`gfortran`（1D 程序编译）；`./R94`（GUI 内 Manager2015 的 Case→New 克隆算例）。

---

## 7. 操作手册（Recipes)

### 7.1 向 2D 新增材料（单温，最常见）

```bash
# 1. 建模块目录放表
mkdir -p $MULTI/r94/mat_Ti-1.0
cp .../mat_Ti/Ti_eos $MULTI/r94/mat_Ti-1.0/
$MULTI/work/eos_opacity_tools/fix_multi_file.sh $MULTI/r94/mat_Ti-1.0/Ti_eos
# 2. 验证
python3 $MULTI/work/eos_opacity_tools/check_multi_file.py $MULTI/r94/mat_Ti-1.0/Ti_eos
```

在 `r94/m2d-core-9.1/Material.r` 仿照 `MaterialAu()` 添加（改后需重编译相关算例）：

```r
MaterialTi()
{
   eosfile         = getenv("MULTI"):"/r94/mat_Ti-1.0/Ti_eos";
   material        = Mat2013();
   material.ieos   = Mat2013_LoadIEOS(eosfile);
   material.ai     = 47.9;      $ 原子量
   material.zi     = 22;        $ 平均电离度(常数)
   material.z2i    = 22;        $ 有效电离(sum f·z²/sum f·z)
   material.ieose  = Mat2013_EleTab(material.ieos,material.ai);
   material.ieosi  = Mat2013_GasIEOS(material.ai,double(5)/double(3));
   material.rho    = 4.54;      $ 固体密度
   material.opafun = 'freepath_Ti(2)';   $ 解析式或自写查表(见7.3)
   return(material);
}
local freepath_Ti(r,t){ ... }
```

双温模拟：若有电子/离子分离表（如 `Al_ELECTRONEOS/Al_IONEOS`），改为
`material.ieose = Mat2013_LoadIEOS(电子表); material.ieosi = Mat2013_LoadIEOS(离子表);`

### 7.2 向 1D（MULTI-IFE）新增材料（可用多群表）

```bash
cd $MULTI/cases/2015IND   # 或克隆新算例
# 表文件放到 tables/ 下(或指绝对路径), 编辑 data.in 的材料块:
#   eeos_file='tables/BE_eos_e', eeos_id=304,
#   ieos_file='tables/BE_eos_i', ieos_id=305,
#   z_id=-1,
#   planck_file='<路径>/SNOP_LTE.PLANCK', planck_id=27003000,
#   ross_file='<路径>/SNOP_LTE.ROSS',   ross_id=27004000,
#   eps_id=-1,                          ! 或挂 SNOP_NLTE.EPS (id 27005000)
./RUN
```

群结构由表自动推导；多材料时取群边界并集。

### 7.3 在 2D 中使用表格不透明度（高级）

2D 输运是单群：`freepath` 回调需返回 λ(ρ,T) [cm]。两条路：

1. **解析拟合**（现有算例做法）：对表数据离线拟合 `l=a·T^s/ρ^r` 形式写入 `opafun`。
2. **查表插值**：用 EOS-tools 把多群表聚合到 1 群（`--opacity-groups 1`），在 User.r 里：

```r
data  = Mat2013_LoadMF(getenv("MULTI"):"/r94/mat_X/opac_1g.ROSS");
tab   = data#2;          $ sgo 表: tab.lr, tab.lt, tab.lo (log10)
$ 自写双对数双线性插值函数 my_opafun(r,t), 返回 10^interp / κ→λ=1/(κρ)
material.opafun = 'my_opafun(2)';
```

（注意 λ = 1/(κ·ρ)，κ 单位 cm²/g。）

### 7.4 转换流程（Hyades/SESAME/FEOS → MULTI）

1. EOS-tools 转换（§6.1 命令；建议开自适应能量网格，检查 audit 报告覆盖率与 P95 误差）
2. 产物 `_electron.multi`/`_ion.multi` 即为 1D 双温 IEOS；2D 单温用法取 `_electron.multi` 当总表（Hyades 单温源是总 EOS）或电子表
3. `check_multi_file.py` 验证
4. 按 7.1/7.2 挂载

#### FEOS 模型计算（`$MULTI_LIBS/FEOS/FEOS`，2026-08-13 打通）

**推荐路径（2026-08-14 定版）：EOS-tools 转换**

```
cd $MULTI_LIBS/FEOS/FEOS/EOS-Data
./feos <mat>                      # 按 <mat>.par 生成 <mat>.feos（17 场全量）
cd $MULTI_LIBS/EOS_converter_xubo/EOS-tools
python3 cli/eos_convert.py --from feos --to multi --input <mat>.feos --output <X>.multi
#   → <X>.multi_electron.multi / _ion.multi / _zeff.multi（192×512 细网格）
# 改表头 id 后入库 tables/X_eos_e / X_eos_i；check_multi_file.py 验证
```

2D 单温总表：EOS-tools 不出 MULTI 单温格式，用 FEOS 自带
`feos2r94.py <mat>.data.txt <mat_id>` **加两步修复**（见下）。

**⚠ 上游转换器（feos2multi.py/feos2r94.py）两个 bug（2026-08-13 发现）**：
① p/t 按密度主序写出，MULTI 要求能量主序 `p[j*NR+i]`——需转置；
② 能量单位误把 MJ/kg 当 1e12 erg/g（实为 1e10）——de/e0 需 ÷100。
**EOS-tools 无此二 bug（1D 表优先走 EOS-tools）**。
详见 `agent/pitfalls/feos-converter-layout-energyunit.md`。
首例：QuartzFEOS/SilicaFEOS（清单 §1.2c）。

### 7.5 新增材料验收清单

- [ ] `check_multi_file.py` 通过（2D 可读性）
- [ ] `tread.f95` 通过（1D 可读性，若给 1D 用）
- [ ] EOS-tools 转换的 audit 报告无超阈值误差
- [ ] ρ/T 覆盖范围满足算例需求（用 EOS-tools 的 query/plot 查看）
- [ ] 2D：`Material.r` 新材料函数编译通过，跑一个已有算例替换材料烟测
- [ ] 1D：替换表后 `2015*` 算例 `output` 无 ERROR，群数符合预期

---

## 8. 物理注意事项

1. **数据来源可靠性**：`Material.r` 头部明确警告——"这些表适合数值研究，定量科研需替换为更准确的数据库"。Multi_BACK 的表来源混杂（SESAME/QEOS/SNOP/MPQEOS/WorkOp/CELIA），`material.base` 的 REM 注释有部分来源说明，引用前请追溯。
2. **2D 单群 vs 1D 多群**：同一物理问题在两程序中辐射描述精度不同；建议用 1D 多群结果离线生成 Rosseland 平均 λ(ρ,T) 回灌 2D，或直接对比校核。
3. **RT→RE 插值误差**：MULTI 的 (ρ,ΔE) 反演表从 (ρ,T) 转换时有插值误差，低温/相变区尤其注意；EOS-tools 自适应网格 + audit 报告就是控制这个的。
4. **温度回折**：部分表的高能端 T(ΔE) 非单调，EOS-tools 读取时会截断并记录（`multi_temperature_trims`），属正常现象但需知晓覆盖损失。
5. **负 P/T 值**：老 IEOS 表（如 AU_eos）冷区含外推负值；1D 输入卡 `inegpre` 控制是否截断为 0，2D 由 `HydroEOS` 的 `positive_P` 选项控制。
6. **EPS 发射率表**仅 1D 支持（非 LTE）；2D 灰体模型无对应接口。
7. **IEOS 布局易误读**：`p`/`t` 是**能量主序** `p[j*NR+i]`（E 行 ρ 列，前 NR 个值属于第一个 ΔE）。用 numpy 默认 `(NR,NE)` reshape 会得到错误的 (ρ,E) 对应关系（2026-08 两次验收都踩过这个坑），正确是 `reshape(NE,NR)` 或按 `j*NR+i` 索引。
8. **自洽性抽查要点**：比较 Pe+Pi vs P_tot 必须按各自能量网格反查（E_e(T)、E_i(T) 不同），同索引直接相加在高温端有系统性偏差（可达数倍），不是拆分错误。
9. **单位换算必须双向验证**（2026-08-10 事故教训）：hyades→EOS-tools 数据集手工构造时，dyne/cm²→MPa 是 **×1e-7**（不是 ÷1e11——那是 →Mbar）。任何自定义转换链必须在完成后与源表做**物理量绝对值抽查对照**（能量守恒类指标发现不了单位错误）。EOS-tools 单位约定：内部 MPa/J/g/eV；MULTI 文件 Mbar、Mbar·cm³/g、K；hyades 文件 dyne/cm²、erg/g、keV。
10. **Thermos 文件可能含退化子表**（f1==f2），1D `load_table_multi` 遇之误判多群表结束——`batch_migrate.py` 的 `drop_degenerate_groups()` 已自动处理，手工迁移时需注意。

---

> 文档维护：新增材料验证通过后请补录到 §3/§4 对应表格，并在本文件记录来源与日期。
