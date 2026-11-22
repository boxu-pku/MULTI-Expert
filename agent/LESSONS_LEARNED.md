# MULTI-Expert — Lessons Learned

> 运行中积累的教训登记处。每条教训给出：编号、日期、来源、内容、应用方式。
> 与 `agent/pitfalls/` 的关系：pitfall 是"具体坑的完整档案"（现象/根因/修复/预防），
> 本文件是"方法论层面的教训"（一句话+指针）。新坑先入 pitfalls，再在此登记一行。

---

## 方法论教训（迁移工作中沉淀，2026-08-10 ~ 08-11）

| 编号 | 日期 | 教训 | 应用 | 关联 |
|---|---|---|---|---|
| L-001 | 2026-08-10 | **能量守恒查不出单位错误**——错单位的表自洽，程序照样守恒；验收必须含与源表的物理量绝对值对照 | 任何自定义转换链完成后与源表做绝对值抽查 | pitfalls/pressure-unit-confusion.md |
| L-002 | 2026-08-10 | **"能跑但结果错"类 bug 最危险**：布局读反（IEOS 能量主序）、单位错、群静默截断都无报错；验收要对照源数据绝对值与数量（群数） | 验收标准 B3（群数一致）、S4（拆分自洽）、单位对照 | pitfalls/ieos-layout-order.md、degenerate-opacity-group.md |
| L-003 | 2026-08-10 | **源码 > 注释**：Zeff 温度单位 r94 注释写 eV，1D 源码 zbr 的 `log10(t)-3` 证明是 keV；冲突时以源码为准 | 写知识条目时优先引源码锚点 | pitfalls/zeff-kev-not-ev.md |
| L-004 | 2026-08-10 | **选例先查表覆盖**：算例状态区间（ρ 含压缩裕量、T 含初温下限）必须在 EOS/不透明度表网格内，否则越界才暴露 | 迁移 S6 建算例前先 check 网格范围 | pitfalls/eos-density-range-limit.md、gas-vs-solid-case-density.md |
| L-005 | 2026-08-10 | **同名文件不同格式**：fort.10 有 ASCII（IFE-2015）与二进制（Windows Multi1D）两种；工具选用先确认来源程序 | 可视化一律用 plot_1d_validation.py | pitfalls/fort10-ascii-vs-binary.md |
| L-006 | 2026-08-11 | **机器验收 ≠ 最终验收**：子 agent ACCEPT 后必须经用户人工查看图/日志确认，才能在清单标"完全迁移 ✅" | 验证规范 §F 人工确认闸门；清单状态分两级 | 材料迁移验证规范.md §F |
| L-007 | 2026-08-11 | **双读取器兼容性**：同一数据文件要被 r94(C) 与 1D Fortran 两个读取器接受，type 串/行尾/特殊值都取交集（` 0.60000000E+01`、LF、`           -INF`） | 生成表文件时固定用双兼容写法 | pitfalls/zeff-type-string-variants.md、crlf-line-endings.md |
| L-008 | 2026-08-11（2026-08-13 强化） | **EOS 格式转换一律用 EOS-tools**（`$MULTI_LIBS/EOS_converter_xubo/EOS-tools`，用户指定**唯一信任工具**，CLI `cli/eos_convert.py`），不手写转换链、不用第三方转换器——2026-08-10 压强单位事故（÷1e11 vs ×1e-7）与 2026-08-13 能量轴 ×1000 事故（J/g vs J/kg 混淆）都是手工组装转换链引入的；FEOS 项目自带 `feos2multi.py`/`feos2r94.py` 有布局+能量单位（×100）双 bug，**禁用**（唯一例外：2D 单温总表无 EOS-tools 路径，用后必须按 pitfalls/feos-converter-layout-energyunit.md 两步修复）；FEOS→MULTI 正确路径是 `eos_convert.py --from feos --to multi`；若必须手工组装（batch_migrate 定制流程），转换后**必须与源表做物理量绝对值抽查对照 + PdV 热力学一致性检查**（migrated-eos-energy-scale-1000x.md"判定方法"），并查 `*.conversion-audit` 报告 | 用户明确指示（2026-08-11 指示"所有涉及状态方程转换的问题都要优先使用 EOS-tools"，2026-08-13 升级为唯一信任工具）；已写入 CLAUDE.md/AGENTS.md 铁律 6、multi-table-tools、multi-material-migration S1 | pitfalls/pressure-unit-confusion.md、migrated-eos-energy-scale-1000x.md、feos-converter-layout-energyunit.md；迁移指南 §6.1 |
| L-009 | 2026-08-14 | **EOS-tools 产物要过"运行关"才算完**：其自适应能量网格会产生完全相同行（零宽区间，导数 0/0），FEOS 离子分量在低 ρ（≲0.1 g/cc）低 T（≲0.35 eV）有非物理平台——两者都能过 check_multi_file 与全网格对拍，但 1D 算例 dt 坍缩卡死（var fail 不自愈）。判据：var fail 计数不是病，**是否自愈**才是；定位用双构型对拍（各换一张表跑 60 s）。修复：重复行去重；FEOS 离子表低 ρ 平台一律换**理想气体离子表**（split_ieos_table 约定，全库通行，不视为降级，代价已量化 ≈2.4% Hugoniot 偏差） | AlFEOS 迁移排障（bisect_A|B 模板）；写入 multi-material-migration 预防清单 | pitfalls/eos-tools-dup-rows-ideal-ion.md |
| L-010 | 2026-08-14 | **定宽表是"连续值流每行 4 值"契约**：块长非 4 倍数时按块断行会让 2D getc 读取器静默错位，但 1D 自由格式读取照跑——"算例能跑"不证明格式合规；check_multi_file.py（严格 getc 语义）才是判据。写表必须先 concatenate 全块再统一 4/行 | 写入 multi-table-tools/multi-eos-format 知识；铁律 4 有效性佐证 | pitfalls/multi-table-continuous-stream-format.md |
| L-011 | 2026-08-14 | **源表无冷曲线 ≠ 转换错误，但先查适用范围**：IONMIX4 金属表（AlFlash）T 下限 1 eV、无固体冷曲线，Hugoniot 自洽线 Us<Up、对理论线偏软 90%——S4 全网格对拍却证明转换保真（P50~2e-4）。冷曲线缺失只影响压缩/冲击场景，热等离子体烧蚀（表的本用途）完全正常（AlFlashCheck 能量误差 1.5e-10）。判据：最低 T 等温线声速 ≪ 体声速 → Hugoniot 不可用 | AlFlash 迁移；Hugoniot 路线先做表自洽线对理论线预检 | pitfalls/ionmix-al-no-cold-curve.md |
| L-012 | 2026-08-31 | **EOS-tools MULTI 产物 ≠ 直接入库**（对 L-008 的三条补充）：① `--from feos` 对**同位素混合物**（同 Z 不同 A，如 DT 的 D/T 均 Z=1）被 MaterialComposition 拒重复 atom_z——绕行走 FEOS 自产 SESAME 分表 `--from sesame --to multi`（.304/.305）；② EOS-tools 不做固定 de 列的 P(ρ) 单调化（DT 实例 28/96 低能列非单调，冷态查表错），入库前须 `np.maximum.accumulate` 后处理；③ 表头 ID 它写 1，须按房子惯例改 matnum×10⁴+304/305。校验三板斧：check_multi_file + 与源 .data.txt 在 T(rho,de) 交叉对拍绝对值（DT：P 中位 0.03%）+ 1D 算例跑通关（DTFEOSCheck 能量误差 3.7e-10，vs SESAME 表末态 te 中位 +2.5%） | DTFEOS 迁移检验；适用于一切 EOS-tools 转 MULTI 入库 | pitfalls/eos-tools-feos-isotope-duplicate-z.md、eos-tools-multi-monotonic-postfix.md |

