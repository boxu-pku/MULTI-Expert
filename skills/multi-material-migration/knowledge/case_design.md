---
title: 验收算例设计模板（validation_cases/<X>Check）
skill: multi-material-migration
category: recipes
source_anchors:
  - 材料迁移验证规范.md §3
  - work/eos_opacity_tools/batch_migrate.py:L172-L243
  - validation_cases/TiCheck/data.in:L12-L86
doc_ref: "材料迁移验证规范.md §3"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 验收算例
  - XCheck
  - 设计模板
  - 辐射浴
---

# 验收算例设计模板

> 本体：《材料迁移验证规范.md §3》。生成器：`batch_migrate.py` 的 CASE_TEMPLATE（L172-L243）+ make_case()（L246-L261）。基准实例：`validation_cases/TiCheck/`。

## 1. 设计原则

**简单、快速、同时激发 EOS+不透明度+电离三张表**：
- 平面几何 + 单材料平板 + 恒定辐射浴 → 辐射波烧入，同时扫过 EOS（ρ,T 大区间）、
  不透明度（多群输运）、Zeff（电离度演化）
- 秒级完成（~121 步）→ 可批量回归
- 输出频率 ns_bout=1 → 热图分辨率（E 节要求记录数 ≥50）

## 2. 物理设计参数（模板默认）

| 项 | 值 | 说明 |
|---|---|---|
| 几何 | `igeo=1`（平面） | — |
| 网格 | `nc=20`，`thick=2.0e-4`（2 μm） | 单一材料平板 |
| 密度 | `r0={rho0}` | **固体密度**（例外：Kr 用气体 3.749e-3，见下） |
| 初温 | `te0=ti0=0.03` eV | 须 ≥ 表 T 下限 |
| 驱动 | `betar=1, itype=2, trad=100, tau=1e-9` | 右侧 100 eV 恒定辐射浴 |
| 时长 | `texit=1.2e-9`，`dtmax=dtinit=1e-11` | 约 121 步 |
| 开关 | `iradia=1, ihydro=1, inegpre=0, zmin=0.1` | 无激光块 |
| 输出 | `ns_bout=1, dt_bout=1e-11` | 逐步记录 |
| 材料块 | eeos/ieos/z/planck/ross 五表，`eps_id=-1` | LTE |

## 3. 文件构成（克隆自 TiCheck）

```
validation_cases/<X>Check/
├── data.in        # 按模板生成（batch_migrate make_case）
├── RUN            # 克隆 TiCheck（gfortran 链）
├── CLEAR          # 克隆 TiCheck（⚠ 验收产物生成后禁止执行）
└── FILELIST       # "FILELIST\ndata.in\nRUN\nCLEAR\n*.png\n"
```

## 4. 密度/初温选取的红线（历史教训）

| 红线 | 违反实例 | 档案 |
|---|---|---|
| 表 ρ 上限 ≥ 10×r0（压缩裕量） | Kr 固体密度 → 辐射坍缩 ρ=1890 vs 上限 10 | `agent/pitfalls/gas-vs-solid-case-density.md` |
| 表 ρ 下限 ≪ 烧蚀稀薄区 | Diamond/Cliquid 越界 | `agent/pitfalls/eos-density-range-limit.md` |

## 4a. Hugoniot 二轮标准配置：quiet start（2026-08-19 用户定版）

EOS 入库的 Hugoniot 二轮校验算例（`make_hugoniot_cases.py` 生成）**一律启用
quiet start，参数与 BN 族验证一致**：

- `iquiet=1, tquiet=0.05`（冻结 Te/Ti<0.05 eV 冷固态单元的流体，加热后解冻）；
- 冷初态 `te0=ti0=0.03` eV（~350 K，贴参考线 300 K 初态）；
- 收益：波前驱污染消除（v_pre 归零）、能量误差最高改善 5 个量级、
  弱驱动档救活、可用档 dUs 改善 ~0.3-0.7 pct（BN 族实测，详见
  `Hugoniot校验流程.md` §一 与 `validation_cases/cBNFEOS/材料表信息.md`）；
- 工具链：需 2026-08-18 13:47 后含 quiet start 的 m150304.f95 重编译的
  multi（旧 binary 遇 iquiet 报 namelist 错）。

（注意：XCheck 一轮算例〔§2 表〕不用 quiet start，仍按模板默认。）
| te0/ti0 ≥ 表 T 下限 | Air 初温问题 | `agent/pitfalls/gas-vs-solid-case-density.md` |

选密度前：用 check_multi_file.py 输出的网格范围（或 EOS-tools eos_query）核对。

## 5. 例外与变体

- **Kr**：气体密度 3.749e-3 g/cc（清单 §四-6）
- **opc 单群材料**：planck/ross 挂 `X_OPC.PLANCK/.ROSS`（sgo 单群表，id=opc 表号），
  z_id=-1（常数 zi）——`migrate_opc_batch.py:make_case` 调用（L73-L75）
- **EOS-only 材料**：按约定**不建 1D 算例**（批次2 验收口径：格式+注册即可）

## 6. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
