# MULTI-2D.2026.3 软件梳理文档

> 一份针对 MULTI-2D.2026.3（1D/2D 辐射流体动力学程序）的整体架构、模块构成、算例库与运行方法的中文梳理文档。
> 主要参考：`README.md`、`INSTALL`、`R94`、`.s96_base`、`r94/*/MODINFO`、`r94/26_MULTI_documents/2026_MULTI-2D_tutorial.tex`、`cases/*/User.r` 等本地源文件。

---

## 1. 概述

**MULTI-2D** 是由 Rafael Ramis（马德里理工大学）等人开发的一维 / 二维 **辐射磁流体力学（R-MHD）模拟程序**，主要用于惯性约束聚变（ICF）、等离子体物理、高能量密度物理、激光—等离子体相互作用、重离子束沉积等领域的数值模拟。

本目录 `MULTI-2D.2026.3` 是 2026 年发布的最新稳定版本（许可协议见 `LICENCE`，MIT，Copyright (c) 2026 Rafael Ramis Abril），其物理核心沿袭 `MULTI-2D` 一贯的「三角形非结构网格 + 拉格朗日 / 欧拉 / ALE」框架，并以 **r94 模块化脚本体系**作为外围环境：

- **物理核心**：`m2d-core-9.1`（控制总驱动）、`m2d-hydro2-7.0.4`（MHD 拉格朗日流体）、`m2d-radia-8.0`（辐射输运）、`m2d-heat-7.0`（电子热传导）、`m2d-ray-7.0`（激光光追）、`m2d-hib-7.0`（重离子束沉积）、`m2d-ALE19-8.0`（ALE 网格投影）、`m2d-geometry-7.0`（几何拓扑）。
- **网格生成**：`malla-6.0`（规则矩形 + 非规则三角剖分）+ 公共域 `triangle`（Shewchuk）。
- **物态 / 光学参数**：`matter-3.1`（物态接口） + 一系列 `mat_<元素>-1.0` 物态与不透明度表（Au、Al、Be、C、DT、Si、W 等）。
- **图形界面 / 后处理**：`ProgManager-1.4`、`CaseManager-1.1`、`mpp22-2.1`、`mpp13-3.1`、`mgs-4.1`、`plot-1.1`、`gr-1.1` 等。
- **1D 版本（MULTI-IFE 2015）**：作为附带模块 `MULTI-IFE-2015` 提供，独立 gfortran 编译。

整个代码以 **C + 自定义 r94 脚本语言（先转译成 C 再编译）** 为主，少量 Fortran（重离子 / IFE 部分）。

---

## 2. 总体目录结构

```
MULTI-2D.2026.3/
├── README.md            # 简要安装/运行说明
├── INSTALL              # 一键安装脚本（调用 installer/main.sh）
├── R94                  # 启动 GUI 的总入口（ProgManager2025）
├── LICENCE              # MIT 许可
├── .s96_base            # 模块路径表（核心：模块名 → 路径的映射 + 别名）
├── 2026-06-1619:11:20.log   # 安装日志（含 50+ 模块解压/编译流水）
├── archive/             # 各模块的原始打包（plain tar，未压缩）
├── installer/           # INSTALL 解开后得到的安装脚本集合
├── r94/                 # 全部模块源代码、编译产物（lib.a）、物态表、文档
│   ├── 26_MULTI_documents/   # PDF 文档 + 教程 + 算例缩略图
│   ├── boot-3.2/             # 模块管理与编译驱动脚本（x.2.* 系列）
│   ├── kernel-4.4/           # r94 内核（DStart/DLibera/DStop + D.h）
│   ├── lib-4.3/、libA-1.2/   # r94 基础库
│   ├── transl-4.3/           # r94 → C 翻译器
│   ├── m2d-*/                # MULTI-2D 物理模块族（详见 §4）
│   ├── malla-6.0/、triangle/ # 网格生成
│   ├── matter-3.1/、mat_*/   # 物态 / 不透明度数据
│   ├── ProgManager-1.4/、CaseManager-1.1/、Widgets-*/WT-*/X-*/windows-3.1/、g94-3.1/
│   │                          # GUI 相关模块
│   ├── mpp22-2.1/、mpp13-3.1/、mgs-4.1/、plot-1.1/、gr-1.1/
│   │                          # 后处理与图形
│   ├── multi_data-2.2/       # m1d/m2d/multifs 数据文件 I/O
│   ├── m2d-cases-8.1/        # 22 个标准算例的 tar 归档
│   └── MULTI-IFE-2015/、m1d_env-1.4/、m2d_env-1.2/
│                              # 1D MULTI-IFE 及其后处理
├── cases/               # 已展开的标准算例工作目录（22 个 M2D_* + 4 个 2015*）
└── work/                # 默认工作目录（GUI 启动后落到这里）
```

