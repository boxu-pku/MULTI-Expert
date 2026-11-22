---
title: 标准算例库、GUI 与后处理（R94/ProgManager/Manager2015/mpp22）
skill: multi-architecture
category: reference
source_anchors:
  - MULTI-2D_梳理文档.md §6, §8-§9
  - R94:L7-L16
  - cases/M2D_Radia_110/RUN:L1-L16
doc_ref: "MULTI-2D_梳理文档.md §6, §8, §9, §10"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 算例
  - GUI
  - mpp22
  - Manager2015
  - 后处理
  - 快照
---

# 标准算例库、GUI 与后处理

> **TL;DR**：22 个 M2D_* + 4 个 2015* 标准算例在 `cases/`；`./R94` 启动 GUI（ProgManager2025 + Manager2015 + mpp22）；快照 = 二进制时间文件 + `.d` 描述。命令行跑算例用各目录的 RUN 脚本。

## 1. 标准算例库（梳理文档 §6，cases/）

按物理类型分组（完整表格见梳理文档 §6.1-§6.7）：

| 组 | 代表算例 | 物理要点 |
|---|---|---|
| 纯流体 | M2D_Taylor_110、M2D_RT_130、M2D_Channel_110、M2D_Implo_110、M2D_Collision_110 | Eulerian/Lagrangian 验证；Taylor/RT 不稳定性；真实 EOS 碰撞 |
| 辐射输运 | M2D_Radia_110、M2D_Cone_110 | 仅输运测试；锥导 ICF 多材料 |
| 激光-等离子体 | M2D_Foil_110、M2D_ThinFoil_120、M2D_Laser_Foil_130、M2D_Hohlraum_110 | 箔靶/黑腔；折射光追、双温、热传导 |
| ICF 内爆/点火 | M2D_Laser_110、M2D_Laser_ALE_120、M2D_Laser_Fusion_130、M2D_Fusion_110 | 直接驱动内爆、ALE、DT 燃烧 |
| 重离子束 | M2D_Converter_110、M2D_Cylinder_110、M2D_XTarget_110 | HIB 沉积 |
| 其他 | M2D_Ablation_110 | 烧蚀 RT（无量纲） |
| 1D | 2015CPC/DIR/IND/PRE | 见 multi-1d-ife |

算例名尾数对应 m2d-core 版本系列（_110↔7.0.6 等），现都经别名指向 9.1（梳理文档 §12）。
算例源码在 `r94/m2d-cases-8.1/M2D_*` 归档中；`cases/M2D_Hohlraum_110/` 预存 100+ 时间快照。

## 2. GUI（梳理文档 §8.1、§9）

```bash
./R94     # 根目录脚本：设 $MULTI（L7-L10）、PATH（L11-L12），
          # 在 work/ 下构建并后台启动 ProgManager2025（L15-L16）
```

- **ProgManager2025**：主面板；菜单 Launch 启动子工具；拖放例程名取交互式文档
- **Manager2015**（CaseManager-1.1）：列出 cases/*；菜单 Case：New/Run/Clear/Delete/Archive/Install
  （New = 从最相似算例克隆——自定义新算例的推荐起点，梳理文档 §11-5）
- **mpp22**：主可视化窗口（云图/矢量图）；Table 选时间帧→变量即出图
- **mpp13**：1995 风格动画式后处理
- 程序间用 X11 ClientMessage 联动（需 X11；远程开 X11 forwarding 或 VNC）

常用可视化变量（写在 `.d` 文件里）：rho、T/Te/Ti、P/Pe/Pi、TR、v、ne、depo/D/V、ct。

## 3. 命令行运行（梳理文档 §8.2-8.4）

```bash
export MULTI=/path/to/MULTI-2D.2026.3
export PATH=$PATH:$MULTI/r94/boot-3.2:.
cd $MULTI/cases/M2D_Radia_110 && ./RUN    # 后台；ls ktag 检查是否在跑
tail -f output
```

输出文件语义（梳理文档 §8.2）：

| 文件 | 含义 |
|---|---|
| `output` | stdout（每步摘要） |
| `cputime` | /usr/bin/time 的 stderr |
| `ktag` | 存在 = 仍在跑；异常退出需手动 `rm ktag` |
| `<t>` 与 `<t>.d` | 时刻 t 的二进制快照 + 字段描述（字段名+偏移+长度） |
| `proceso` | 实际执行的单步 shell |
| `lib.a`/`User.o`/`a.out` | 编译产物 |

清理：`Manager2015 → Case → Clear` 按 `FILELIST` 清理残留快照（梳理文档 §12）。
**注意**：`validation_cases/` 例外——永久保留禁止清理（验证规范 §E）。

## 4. 后处理数据读写

- `multi_data-2.2`：二进制 m1d/m2d/multifs 文件的读写接口
- 快照由 `HydroOutputAtTimes` 写出；自定义变量用 `m2d_write` 注册（m2d_core.md §4）
- 1D fort.10 可视化走 `plot_1d_validation.py`（multi-visualize skill）

## 5. 文档资源（`r94/26_MULTI_documents/`）

tutorial（2026，含 example_00→09 渐进教程）、multi_manual、r94_manual、ray_tracing、
mgs_manual、MULTI-IFE 手册、各时期论文（梳理文档 §10-11）。

## 6. 延伸阅读

- `MULTI-2D_梳理文档.md`（全文权威）
- `multi-case-runner` skill（实际跑算例的操作协议）

## 7. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
