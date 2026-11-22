# MULTI-Expert — 项目计划与状态跟踪

> 本文件是 MULTI-Expert skill 系统的指挥塔。
> 用户问"做到哪了 / 下一步是什么"时，先读本文件。

---

## 1. Dashboard

| 项 | 状态 |
|---|---|
| 治理骨架（agent/） | ✅ 完成（2026-08-11） |
| 陷阱库（12 条初始） | ✅ 完成（2026-08-11） |
| 知识层 skill（5） | ✅ 完成（2026-08-11） |
| 工具层 skill（2） | ✅ 完成（2026-08-11） |
| 操作层 skill（2） | ✅ 完成（2026-08-11） |
| ZCode 发现兼容 + CLAUDE.md/AGENTS.md | ✅ 完成（2026-08-11，.zcode/skills 软链） |
| 自检验收（§4 测试集） | 见 §4 逐项记录 |

## 2. Skill 状态表

| Skill | 层 | status | 完成日期 | 备注 |
|---|---|---|---|---|
| multi-architecture | 知识 | stable | 2026-08-11 | knowledge 5 篇；锚点全量机检通过 |
| multi-eos-format | 知识 | stable | 2026-08-11 | knowledge 4 篇；T3 任务测试通过 |
| multi-opacity | 知识 | stable | 2026-08-11 | knowledge 4 篇 |
| multi-1d-ife | 知识 | stable | 2026-08-11 | knowledge 5 篇；T2 佐证 |
| multi-materials-db | 知识 | stable | 2026-08-11 | knowledge 5 篇 |
| multi-table-tools | 工具 | stable | 2026-08-11 | knowledge 4 篇；T3 任务测试通过 |
| multi-visualize | 工具 | stable | 2026-08-11 | knowledge 4 篇；T2 任务测试通过 |
| multi-material-migration | 操作 | stable | 2026-08-11 | knowledge 4 + examples 1 + recipes 2；T1 演练通过（Gd 复查 ACCEPT 19/19） |
| multi-case-runner | 操作 | stable | 2026-08-11 | knowledge 4 + examples 2 + recipes 2；T2 任务测试通过 |

**状态判据**（ARCHITECTURE.md §7）：draft=骨架；beta=knowledge 齐+问答测试；stable=通过 §4 验收。
2026-08-11 §4 全部验收项通过，统一升 stable。

**状态判据**（ARCHITECTURE.md §7）：draft=骨架；beta=knowledge 齐+问答测试；stable=通过 §4 验收。

## 3. 决策记录

| 编号 | 日期 | 决策 | 来源 |
|---|---|---|---|
| D-001 | 2026-08-11 | 仿 FLASH-Expert 架构建 MULTI-Expert（9 skill：5 知识+2 工具+2 操作） | MULTI_Skill_规划文档.md §2/§4 |
| D-002 | 2026-08-11 | 工具实体不移动，skill 只写调用约定 | MULTI_Skill_规划文档.md §9 |
| D-003 | 2026-08-11 | 知识条目写"摘要+锚点"，一手来源是项目根 4 份治理文档 | MULTI_Skill_规划文档.md §9 |
| D-004 | 2026-08-11 | 2D 算例运行验证本轮不逐一实测，知识条目注明 | MULTI_Skill_规划文档.md §9 |
| D-005 | 2026-08-11 | 主位置 `.claude/skills/`；ZCode 兼容用 `.zcode/skills` 软链（如客户端需要） | MULTI_Skill_规划文档.md §7 |

## 4. 验收测试集（自检用）

### 4.1 触发测试（应命中对应 skill）

各 skill 的 description/triggers 已核对覆盖以下句子（description 均 <1024 字符、
前 250 字符前置核心触发词，符合 ZCode 呈现规则）：

- [x] "这个 IEOS 文件格式对不对" → multi-eos-format / multi-table-tools（双命中，符合预期）
- [x] "帮我加一种新材料 Ta" → multi-material-migration（triggers 含"加一种材料"）
- [x] "跑一下 TiCheck" → multi-case-runner（triggers 含"跑一下"/"TiCheck"）
- [x] "画密度热图" → multi-visualize（triggers 含"密度热图"/"画图"）
- [x] "MULTI 有哪些材料可用" → multi-materials-db（triggers 含"有哪些材料"）
- [x] "多群不透明度怎么用" → multi-opacity（when_to_use 逐字覆盖）

### 4.2 任务测试

- [x] T2：官方 1D 算例 2015CPC 跑通（normal termination，能量误差 9.3e-13，到达 texit=610 ps，
  153 条记录）+ plot_1d_validation.py 出图（density_heatmap.png / profiles_mid.png；
  剖面物理合理：烧蚀压 ~18 Mbar、冕区 Te~1200 eV、中间时刻 0.304 ns∈45-55% 区间）——2026-08-11
- [x] T3：Multi_BACK 原始文件验证——mat_Ti/Ti_eos 原件正确报出 `头行长度=61 != 60`（CRLF），
  fix_multi_file.sh 修复后 Ti_eos（IEOS 45×100）与 V_Z.dat（Zeff sgo 22×21，
  type ` 0.60000000E+01`）全部通过，退出码 0——2026-08-11（/tmp/skill_accept 副本上操作，未动源库）