---

## 3. r94 模块化体系（核心设计思想）

MULTI-2D 不采用传统单一可执行文件的设计，而是把整个代码组织成约 **50 个独立的"模块（module）"目录**。每个模块目录里都包含：

| 文件 | 作用 |
|------|------|
| `MODINFO` | 模块元信息：`name`、`author`、`info`（一句话描述）、`parent`（父版本）、`cdate`/`ldate` |
| `DEPENDENCES` | 依赖的其他模块名（每行一个），用于自动递归链接 |
| `FILELIST` | 打包清单（用于 `tar` 归档） |
| `CHECKSUM`、`LOCK` | 校验和与安装锁 |
| `*.r` | r94 脚本源代码（用户/物理逻辑） |
| `*.c`、`*.o`、`*.t` | 翻译器生成的 C 源、目标文件、引用表 |
| `lib.a` | 该模块编译后归档的静态库 |
| `D.h` | 从 `kernel-4.4/D.h` 拷贝过来的内核头文件 |

### 3.1 模块路径解析

环境变量 `$MULTI` 是程序根目录的绝对路径（由 `R94` 脚本设置）。`.s96_base` 是路径表，例如：

```
default:$MULTI/r94/m2d-core-9.1:m2d-core-9.1:
alias:$MULTI/r94/m2d-core-9.1:m2d-core-9.0:
alias:$MULTI/r94/m2d-core-9.1:m2d-core-7.0.9:
...
```

这意味着 `User.r` 写 `DEPENDENCES` 时引用旧版本号 `m2d-core-7.0.7` 也能透明地映射到当前版本 `m2d-core-9.1`。

### 3.2 r94 语言

r94 是一种类 C 的脚本语言，源代码以 `.r` 为后缀。编译流水如下（详见 tutorial 第 2 章）：

```
User.r ──(transl-4.3/r94)──> User.c ──(gcc -c)──> User.o ──(ar)──> lib.a
                                                                    │
                                                  x.2.build multi2d │
                                                      ↓             ↓
                                       自动生成 main.c，链接 lib.a 与
                             $MULTI/r94/{lib-4.3, kernel-4.4}/lib.a → 可执行文件 multi2d
```

入口约定：源文件中至少定义一个 `entry multi2d()` 或 `entry multi()`，编译器据此生成名为 `_multi2d0` / `_multi0` 的 C 函数，由 `main.c` 调用。

### 3.3 编译驱动脚本（boot-3.2/x.2.*）

| 命令 | 作用 |
|------|------|
| `x.2.library [dir]` | 把目录里所有 `*.r` 翻译成 `*.c`、编译、归档为 `lib.a` |
| `x.2.build <name>` | 在当前目录生成 `main.c` 并链接出可执行 `<name>`；自动递归读取 `DEPENDENCES` 拼接链接列表 |
| `x.2.linklist [dir]` | 输出当前目录需要的所有 lib.a 完整路径列表 |
| `x.0.find <module>` | 在 `.s96_base` 中查找模块，返回绝对路径 |
| `x.1.install / x.1.alias / x.1.save` | 模块安装与别名管理 |

每个算例目录的 `RUN` 脚本就是 `x.2.library && x.2.build multi2d` 加上 `nohup` 后台执行。

---

## 4. 主要模块详解

下表汇总了 `r94/` 下所有核心模块（按功能分组）：

### 4.1 物理核心（MULTI-2D 物理包）

