---
name: multi-material-migration
description: |
  MULTI 新材料端到端迁移专家。按《材料迁移验证规范》S1-S9 执行：源文件复制与修复
  （fix_multi_file）→ 总 IEOS 拆分（split_ieos_table）→ 格式验证（check_multi_file）→
  拆分自洽抽查 → 2D 材料函数（Material.r/Material_mig.r + 重编译）→ 建 1D 验收算例
  （validation_cases/<X>Check）→ 运行+可视化 → 子 agent 独立验收（A/B/C/D/E 条目）→
  登记清单 → 用户人工确认闸门。触发词：迁移, 新材料, 加材料, 加一种材料, migration,
  迁移流程, S1, S9, 验收, 子agent, 人工确认, 材料函数, Material.r, 验收算例,
  清单登记, batch_migrate, 全套迁移, 端到端
triggers:
  - 迁移
  - 新材料
  - 加材料
  - 加一种材料
  - migration
  - 迁移流程
  - 验收
  - 子agent
  - 人工确认
  - 材料函数
  - 验收算例
  - 清单登记
  - batch_migrate
  - 全套迁移
  - 端到端
  - 新增材料
  - migrate
when_to_use: |
  1. 用户要加新材料（"帮我加一种新材料 Ta"、"把 Gd 复查一遍"、"迁移 XXX"）
  2. 用户问迁移流程（"S1-S9 是什么"、"迁移一种材料要几步"）
  3. 用户问验收标准（"验收查什么"、"子 agent 提示词怎么写"）
  4. 用户问验收算例设计（"<X>Check 怎么建"）
  5. 迁移中途出错（某步骤失败的处理）
  6. 用户问清单登记/人工确认流程
when_not_to_use: |
  - 单个工具的使用细节（check/split/转换命令） → multi-table-tools
  - 表格式原理 → multi-eos-format
  - 不透明度源选用 → multi-opacity
  - 只跑已有算例 → multi-case-runner
  - 只出图 → multi-visualize
  - 查已有材料 → multi-materials-db
layer: operator
phase: 1
status: stable
created: 2026-08-11
last_updated: 2026-08-11
owner: claude
---

# multi-material-migration — 新材料端到端迁移专家

## 1. 角色与边界

### 1.1 我是做什么的

把"加一种新材料"的完整流水线固化：从源文件（Multi_BACK/hyades/Thermos/CELIA/SNOP）
到验收登记（清单标"完全迁移 ✅"）的 S1-S9 全流程，含**子 agent 独立验收**与
**用户人工确认闸门**。流程本体是《材料迁移验证规范.md》，本 skill 是它的执行层。

### 1.2 我不做什么

| 用户问题类型 | 归属 skill |
|---|---|
| 单工具命令细节 | `multi-table-tools` |
| 表格式原理 | `multi-eos-format` |
| 不透明度源选用 | `multi-opacity` |
| 只跑已有算例 | `multi-case-runner` |
| 只出图 | `multi-visualize` |

## 2. 行为协议

### 2.2 接到执行任务时（on_run）

**总原则**：严格按《材料迁移验证规范.md》S1-S9 执行，不跳步、不简化验收。

**开工前**：
0. **FEOS 源材料**：一律从 `.feos` 主表迁移；先读 FEOS 项目 skill
   （feos-converter/feos-visualizer），并用 showeos 生成 `.hug` 参考线拷至
   `validation_cases/<X>/` 供二轮对比（详见 knowledge/s_flow.md S1 规约）
1. 明确材料名、源文件位置、目标分类（全套/单群/仅EOS）——查
   `Multi_BACK_材料不透明度映射表.md` 与迁移指南 §4 资源分级
2. 查 EOS 表覆盖范围能否支撑验证算例（ρ 下限/上限、T 下限）——
   防 eos-density-range-limit / gas-vs-solid-case-density 类失败
3. 优先复用 `batch_migrate.py` + `migrate_manifest.py`（把材料加进清单条目），
   而不是手工逐步——手工步骤只在批量工具不覆盖时（新源类型）使用

**S1-S9 执行**（详见 `knowledge/s_flow.md`）：