- [x] T1：端到端迁移验收演练——以 Gd 复查形式新起子 agent（提示词按规范 §5 模板），
  独立检查 A1-A2/B1-B6/C1-C3/D1/E1-E4 共 19 项全部 PASS → **ACCEPT**
  （含与 hyades 源表绝对值对照：dP/P 中位 0.37%、最大 2.95% ≤3%）——2026-08-11

### 4.3 文档完备性

- [x] 锚点全量机检：9 个 skill + 12 条 pitfalls 的 **148 个 `文件:行号` 锚点全部真实存在
  且行号合法**（2026-08-11 脚本全量验证，非抽样）；每个 knowledge 文件 ≥3 锚点或有 § 文档锚点

## 5. 进行中工作流（skill 系统之外）

| 工作流 | 状态 | 位置 |
|---|---|---|
| MULTI1D 自适应反演平台 | **M0–M5 首战闭环完成（2026-09-01）**：G3 0/4、G4 1/4——波形修正未过实用门（信息量上限，非平台缺陷）；后续方向 A–D 待用户裁定 | `inversion/PLAN.md` §9.3 |
| TVV 复现工程（廖棱锐 PoF 2024 方法全量复现） | **T0–T5 全部完成（2026-09-06），A1–A5 验收全过**：σ₁ 94.6%、影响窗 [0,3.5] ns、可达设计=标量设计——与反演平台"可辨识信息≈一个标量"双链闭合；A–D 裁定证据输入就绪（REPORT §四，倾向 B） | `tvv_reproduction/PLAN.md`、`docs/REPORT.md` |

待用户裁定/复核：① inversion A–D 方向（含 TVV 新证据）；② TVV 三图人工判读；
④ cBN 偏硬
+8~10% 裁定；⑤ Hugoniot 人工闸门欠账（Silica/CH/SilicaFEOS/ParyleneHub）；
⑥ N/O 首步 NaN 待查；⑦ HOPG 新设计需求待提。

## 6. 变更日志

| 日期 | 改动 |
|---|---|
| 2026-08-11 | 初始创建；治理骨架（ARCHITECTURE/TEMPLATES/LESSONS/pitfalls 12 条）完成 |
| 2026-08-11 | 9 个 skill 全部实施完成（5 知识+2 工具+2 操作，共 41 个知识文件 + examples/recipes）；.zcode/skills 软链建立；CLAUDE.md/AGENTS.md 写入；T2/T3 任务测试通过、锚点全量机检通过；全部置 beta |
| 2026-08-11 | T1 演练通过（Gd 复查子 agent ACCEPT 19/19）；§4 验收测试集全部通过；9 个 skill 统一升 **stable** |
| 2026-08-14 | 经验沉淀：EOS 转换一律用 EOS-tools（用户指定唯一信任工具）——L-008 强化（LESSONS_LEARNED）、铁律 6（CLAUDE/AGENTS）、multi-table-tools（SKILL on_run + §3 + pitfalls）、multi-eos-format pitfalls、multi-material-migration（S1 + 新增 S4a 转换正确性加验：源表绝对值对照 + PdV 检查）；FEOS 自带转换器禁令全层引用 |
| 2026-09-01 | 新工作流登记：MULTI1D 自适应反演平台（inversion/，计划定稿 M0） |
| 2026-09-01 | 反演平台 M1+M2 落地：base 零差异复现、G1 sanity 3/4 入门+385 边缘（密集网格证优化器正确，偏移源于 DTW 口径+人工取整，见 inversion/PLAN.md §9.1）；工程教训：matplotlib mathtext 线程不安全 |
| 2026-09-01 | 反演平台 M3 完成：合成恢复 G2a 7/8、G2b 分层（A 过/C 边缘/B 简并）；口径定版 dtw 主 + χ² 接受带；b0/b1/b2 三角简并确认为物理上限（报告 inversion/docs/M3_synthetic_recovery.md） |
| 2026-09-01 | 反演平台 M4/M5 完成：G3 0/4、G4 1/4；结论=Us 对 Tr(t) 可辨识信息≈一个标量，四发无共性系统修正（docs/M4M5_real_campaign.md） |
| 2026-09-06 | 新工作流登记并当日收官：TVV 复现工程（廖棱锐 PoF 2024 时变 Volterra 方法，decay-wave 385 工况，~2080 次仿真）。A1–A5 全过；与反演平台双链闭合（σ₁ 94.6%、零响应边界 3.5 ns、可达设计=标量）；两项修订性发现（M3 B 构型简并=参数化口径非信息上限；核线性化域 δTr≤15-20 eV）。文献线：源文章全文+笔记存 work/reference_papers/liao_pof2024/ |
| 2026-09-06 | split_ieos 离子表 2.25 倍 bug 批量重拆收官：实际带毒 65 张（含库存老表，多于预估 47），65/65 安装+四道验证+终态复核 q=1.0000，备份 65 对；Hugoniot 不重验；历史 TI 列 ÷2.25 可线性修正，复核清单与报告 work/resplit_ionfactor/REPORT.md |
