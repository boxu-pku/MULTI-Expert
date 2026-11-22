---
title: 两类算例目录结构与 RUN 机制对比（1D gfortran 链 vs 2D r94 链）
skill: multi-case-runner
category: overview
source_anchors:
  - cases/2015CPC/RUN:L2-L16
  - cases/M2D_Radia_110/RUN:L1-L16
  - validation_cases/TiCheck/RUN:L2-L16
  - MULTI-2D_梳理文档.md §8.2-§8.4
doc_ref: "MULTI-2D_梳理文档.md §8"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - RUN
  - 算例目录
  - 1D
  - 2D
---

# 两类算例目录结构与 RUN 机制对比

> **TL;DR**：1D 算例（有 data.in）：RUN 软链 m150304.f95 → gfortran 编译 → 软链 data.in 为 fort.12、tables → nohup 后台。2D 算例（有 User.r）：RUN = x.2.library + x.2.build → nohup 后台。两者都用 ktag 做运行标记、proceso 做执行脚本。

## 1. 算例目录识别

| 判据 | 1D（MULTI-IFE） | 2D（M2D_*） |
|---|---|---|
| 标志性文件 | `data.in`（namelist 输入卡） | `User.r`（r94 源码，entry multi2d()） |
| 代表目录 | `cases/2015*`、`validation_cases/*Check` | `cases/M2D_*` |
| 编译链 | gfortran 直编单文件 | r94 翻译→gcc→lib.a→链接 |
| 典型时长 | 秒~分钟级 | 分钟~小时级（本轮未逐一实测） |

## 2. 1D RUN 机制（`cases/2015CPC/RUN`，16 行；TiCheck 同构）

```bash
:2  module=`x.0.find MULTI-IFE-2015`     # .s96_base 查模块路径
:4  cp -s $module/m150304.f95 multi.f95  # 软链主程序
:5  gfortran multi.f95 -o multi 2>>output
:7  cp -s data.in fort.12                # 输入卡 → fort.12
:8  ln -s $module/tables tables          # 表库软链
:14 echo nada >ktag                      # 运行标记
:16 nohup sh proceso &                   # proceso: /usr/bin/time multi>>output 2>>cputime;rm ktag
```

产物：multi（可执行）、output、cputime、fort.10、fort.11、ktag、proceso、
multi.f95/tables/fort.12（软链）、multidata.mod、block（namelist 临时文件）。

## 3. 2D RUN 机制（`cases/M2D_Radia_110/RUN`，16 行）

```bash
:1  echo "nada" >ktag
:3  x.2.library          # User.r → User.c → User.o → lib.a
:10 x.2.build multi      # 生成 main.c 并链接（依赖递归收集）
:11 mv multi a.out
:13-15 生成 proceso（/usr/bin/time a.out>>output 2>>cputime;rm ktag）
:16 nohup sh proceso &
```

产物：a.out、output、cputime、ktag、`<t>`/`<t>.d` 快照、lib.a/User.c/User.o/User.t。
（部分案例 build 的是 `multi2d` 而非 `multi`，以各自 RUN 为准。）

## 4. ktag / proceso 语义

- `ktag`：存在 = 后台任务在跑（或异常残留）；proceso 末尾 `rm ktag` 是正常结束的标志
- `proceso`：实际执行的单步 shell（RUN 生成），便于复现/手动重跑
- 异常退出 → ktag 残留，需手动 `rm ktag`（梳理文档 §12）

## 5. 清理规则

| 目录 | 规则 |
|---|---|
| `cases/*` | Manager2015 Case→Clear 按 FILELIST 清残留快照；或手工对照 FILELIST |
| `validation_cases/*` | **永久保留，禁止 CLEAR**（人工验收依据；README.md 明示） |

CLEAR 脚本语义（`validation_cases/TiCheck/CLEAR` L17-L59）：按 FILELIST 逐行展开
（含通配符）生成保留清单，删除未保留项；支持 `-n` 干跑。

## 6. 延伸阅读

- `knowledge/run_protocol.md`（标准流程）、`knowledge/output_reading.md`（判读）
- `MULTI-2D_梳理文档.md §8`

## 7. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