| 步 | 动作 | 工具/锚点 |
|---|---|---|
| S1 | 源文件到目标位（2D 总表→`r94/mat_<X>-1.0/`；1D 表→`tables/`）；修 CRLF/-INF | fix_multi_file.sh / batch_migrate |
| S2 | 总 IEOS → 电子/离子表（1D 需要） | split_ieos_table.py；id=Z×10⁶+304/305 |
| S3 | 逐文件格式验证 | check_multi_file.py（全 ✓ 退出码 0） |
| S4 | 拆分自洽抽查（Pe+Pi vs P_tot，与官方 Be 表偏差同量级） | 自写脚本（指南 §7.4 法） |
| S5 | 2D 材料函数 + 重编译 | Material.r / Material_mig.r；`x.2.library` |
| S6 | 建 1D 验收算例 `validation_cases/<X>Check/` | 克隆 TiCheck / make_case() |
| S7 | 运行算例 | `cd <X>Check && ./RUN` |
| S7b | 可视化（density_heatmap.png + profiles_mid.png） | plot_1d_validation.py |
| S8 | **新子 agent 独立验收**（提示词模板见 §5 规范） | A1-A2/B1-B6/C1-C3/D1/E1-E4 |
| S9 | 登记《MULTI-2D_材料库清单.md》，状态"待人工确认"；**用户确认后标 ✅** | 规范 §F |

**验收提示词模板**：`材料迁移验证规范.md §5`（复制后替换 <X> 占位）。
**子 agent 全部 PASS 前不得进入 S9 登记；用户人工确认前不得标"完全迁移 ✅"。**

**失败处理**：任何一步 FAIL → 查 `knowledge/pitfalls.md` 与 `agent/pitfalls/`；
历史事故（单位/退化子表/算例密度）有完整记录，先对照再排查。

## 3. 知识维护规则

- 《材料迁移验证规范.md》是流程本体（single source of truth）；规范更新时同步本 skill
- 迁移中发现新坑 → `agent/pitfalls/` + `agent/LESSONS_LEARNED.md`

## 4. knowledge/ 子目录索引

| 文件 | 内容 | 当前状态 |
|---|---|---|
| `knowledge/s_flow.md` | S1-S9 逐步详解（含命令） | stable |
| `knowledge/acceptance.md` | 验收标准 A-E 全条目 + 子 agent 提示词模板 + 人工确认闸门 | stable |
| `knowledge/case_design.md` | 验收算例设计模板与物理设计原则 | stable |
| `knowledge/pitfalls.md` | 迁移类踩坑索引（含历史事故） | stable |

## 5. examples/ 与 recipes/

| 文件 | 内容 |
|---|---|
| `examples/ti_migration.md` | Ti 迁移实录（首个全流程范例，含实际命令与验收结论） |
| `recipes/full_migration.md` | 全套材料迁移流程单（hyades EOS + Thermos 不透明度） |
| `recipes/opc_single_group.md` | 为 EOS-only 材料配 opc 单群不透明度流程单 |

## 6. 示例问答（验收基准）

### Q1: 帮我加一种新材料 Ta
**A**: Ta 已迁移（mat_Ta-1.0，49×128 EOS + Thermos 21 群 + TaCheck ACCEPT）——
先查 `multi-materials-db` 确认。若真要复查/换新源：按 `recipes/full_migration.md`——
把 Ta 条目放进 migrate_manifest 的 BATCH_FULL 格式 → batch_migrate.py Ta →
检查验证输出 → 重跑 TaCheck → 子 agent 复验 → 更新清单 → 用户确认。

### Q2: 验收子 agent 的提示词怎么写？
**A**: 用《材料迁移验证规范.md §5》模板（`knowledge/acceptance.md §4` 有副本）——
替换材料名/文件清单/算例路径/迁移记录；子 agent 逐条输出 [PASS/FAIL] + ACCEPT/REJECT
结论；**必须新起子 agent**（独立验收，不带迁移者上下文）。

### Q3: 机器验收过了就能标"完全迁移 ✅"吗？
**A**: **不能**。规范 §F：机器 ACCEPT 后状态="机器验收通过，待人工确认"；
用户人工查看 `validation_cases/<X>Check/` 的 output 与两张 PNG 明确确认后，
才能在清单标"完全迁移 ✅"。

## 7. 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建（knowledge 4 + examples 1 + recipes 2） | claude |
| 2026-08-18 | 新增 FEOS 源迁移规约（.feos 主表 + showeos .hug 参考线） | claude |
