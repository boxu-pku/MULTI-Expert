# Example: Ti 迁移实录（首个全流程范例，2026-08-10）

> Ti 是首个完成全流程（S1-S9 + 人工确认 ✅）的迁移材料。
> 本实录作为端到端迁移的参照样板。数据源：Multi_BACK `mat_Ti/`（EOS）
> + SNOP_LTE 30 群不透明度（映射表 MID309）。

## 1. 源与目标

| 项 | 内容 |
|---|---|
| EOS 源 | `Multi_BACK/matter++/mat_Ti/Ti_eos`（45×100，CRLF 文件，B 类） |
| 不透明度源 | `mat_Ti/SNOP_LTE.Planck/.Ross/.ZEFF`（30 群，SNOP） |
| 2D 目标 | `r94/mat_Ti-1.0/Ti_eos` + `Material.r` 的 `MaterialTi()`（L418-L431） |
| 1D 目标 | `tables/Ti_eos_e`（id 22000304）、`tables/Ti_eos_i`（22000305）、`tables/Ti_LTE.*` |
| 验证算例 | `validation_cases/TiCheck/` |

## 2. 实际执行（S1-S7b 摘要）

```bash
M=$MULTI_ROOT
# S1 复制+修复
mkdir -p $M/r94/mat_Ti-1.0
cp .../mat_Ti/Ti_eos $M/r94/mat_Ti-1.0/
$M/work/eos_opacity_tools/fix_multi_file.sh $M/r94/mat_Ti-1.0/Ti_eos   # 去 CR

# S2 拆分（A=47.867, Z=22 → id 22000304/22000305）
cd $M/r94/MULTI-IFE-2015/tables
python3 $M/work/eos_opacity_tools/split_ieos_table.py \
    $M/r94/mat_Ti-1.0/Ti_eos 47.867 Ti_eos_e Ti_eos_i 22000304 22000305

# S1b 不透明度（SNOP 文件去 CR 后复制为 Ti_LTE.*）
# S3 验证
python3 $M/work/eos_opacity_tools/check_multi_file.py \
    $M/r94/mat_Ti-1.0/Ti_eos Ti_eos_e Ti_eos_i Ti_LTE.PLANCK Ti_LTE.ROSS Ti_LTE.ZEFF

# S5 Material.r 添加 MaterialTi（Material.r:L418-L431）+ freepath_Ti（L432-L437）
cd $M/r94/m2d-core-9.1 && x.2.library   # 重编译

# S6 建算例（手工克隆首建，后固化为 batch_migrate 的 make_case）
# S7 运行
cd $M/validation_cases/TiCheck && ./RUN
# S7b 可视化
python3 $M/work/eos_opacity_tools/plot_1d_validation.py $M/validation_cases/TiCheck
```

## 3. 验收结论（S8-S9）

- 子 agent 验收：**ACCEPT 16/16**（A/B/C 13 项 + E 可视化 4 项全 PASS，两轮子 agent）
- 用户人工确认：✅（2026-08-10）——清单中 Ti 是唯一"完全迁移 ✅"的参照态
- 过程中发现并固化的陷阱：Ti_Ross 头行 59 字符（用 SNOP_LTE.ROSS 替代）、
  Zeff type 串变体问题

## 4. 复用要点

- TiCheck 的 RUN/CLEAR 是所有后续 XCheck 算例的克隆母本（batch_migrate make_case L256-L257）
- Ti 的 id 约定（Z×10⁶+304/305）成为全部迁移材料的约定
- Ti 的 data.in 结构成为 CASE_TEMPLATE（`batch_migrate.py:L172-L243`）
