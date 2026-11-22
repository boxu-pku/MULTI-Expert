---
title: MULTI 数据文件容器格式总览（60 字符头 + 15 字符定宽）
skill: multi-eos-format
category: overview
source_anchors:
  - r94/matter-3.1/Mat2013_LoadMF.r:L101-L110
  - r94/matter-3.1/Mat2013_LoadMF.r:L130-L149
  - r94/matter-3.1/Mat2013_LoadMF.r:L262-L269
  - MULTI-2D_材料库迁移指南.md §1.1
doc_ref: "MULTI-2D_材料库迁移指南.md §1"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 容器格式
  - 60字符头
  - 15字符定宽
  - type分类
---

# MULTI 数据文件容器格式总览

> **TL;DR**：所有 MULTI 材料数据文件共享同一容器：60 字符表头（id|type|NR|NT/NE 四个 15 字符字段）+ 15 字符定宽数据（每行最多 4 值、跨节连续打包）。type 字段决定表类别（IEOS/mgo/sgo/Zeff）。一个文件可含多个子表顺序拼接。

## 1. 原理 / 设计动机

MULTI（无论 2D 的 r94/C 端还是 1D 的 Fortran 端）用**同一种容器格式**存全部材料数据：
状态方程、多群/单群不透明度、电离度。统一解析入口在 2D 是 `Mat2013_LoadMF`
（`r94/matter-3.1/Mat2013_LoadMF.r:L52`），1D 是 `load_table` 族
（`r94/MULTI-IFE-2015/m150304.f95:L2880`）。定宽字段设计让两个解析器都能
不依赖分隔符地按位置切分。

## 2. 容器结构（字节级）

```
表头行:  恰好 60 字符 = 4 个 15 字符定宽字段
         [id 15字符][type 15字符][NR 15字符][NT/NE 15字符]
数据体:  15 字符定宽科学计数（典型 "%15.8e"），每行最多 4 个值
         各节之间连续打包（上一节在某行中间结束，下一节从同一行继续）
特殊值:  "           -INF" → 读为 -40（log 截断）
         "            NAN" → 读为 0
```

- 60 字符检查（r94 端）：`Mat2013_LoadMF.r:L101-L102`
  `if(#a!=60){ return([["Format error: head line size != 60"]]); }`
- 15 字符定宽读取核心：`Mat2013_LoadMF.r:L262`
  `for(j=0;j<15;j++)field[j]=line[pos*15+j]; field[15]=0;`
- -INF/-40 与 NAN/0：`Mat2013_LoadMF.r:L263-L269`
- 1D 端表头格式 `(e15.0,a,2e15.8)`：`m150304.f95:L3096`；
  数据 `(4e15.8)`：`m150304.f95:L3131`
- 多子表：文件可含多个子表顺序拼接（mgo 多群表就是 NG 个子表连续存放，同 id）。

## 3. type 字段分类表

type（表头第 2 个 15 字符字段）决定表类别，字符串精确匹配：

| type 字符串 | 类别 | 含义 | 判定锚点 |
|---|---|---|---|
| `PLANCK M       ` / `ROSSELAND M    ` / `EPS M          ` | **mgo** | 多群不透明度/发射率 | `Mat2013_LoadMF.r:L110` |
| `PLANCK 1       ` / ` 0.70000000E+01` / ` 7.00000000e+00` | **sgo** | 单群 Planck 平均 | `Mat2013_LoadMF.r:L130-L132` |
| `ROSSELAND 1    ` / ` 0.40000000E+01` / ` 4.00000000e+00` | **sgo** | 单群 Rosseland 平均 | 同上 |
| `EPS 1          ` | **sgo** | 单群发射率 | 同上 |
| ` 0.60000000E+01` / ` 6.00000000e+00`（r94）；` 0.60000000e+01`（仅 1D） | **sgo** | **Zeff 电离度表** | `Mat2013_LoadMF.r:L133-L134` |
| 其他任何字符串 | **IEOS** | 反演状态方程表（兜底分支） | `Mat2013_LoadMF.r:L148-L149` |

> ⚠ Zeff type 串两个读取器接受的变体不同，双兼容写法只有 ` 0.60000000E+01`
> ——见 `knowledge/mgo_sgo_format.md §4` 与 `agent/pitfalls/zeff-type-string-variants.md`。

## 4. 三类表数据体速查

| 类别 | 数据节（顺序） | 值域 |
|---|---|---|
| IEOS | r[NR], de[NE], e0[NR], p[NE×NR], t[NE×NR] | 线性值（g/cc, Mbar·cm³/g, Mbar, K） |
| mgo | **f1 f2（独占一行）**, lr[NR], lt[NT], lo[NT×NR] | 全部 log10（ρ g/cc, T eV, κ cm²/g） |
| sgo | lr[NR], lt[NT], lo[NT×NR]（无 f1f2 行） | 全部 log10；Zeff 的 lt 是 log10(T/**keV**) |

详见 `knowledge/ieos_format.md`、`knowledge/mgo_sgo_format.md`。

## 5. 与其他部分的耦合

| 方向 | 关联部分 | 关系 |
|---|---|---|
| 下游 2D | `Mat2013_LoadIEOS`（`Mat2013_LoadIEOS.r:L18`） | 要求文件恰好 1 张 IEOS 表 |
| 下游 1D | `load_table`（`m150304.f95:L2880`） | 按 id 从多表文件挑表 |
| 工具 | `check_multi_file.py` | 复现 LoadMF C 语义的独立验证器 |

## 6. 常见错误

| 错误信息 | 原因 | 修复 |
|---|---|---|
| `head line size != 60` | CRLF（头变 61 字符）或字段缺前导空格 | `fix_multi_file.sh`；agent/pitfalls/crlf-line-endings.md |
| `bad number of tables: N` | 2D LoadIEOS 遇到多表文件 | 拆成单表文件（`Mat2013_LoadIEOS.r:L26-L28`） |
| `bad table type: ...` | LoadIEOS 遇到的子表不是 IEOS | 检查 type 字段 |
| Python float() 解析失败 | `-1.#INF000e+000` 或省略 e 的指数 | agent/pitfalls/windows-inf-field.md、missing-e-exponent.md |

## 7. 已知陷阱 / 与文档的差异

- `Mat2013.r:L31` 注释说 Zeff 温度是 eV——**陈旧**，实为 keV（见 pitfalls/zeff-kev-not-ev.md）。
- EOS-tools 代码注释把能量单位标为 "MJ/kg"，实际数值对应 Mbar·cm³/g（迁移指南 §6.1 ⚠）。

## 8. 延伸阅读

- `knowledge/ieos_format.md`、`knowledge/mgo_sgo_format.md`
- `MULTI-2D_材料库迁移指南.md §1`（格式规范全文）
- 验证器实现：`work/eos_opacity_tools/check_multi_file.py:L28-L108`

## 9. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