| 模块 | info（取自 MODINFO） | 关键文件 | 作用 |
|------|----------|----------|------|
| **`m2d-core-9.1`** | "Multi2d (control package)" | `M20_Step.r`、`M20_Hydrodynamics.r`、`M20_Transport.r`、`M20_RayTracing.r`、`M20_HIB.r`、`M20_Project.r`、`Hydro.r`、`Material.r` | 总控制包；定义核心数据结构 `hydro`（节点位置、速度、能量、质量、EOS 量等），并提供时间推进总驱动 `M20_Step()` |
| **`m2d-hydro2-7.0.4`** | "MHD Lagrangian 2D hydrodynamics for unstructured grids" | `M19_HydroAcc.r`、`M19_LorentzF.r`、`M19_SphericalF.r`、`M19_ThermalF.r` | 拉格朗日流体求解器；计算加速度（热压力、洛伦兹力、球面几何修正）、人工粘性、节点更新 |
| **`m2d-radia-8.0`** | "MULTI-2D (radiation transport package)" | `M19_Radia.r`、`M19_I_mesh.r`、`M19_I_radia.r` | 多群扩散 / 离散纵标类辐射输运；入口 `M19_Radia()` 接收 `topo`、温度、不透明度（自由程）等 |
| **`m2d-heat-7.0`** | "MULTI-2D version 7.0 (heat transport package)" | `M19_Heat.r` | 电子（及离子）热传导，Spitzer 经典热导 + 自由流限制 |
| **`m2d-ALE19-8.0`** | "ALE library for MULTI-2D" | `M19_ALE_main.r`、`M19_I_ALE_*.r` | ALE（任意拉格朗日—欧拉）投影库；把扭曲网格上的守恒量二阶保守地投影到参考网格 |
| **`m2d-ray-7.0`** | "2D ray tracing package" | `M19_ray2d_init.r`、`M19_I_ray_trace.r`、`M19_I_ray2d_grad.r`、`M19_I_ray2d_topo.r`、`M19_I_ray_entry.r` | 激光光追（含折射），输出沉积剖面 `depo` 与光线轨迹 `rays` |
| **`m2d-hib-7.0`** | "Heavy Ion Beam deposition package" | `M19_HIB.r`、`M19_I_Coral.r` | 重离子束沉积（无折射光追 + 范围表），可被激光算例（无折射时）借用 |
| **`m2d-geometry-7.0`** | "geometry processing of 2D unstructured grids" | `M19_Geometry.r`、`NewTopo.r` | 由 `ma` 三角剖分构建全部拓扑表（`tn`、`tw`、`wn`、`wt`、`tt`、`bw`） |
| **`m2d-unix-7.0`** | "O.S. interface" | — | 操作系统接口（系统调用、时间统计等） |
| **`m2d-hib-7.0`** | — | — | 与重离子束配套的 Coral 数据接口 |

### 4.2 物态与材料数据

| 模块 | 说明 |
|------|------|
| `matter-3.1` | 物态接口库；定义 `Mat2013()` 结构与理想气体 IEOS（`Mat2013_GasIEOS`）、内能/压力插值、元素表 `Mat2013_EleTab`，以及读入外部 EOS 表 |
| `mat_DT-1.0` | 氘氚混合物 EOS + Planck/Rosseland 不透明度 |
| `mat_Au-1.0` | 金（含 0.3 μm 群的多群不透明度 `AU_op03*`） |
| `mat_Al-1.0` | 铝 |
| `mat_Be-1.0` | 铍 |
| `mat_C-1.0` | 碳 |
| `mat_Si-1.0` | 硅（液体/蒸汽反演表 `SI.INV*`） |
| `mat_W-1.0` | 钨（Tungsten2015 系列） |
| `mat_CPC` | 杂项材料（Au、Be 等的辅助表） |
| `mat_2019` | 算例用杂项：`Al/CHOQG/Cu/Fe/...` MPQEOS 表 |

### 4.3 网格生成

| 模块 | 说明 |
|------|------|
| `malla-6.0` | MULTI 自带的非结构网格生成包。提供 `ma()`（创建句柄）、`ma_point/ma_line/ma_rect/ma_fill_area/ma_divide/ma_simple_quadrant` 等；支持均匀/几何级数布点（`ma_d`）、弧线（曲率半径）、多边形区域自动三角剖分 |
| `triangle` | Jonathan Shewchuk 的公共域三角剖分程序，由 `ma_fill_area` 调用 |

### 4.4 内核与基础库

| 模块 | 说明 |
|------|------|
| `kernel-4.4` | r94 内核。提供 `DStart/DLibera/DStop` 与全局头文件 `D.h`（所有 `.c` 都 `#include`），定义动态字符串、结构体、内存管理等最基本例程 |
| `lib-4.3` | 通用算法库：插值、排序、向量运算、I/O（如 `fileread`、`algorithm_interpola_lin1d`、`algorithm_components`、`algorithm_vector`） |
| `libA-1.2` | lib 的补充 |
| `transl-4.3` | r94 → C 翻译器；可执行文件 `boot-3.2/r94` |
| `boot-3.2` | 模块管理脚本集（`x.0.*` ~ `x.2.*`），见 §3.3 |

### 4.5 GUI 与后处理

