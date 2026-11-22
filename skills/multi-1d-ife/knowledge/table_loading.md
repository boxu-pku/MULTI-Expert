---
title: 1D 六表加载与群结构自动推导
skill: multi-1d-ife
category: internals
source_anchors:
  - r94/MULTI-IFE-2015/m150304.f95:L2858-L2904
  - r94/MULTI-IFE-2015/m150304.f95:L2944-L2965
  - r94/MULTI-IFE-2015/m150304.f95:L3040-L3071
  - r94/MULTI-IFE-2015/m150304.f95:L3345-L3388
  - MULTI-2D_材料库清单.md §三
doc_ref: "MULTI-2D_材料库迁移指南.md §2.2-2.3; MULTI-2D_材料库清单.md §三"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 六表
  - id匹配
  - 群结构
  - load_table_multi
  - frequencies
---

# 1D 六表加载与群结构自动推导

> **TL;DR**：每种材料挂 eeos/ieos/z/planck/ross/eps 六表，按"文件名+id"检索（id=0 通配）。群结构由 `frequencies` 自动从所有多群表的 f1/f2 边界并集推导。

## 1. 加载链路

```
read_material_data (m150304.f95:L2858)
  └─ 对每种材料调 load_table(mode,file,id,m) (L2880)，mode=1..6：
       1→load_table_eos(eeos)   L2892
       2→load_table_eos(ieos)   L2894
       3→load_table_group(z)    L2896   (Zeff)
       4→load_table_multi(planck) L2898
       5→load_table_multi(ross)   L2901
       6→load_table_multi(eps)    L2904
load_table 打开文件：L2889（'old', formatted； Fortran 顺序读，对 CRLF 天然容忍）
```

## 2. id 匹配规则

表头第 1 字段（15 字符）的整数值 = 表 id（`load_table_heading`，`L3090-L3097`；
type 第 2 字段 → itype，`L3099-L3111`）：

```
EOS 匹配：m150304.f95:L2944
   if((id==idin.or.idin==0).and.itype==1)then
群表匹配：m150304.f95:L2999
   if((id==idin.or.idin==0).and.itype>1)then
```

- `idin==0` 是**通配符**：取文件中第一张对应类型的表
- 一个文件可含多表（不同 id），1D 按需挑表；2D 的 LoadIEOS 则要求单表文件
- **Thermos 迁移表 id=0 → 输入卡用 `*_id=0`**（agent/pitfalls/thermos-id-zero.md）
- 迁移表 id 约定（材料库清单 §三）：电子表 `int(Z)×10⁶+304`、离子表 `+305`
  （分数 Z 用 round(Z*100)×10⁴；`batch_migrate.py:elem_ids` L164-L168）；
  不透明度/电离度表沿用源文件 id；opc 单群表 id=opc 表号

## 3. 各表加载细节

### EOS（eeos/ieos，`load_table_eos` L2928）

单位换算 `L2959-L2965`：de/e0/p ×1e12→cgs，t ÷11605→eV（与 r94 端约定一致，
详见 multi-eos-format/knowledge/ieos_format.md §3）。

### Zeff（z，`load_table_group` L2983 → `zbr` 插值 L2218）

- T 网格 **log10(keV)**：`zbr` 的 `tlog = log10(t)-3.`（`L2226-L2227`）——
  见 agent/pitfalls/zeff-kev-not-ev.md
- z_id=-1：不读表，用常数 zi

### 多群不透明度（planck/ross/eps，`load_table_multi` L3040）

- 循环读子表：EOF 结束（`L3050-L3052`）
- **f1==f2 退化子表误判结束**（`L3068-L3071`）——Thermos 文件可能含退化子表，
  迁移时必须先 `drop_degenerate_groups()`；见 agent/pitfalls/degenerate-opacity-group.md
- 单群（sgo）表：`load_table_group` 不读 f1f2 行时 `fmin=fmax=0.0`（`L3010-L3016`），
  `opa` 中 `fa==fb` 分支使任何频率命中（`L2285`）——sgo 表可作灰体材料跑
- eps_id=-1 → LTE（不用发射率表）

## 4. 群结构自动推导（`frequencies`，L3345）

```
do i=1,nmat; do j=1,3(三类多群表); do k=1,ng   L3354-L3373
   fa=tables(k)%fmin; fb=tables(k)%fmax
   if(fa/=fb)then → glist 插入有序边界表      L3367-L3370 （跳过单群表）
无多群表回退：ng=2, frei=[1, 1e6] eV          L3375-L3379
p%frei=frei(1:ng); p%ng=ng-1                  L3387-L3388
```

- **多材料群结构不同 → 边界并集**（群数膨胀，注意算力；迁移指南 §2.2）
- `glist`（L3392）：有序插入（L3405-L3416）
- 群数核对：output 表加载摘要中的 `ng` 应与源表群数一致（验证规范 §B3）

## 5. 常见错误

| 错误 | 原因 | 修复 |
|---|---|---|
| 群数比源表少 | 退化子表截断 | drop_degenerate_groups() |
| 表缺失/群数 0 | id 不匹配 | 读表头 id 或 *_id=0 |
| Zeff 被当 IEOS 读 | type 串 1D 不认 | 改头 ` 0.60000000E+01`（pitfalls/zeff-type-string-variants） |
| 群数异常多 | 多材料群边界并集 | 预期行为；算力敏感时统一群结构 |

## 6. 延伸阅读

- `knowledge/input_cards.md`（material 块写法）
- `multi-eos-format/knowledge/mgo_sgo_format.md §5`（1D 加载行为）

## 7. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