---

## 维护规则

- 每发现一个新坑：按 `agent/TEMPLATES/pitfall.md` 追加到 `agent/pitfalls/`，
  并在此登记一行（若是方法论层面）。
- 每条教训标注**应用方式**（在哪条流程/哪份规范里落地），避免只记不用。

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建（7 条，从迁移工作沉淀回填） | claude |
| 2026-08-11 | 新增 L-008（EOS 转换一律优先 EOS-tools，用户指示） | user → claude 登记 |
| 2026-08-13 | 强化 L-008：EOS-tools 升级为用户指定唯一信任工具；FEOS 自带转换器双 bug 禁用（唯一例外+两步修复）；手写链两起单位事故（压强 ÷1e11、能量 ×1000）佐证；验收加 PdV 检查 | user → claude 登记 |
| 2026-08-14 | 新增 L-009（EOS-tools 产物运行关：重复行+FEOS 离子低ρ平台，理想离子约定）、L-010（连续值流 4/行契约）——AlFEOS 迁移排障沉淀 | claude |
| 2026-08-31 | 新增 L-012（EOS-tools MULTI 产物入库前三步：同位素重复 Z 绕行 sesame 路线、P(ρ) 单调后处理、表头 ID 改写）——DTFEOS 迁移检验沉淀 | claude |