| 模块 | 说明 |
|------|------|
| `ProgManager-1.4` | 主开发/管理 GUI（`ProgManager2025`），含交互式文档检索 |
| `CaseManager-1.1` | 案例 GUI（`Manager2015`），克隆/清理/运行/归档/安装案例 |
| `Widgets-1.1/1.3`、`WT-1.2`、`X-1.3`、`windows-3.1` | X-Window 工具包层（按钮、菜单、滚动条、对话框） |
| `g94-3.1` | 基础绘图库 |
| `mgs-4.1` | MULTI Graphic System（颜色表、绘图原语） |
| `plot-1.1`、`gr-1.1` | 高层图形例程 |
| `mpp22-2.1` | Multi-Post-Processor 22 v2.1，主可视化窗口（云图 / 矢量图） |
| `mpp13-3.1` | 早期（1995）动画式后处理，仍保留可用 |
| `multi_data-2.2` | 二进制 m1d / m2d / multifs 输出文件的读写 |
| `m2d_env-1.2`、`m1d_env-1.4` | 各类杂项后处理工具 |

### 4.6 1D MULTI-IFE

| 模块 | 说明 |
|------|------|
| `MULTI-IFE-2015` | 1D 多群辐射流体代码（自包含 `m150304.f95`，`gfortran m150304.f95` 即可生成 `a.out`）。包含 4 个测试输入：`2015CPC`（平面 Al+Au 靶）、`2015DIR`（直接驱动）、`2015IND`（NIF 间接驱动 Be 靶）、`2015PRE`（150 nm Al 箔超短脉冲） |
| `cases/2015CPC`、`cases/2015DIR`、`cases/2015IND`、`cases/2015PRE` | 对应的展开案例目录 |

---

## 5. 物理模型与求解流程

### 5.1 核心数据结构 `hydro`

由 `m2d-core-9.1/Hydro.r` 中的 `Hydro(topo,gmode,xsymmetry,ntemp)` 创建。关键字段（节选自源码注释）：

- **几何**：`topo`（拓扑结构）、`gmode`（1=平面 XY，2=轴对称 ZR）、`xsymmetry`（X=0 是否对称面）、`ntemp`（1 或 2 温度模型）
- **状态量**：`p`（节点位置）、`v`（节点速度）、`E` 或 `Ee`+`Ei`（节点内能）、`mass`（每材料三角形质量）、`bz`（方位角磁场，可选）
- **导出量**：`area`/`vol`/`rho`/`tmass`/`nmass`
- **EOS**：`P`/`T` 或 `Pe`/`Te`/`Pi`/`Ti`，`c²`（声速平方）、`am`/`zm`/`zeff`/`ne`/`ecf`
- **附加量**：`TR`（辐射温度）、`lambda`（自由程）、`depo`（束沉积）、`rays`（光线轨迹）等

### 5.2 时间推进总驱动 `M20_Step`

源文件：`m2d-core-9.1/M20_Step.r`。算法骨架（按需开启）：

```
1. HydroEOS()                          # 计算热力学量
2. if control.plasma:                  # 等离子体参数
     HydroIonization() / HydroCollfreq()
3. 复制 hydro_save → hydro
4. while 步进成功不成功反复 halve dt:
     a. control.plasma  → M20_Relax()                     # 电子-离子温度弛豫
     b. control.fusion  → control.fusion.f(hydro,dt,…)     # 用户热核反应包
     c. control.hydro   → M20_Hydrodynamics()              # 拉格朗日流体
     d. control.hib     → M20_HIB()                        # 重离子束 / 无折射激光
     e. control.ray     → M20_RayTracing()                 # 折射光追
     f. control.transport → M20_Transport()                # 辐射 + 热传导
   返回 status.value，最大值 > 1 ⇒ dt 减半重试，否则按 0.5 目标估算下步 dt
```

其中：

- **`M20_Hydrodynamics`**（`m2d-core/M20_Hydrodynamics.r`）调用 `m2d-hydro2-7.0.4` 中的加速度子程序（`M19_ThermalF`/`M19_LorentzF`/`M19_SphericalF`），含人工粘性 `kq1`、`kq2` 与 `qmode`，CFL 限 `max_cfl`，最大相对体积变化限 `max_var`，对称性选项 `spherical`。
- **`M20_Transport`** 调用 `m2d-radia-8.0` 的 `M19_Radia`（扩散风格，需要用户提供 `freepath(4)`、可选 `heatcond(4)` 与 `freeflux(4)`）和 `m2d-heat-7.0` 的 `M19_Heat`。`nphis` 给出 4π 立体角方向的离散（典型 `2:4:4:4:4:2`）；`Tmaxvar` 限制单步温度相对变化。
- **`M20_RayTracing`** 调用 `m2d-ray-7.0` 实现激光追踪，用户在 `control.ray.rays_f` 提供光线初始化回调，返回每束光的起点、方向、强度。
- **`M20_HIB`** 调用 `m2d-hib-7.0` 的 `M19_HIB`，按用户给定的能量—射程表 `eout_f` 沿光线沉积。
- **`M20_Project`** + `M20_Project_Test`（`m2d-core`）+ `m2d-ALE19-8.0`：当拉格朗日网格扭曲超阈值时，把当前网格上的状态二阶保守投影回参考网格（即欧拉 / ALE 步）。
- **`HydroOutput` / `HydroOutputAtTimes`**：写出二进制快照文件（命名为时间值，如 `0`、`1.2e-9`、`5` 等），伴随同名 `.d` 描述文件。

### 5.3 入口循环（典型 User.r 结构）

```r
entry multi2d()
{
   hydro    = ...;                # 用 malla + NewTopo + Hydro + HydroAdd 构造
   hydro.dt = ...;
   control  = struct();
   struct(control,<hydro>,    M20_Hydrodynamics_Control());
   struct(control,<transport>,M20_Transport_Control());   # 按需
   struct(control,<ray> / <hib> / <plasma> / <fusion> / <project>, ...);

   hydro1 = hydro;
   while( hydro1.time < tmax ){
      hydro2 = M20_Step(control,hydro1);
      if(M20_Project_Test(hydro2,hydro,control.project))   # 仅 Euler/ALE 案例
         hydro2 = M20_Project(hydro2,hydro,control.project);
      HydroOutputAtTimes(hydro1,hydro2,times);
      hydro1 = hydro2;
   }
}
```

---

## 6. 标准算例库（22 个 M2D_* + 4 个 2015*）

所有算例位于 `cases/`，源代码（`User.r` + 可能的 `model.r`/`Lib.r`/`Fusion.r`）位于 `r94/m2d-cases-8.1/M2D_*` 归档中。下表按物理类型分组列出。

### 6.1 纯流体（Eulerian / Lagrangian）测试

| 算例 | 关键词 | 主要内容 |
|------|--------|----------|
| **M2D_Taylor_110** | Eulerian 单温 | 二维 Taylor 不稳定性测试。重力 `g=0.1`，水平密度阶跃 + 静力学平衡密度剖面，64×32 网格，`times = 0…250 * 0.2`，作为 Eulerian 流体 + ALE 投影的最小验证 |
| **M2D_RT_130** | Eulerian 单温 | 平面几何单模 Rayleigh-Taylor 不稳定性。`xmin=0, xmax=4, ymax=0.5`，初态为静力学平衡的双密度层 + 余弦速度扰动（振幅 `v0=0.05`），前 2.8 时间单位强制拉格朗日，之后开启投影 |
| **M2D_Channel_110** | Eulerian 单温 | 超声速通道 + 障碍物。理想气体 γ=5/3，入口 ρ=0.001、T=273/30605 eV、v=10⁶ cm/s，最大 CFL=0.5，固定时间步长 0.5e-7 |
| **M2D_Karman_130** | Eulerian 单温 | 高超声速通道（v=10⁵ cm/s）含圆柱障碍物，类 Karman 涡街演示。平面几何 `gmode=1` |
| **M2D_Hyper_130** | Eulerian 单温 | 高超声速风洞含 Mercury 飞船模型；同 Karman 系列 |
| **M2D_Collision_110** | Eulerian 单温 + 真实 EOS | Al 弹丸撞击 Al 靶，验证实际 EOS（不是理想气体）在欧拉流体下的行为。`max_cfl=0.5, max_var=0.5, positive_P=1` |
| **M2D_Implo_110** | Lagrangian 单温 | 球形内爆靶（DT 气体 + DT 冰层），检验拉格朗日流体**球对称保持**能力。带 Legendre 模数 12、振幅 0.001 的初始扰动 |
| **M2D_Jet_110** | Eulerian + 化学反应 | Jet 形成与相互作用；自定义 `reaction(hydro2)` 步骤 |

### 6.2 辐射输运

| 算例 | 关键词 | 主要内容 |
|------|--------|----------|
| **M2D_Radia_110** | 仅辐射输运 | 检验 `M19_Radia`。两个区域（自由程分别为 0.006 / 0.00006），外侧施加 100 eV 热浴辐射边界条件 `external(4)`。`nphis = 4:4:4:4`，反射边界 `reflex=1` |
| **M2D_Cone_110** | Eulerian + 多材料 + 辐射 | 锥导 ICF 内爆末期；DT + Au 双材料，初始速度场 `v = -3e7 * (rc/0.025)` 向心，6 个方向离散 |

### 6.3 激光—等离子体

| 算例 | 关键词 | 主要内容 |
|------|--------|----------|
| **M2D_Foil_110** | Lagrangian + 激光(HIB 无折射) + 辐射 + 热传导 | 平面多层靶（CH/Au/...）受激光辐照 + 热传导 + 辐射。波长经 `Material_Laser` 给出射程；`reflex=0.5` |
| **M2D_ThinFoil_120** | Lagrangian + 无折射激光 + 辐射 | 薄箔（150 nm 量级）激光辐照，沉积按 `D/V`、`D/M` 输出 |
| **M2D_Laser_Foil_130** | Lagrangian + 折射光追 + 双温 + 辐射 + 热传导 | 完整激光—箔物理：含折射的 `M20_RayTracing`、`M20_Break_Cells` 把扭曲四边形分裂成两个三角形，Spitzer 热导 + 多群辐射 |
| **M2D_Hohlraum_110** | Lagrangian + 激光 + 辐射 + 热传导 | 模拟间接驱动的**黑腔（Hohlraum）**：Be 腔 + Au 壁 + 低密度 H 气体，4 个区域。35 nm 激光从 LEH 进入，方向分布 `nphis=2:4:4:6:6:4:4:2`。该算例的 100 多个时间快照已预存于 `cases/M2D_Hohlraum_110/`（含 `0`、`1e-10`、…、`1e-8` 等） |

### 6.4 ICF 内爆 / 点火

| 算例 | 关键词 | 主要内容 |
|------|--------|----------|
| **M2D_Laser_110** | Lagrangian + 球对称保持 + 折射光追 + 辐射 + 热传导 | **直接驱动胶囊内爆**：DT 气 + DT 冰 + CH 烧蚀层，激光波形取自 Temporal 等 *Eur. Phys. J. D* 73:5 (2019)。`spherical=1, qmode=5, pfactor=2`，方位角滤波 `smooth_laser / smooth_radia`。设置自动终止条件 `dt<1e-15` 或 `Tmax>1e6` |
| **M2D_Laser_ALE_120** | ALE + 其余同上 | 上一例的 ALE 版本：当网格扭曲时调用 `M20_Project` 投影到球形参考网格 |
| **M2D_Laser_Fusion_130** | ALE + 全物理 + DT 核反应 | 上一例再加 `HydroFusion(3)`（来自 `Fusion.r`）：DT 燃烧 + α 粒子输运 + 中子输运。预计算结果：吸收激光 400 kJ，核产额 10 MJ，与 1D 发表值（270 kJ / 11.9 MJ）接近 |
| **M2D_Fusion_110** | Eulerian + 双温 + 辐射 + 热核反应 + α/中子输运 | 已压缩 ICF 芯部的点火过程。DT 核心（ρ=50）+ He + Au 推层，热斑 T=6000 eV，外部 100 eV，模拟时长 500 ps |

### 6.5 重离子束驱动

| 算例 | 关键词 | 主要内容 |
|------|--------|----------|
| **M2D_Converter_110** | Lagrangian + HIB | 简单圆柱碳靶受 HIB 沉积，30° 入射 40000 条射线 |
| **M2D_Cylinder_110** | Eulerian + HIB | DT 核 + Au 推层 + Fe 吸收层圆柱靶（"rotating beam"），双脉冲 HIB（125 GeV Bi⁻） |
| **M2D_XTarget_110** | Eulerian + HIB | Henestroza et al. *Phys. Plasma* (2011) 的 X 靶构型；Rb 离子束 85.468 / 37 |

### 6.6 其他特殊

| 算例 | 关键词 | 主要内容 |
|------|--------|----------|
| **M2D_Ablation_110** | Eulerian + 热传导 + 重力 | 烧蚀 Rayleigh-Taylor 不稳定性，**无量纲**变量；用 `ablation_wave.c`（解析烧蚀波解）做初值；典型 `tabl=12.5, vabl=0.133, kbar=1.07e-6, g=1`，横向波长 1.2 |
| **M2D_Converter_110** | （见上） | — |

### 6.7 1D MULTI-IFE 测试（Fortran）

| 算例 | 描述 |
|------|------|
| **2015CPC** | 平面 Al(2 μm) + Au(0.2 μm) 靶受 3×10¹⁴ W/cm²、300 ps、0.44 μm 激光；CPC 1988 经典案例 |
| **2015PRE** | 150 nm Al 箔受 10¹⁵ W/cm²、150 fs、400 nm 超短脉冲（Ramis *CPC* 183 (2012) 637） |
| **2015IND** | NIF 间接驱动 Be 烧蚀层靶（Lindl *Phys. Plasmas* 1995）；20 ns、球形几何、辐射温度从 80 eV 升至 250 eV |
| **2015DIR** | 直接驱动相关输入 |

---

## 7. 安装

依赖：Linux/Unix、`gcc`、`gfortran`、X11 开发包、`xterm`。

```bash
# 1. 解压发布包
tar -xvf MULTI-2D.2026.3.tar.gz
cd MULTI-2D.2026.3

# 2. 运行 INSTALL（若 installer/ 已存在则直接执行，否则从 archive/ 解出）
./INSTALL
```

`INSTALL` 内部依次执行 `installer/install_core_2026.sh`、`install_GUI_2026.sh`、`install_m2d-9.1_2026.sh`、`install_MPP_2026.sh`、`install_mpp13_2026.sh`、`install_MULTI-IFE_2026.sh`，把 `archive/` 中各模块解压到 `r94/<module>`，对 `*.r` 调用 `transl-4.3` 翻译为 `*.c`、`gcc` 编译并 `ar r lib.a`；最后建立 `.s96_base`、`cases/`、`work/` 与顶级 `R94` 启动脚本。安装日志在根目录 `2026-06-1619:11:20.log`。

> 若需要重新初始化某个模块，删除其 `LOCK` 文件后重跑 `INSTALL` 即可。

---

## 8. 运行方式

### 8.1 GUI 总入口（推荐）

```bash
./R94
```

`R94` 脚本设置 `$MULTI`、把 `r94/boot-3.2` 加入 `PATH`，并在 `work/` 下生成一个 ProgManager2025 的可执行并后台启动。GUI 包含：

- **ProgManager2025**：主面板，菜单 `Launch` 启动子工具；下部蓝色矩形支持**拖放例程名**直接获取交互式文档
- **Manager2015**（CaseManager-1.1）：列出 `cases/*`，菜单 `Case` 提供 `New / Run / Clear / Delete / Archive / Install`
- **mpp22**：主可视化窗口（云图）
- **Table**：列出某 case 的可用时间帧 → 可用变量
- **mpp13**：1995 年风格的动画式云图后处理

### 8.2 命令行（无 X11 环境或脚本化）

每个 case 目录都有一个 `RUN` 文件，内容大致：

```bash
x.2.library           # 翻译 + 编译 + 归档 lib.a
x.2.build multi2d     # 生成 main.c 并链接出 multi2d（部分案例是 multi）
echo nada > ktag
cat > proceso <<EOF
/usr/bin/time a.out>>output 2>>cputime;rm ktag
EOF
nohup sh proceso &
```

操作流程：

```bash
export MULTI=/path/to/MULTI-2D.2026.3
export PATH=$PATH:$MULTI/r94/boot-3.2:.
cd $MULTI/cases/M2D_Radia_110
./RUN                  # 后台启动；用 ls ktag 检查是否仍在运行
tail -f output         # 查看运行日志
```

输出说明：

| 文件 | 含义 |
|------|------|
| `output` | 程序 stdout（每个时间步的摘要：dt、CFL、沉积量、产额等） |
| `cputime` | `/usr/bin/time` 的 stderr（user/sys/wall 时间） |
| `ktag` | 运行标记（存在 = 仍在跑） |
| `<t>` 与 `<t>.d` | 时刻 `t` 的二进制快照 + 字段描述 |
| `proceso` | 实际执行的单步 shell 脚本 |
| `lib.a`、`User.o`、`User.c`、`User.t`、`a.out` | 编译产物 |

### 8.3 单步手动（教学用，见 tutorial 第 2 章）

```bash
# 在 case 目录中
x.2.library
x.2.build multi2d
./multi2d            # 前台运行，直接看 stdout
```

### 8.4 1D MULTI-IFE 算例

每个 2015* 目录的 `RUN` 内容：

```bash
module=`x.0.find MULTI-IFE-2015`
cp -s $module/m150304.f95 multi.f95
gfortran multi.f95 -o multi 2>>output
cp -s data.in fort.12
ln -s $module/tables tables
nohup sh proceso &     # 实为 /usr/bin/time multi>>output 2>>cputime;rm ktag
```

只需 `cd cases/2015CPC && ./RUN`。

---

## 9. 后处理与可视化

1. 启动 GUI：`./R94`
2. 在 Manager2015 中选 case，Table 选时间 → 变量，mpp22 立刻出图
3. 常用变量名（写在 `.d` 文件里）：`rho`（密度）、`T` / `Te` / `Ti`（温度）、`P` / `Pe` / `Pi`（压力）、`TR`（辐射温度）、`v`（速度）、`ne`（电子密度）、`depo` 或 `D/V`（沉积密度）、`ct`（三角形类型）
4. 用户可以在 `User.r` 中通过 `m2d_write("name", array)` 注册自定义输出变量，并用 `hydro.output = 'myoutput(1)'` 把回调挂进快照
5. 老式动画后处理：`mpp13`（动画 film 模式，适合做演示）
6. 程序间通过 X11 ClientMessage 通信，因此只要几个窗口都打开，选择会自动联动

---

## 10. 关键文件 / 数据结构速查

| 项 | 路径 / 名称 | 说明 |
|----|-------------|------|
| 模块路径表 | `.s96_base` | 模块名 ↔ 路径，含别名 |
| 案例元清单 | `cases/<case>/FILELIST` | 归档保留文件清单 |
| 案例依赖 | `cases/<case>/DEPENDENCES` | 编译时需要的模块名 |
| 案例脚本 | `cases/<case>/RUN` | 编译+运行 |
| 主程序 | `cases/<case>/User.r` | 用户物理逻辑入口 `entry multi2d() / multi()` |
| 辅助源 | `cases/<case>/model.r`、`Lib.r`、`Fusion.r` | `User.r` 调用的辅助函数 |
| 快照 | `cases/<case>/<time>`（无后缀二进制） | 由 `HydroOutputAtTimes` 写出 |
| 快照描述 | `cases/<case>/<time>.d` | 字段名 + 偏移 + 长度 |
| 模块元信息 | `r94/<mod>/MODINFO` | 名称、作者、info、parent、时间戳 |
| 模块依赖 | `r94/<mod>/DEPENDENCES` | 链接时需要的其他模块 |
| 模块库 | `r94/<mod>/lib.a` | 编译产物 |
| 文档 | `r94/26_MULTI_documents/*.pdf` | tutorial、multi_manual、r94_manual、ray_tracing、mgs_manual、MULTI-IFE、各时期发表的论文 |

---

## 11. 学习路径建议

1. 读 `r94/26_MULTI_documents/2026_MULTI-2D_tutorial.pdf`（或同目录 `.tex`），按 `example_00 → example_09` 完整复现一遍，理解 r94 语言、网格生成、最小流体 → 欧拉投影 → 激光光追 → 双温 + 辐射 → 烧蚀箔的渐进式构建
2. 读 `multi_manual.pdf`（MULTI-2D 主体手册）、`2009_r94_manual.pdf`（r94 语言手册）
3. 选一个简单案例（如 `M2D_Radia_110`）跑通，再读其 `User.r` 与 `output`，对照本文件 §5 的求解流程
4. 复杂案例（`M2D_Laser_Fusion_130`、`M2D_Hohlraum_110`）涉及激光 + 辐射 + 双温 + ALE + 核反应全套物理，可作为深入理解的样板
5. 自定义新算例：从最相似的现成 case 用 `Manager2015 → Case → New...` 克隆，再修改 `User.r`

---

## 12. 常见注意点

- **运行前**确认 `$MULTI` 已正确指向根目录，且 `$MULTI/r94/boot-3.2` 在 `PATH` 中（`R94` 脚本会自动设置一次，但命令行直跑要手动）
- **案例目录里残留文件**（如 `0`、`1.2e-9` 等大堆快照）属于上次运行的产物；`Manager2015 → Case → Clear` 会按 `FILELIST` 清理
- **ktag** 文件存在表示后台任务在跑；如果异常退出，需手动 `rm ktag`
- **X11** 是 GUI 必需；远程使用请开 X11 forwarding 或 VNC
- **r94 语法的例程引用**写作 `'name(N)'`（带单引号和参数个数），如 `'laser(5)'`、`'Material_Freepath(4)'`
- **物态表**是分群的；不同案例使用不同群结构（如 `AU_op03*` 是 0.3 μm 群），改材料时需对应
- 案例名末尾的数字（`_110`、`_120`、`_130`）大致对应 m2d-core 的版本系列：`110` ↔ m2d-core-7.0.6、`120` ↔ 7.0.7、`130` ↔ 7.0.8；当前都已通过 `.s96_base` 别名指向 `m2d-core-9.1`

---

> 文档整理完毕。如需对某个模块或算例做更深入的代码级解读，可指定具体子目录，例如 `r94/m2d-radia-8.0` 或 `cases/M2D_Hohlraum_110/User.r`。
