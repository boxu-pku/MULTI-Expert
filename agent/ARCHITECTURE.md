# MULTI Expert Agent — 架构规范

> 本文件是 MULTI-Expert multi-skill 架构的权威定义。所有 skill 必须遵循此处的结构和协议。
> 架构仿自 FLASH-Expert（`$MULTI_LIBS/flash/FLASH4.8/FLASH/FLASH4.8/agent/ARCHITECTURE.md`），
> 按 MULTI-2D.2026.3 的领域重写。修改本文件需要同步更新 `PROJECT_PLAN.md` 的决策记录。

---

## 0. 设计哲学

**核心原则**：主 Agent 不写业务逻辑，业务逻辑全部下沉到 skill。

| 角色 | 谁来扮演 | 职责 |
|---|---|---|
| **Orchestrator（主控）** | ZCode / Claude Code 本身 | 理解用户意图、选择 skill、组合结果、维护对话 |
| **Skill（专家）** | `.claude/skills/<name>/` | 单一领域的全部知识 + 行为协议 |
| **Knowledge Base（知识库）** | 每个 skill 内部的 `knowledge/` | 该领域结构化的 md，带源码/文档锚点 |
| **Tools（工具实体）** | `work/eos_opacity_tools/` + 外部 EOS-tools | 已存在的可运行脚本；**skill 只写调用约定，不移动实体** |

**反模式**（禁止）：
- ❌ 写一个"大 skill"装所有知识
- ❌ Skill 之间直接互相调用（必须经 Orchestrator）
- ❌ Knowledge md 跨 skill 共享（必须各自维护；共同事实引用项目根的 4 份治理文档并带锚点）
- ❌ Knowledge md 不带源码/文档锚点
- ❌ Skill 之间职责重叠
- ❌ 移动或复制 `work/eos_opacity_tools/` 的实体文件到 skill 内

---

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    用户对话层（ZCode / Claude Code 主上下文）        │
│                                                                     │
│  • 项目 CLAUDE.md / AGENTS.md 描述整个 skill 系统                    │
│  • 客户端看到所有 skill 的 description 字段                          │
│  • 根据用户意图自动选 1 个或多个 skill                               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ 通过 Skill 工具调用
        ┌──────────────────────┴──────────────────────┐
        ▼                                             ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│  知识层 skill (5)        │              │  工具层 skill (2)        │
│  按领域切                │              │  按功能切                │
│                          │              │                          │
│  multi-architecture      │              │  multi-table-tools       │
│  multi-eos-format        │              │  multi-visualize         │
│  multi-opacity           │              └──────────────────────────┘
│  multi-1d-ife            │
│  multi-materials-db      │              ┌──────────────────────────┐
└──────────────────────────┘              │  操作层 skill (2)        │
                                          │  端到端任务              │
                                          │                          │
                                          │  multi-material-migration│
                                          │  multi-case-runner       │
                                          └──────────────────────────┘
```

---

## 2. 9 个 Skill 完整清单

### 2.1 知识层 skill（5 个）

职责单一：回答该领域的"是什么/为什么/怎么用"问题。

| Skill | 领域 | 核心知识源 |
|---|---|---|
| `multi-architecture` | r94 模块体系、.s96_base 别名、编译链（x.2.*）、2D 核心模块、GUI/后处理 | `MULTI-2D_梳理文档.md`、`r94/*/MODINFO`、`boot-3.2/x.2.*` |
| `multi-eos-format` | IEOS/mgo/sgo 字节级格式、单位换算链、EleTab/GasIEOS 拆分、双温 ieose/ieosi | `r94/matter-3.1/Mat2013_LoadMF.r` 等、迁移指南 §1-2 |
| `multi-opacity` | 单群输运模型、freepath/opafun 机制、Thermos/CELIA/SNOP/opc 数据源、多群→单群聚合 | 迁移指南、映射表、`M20_Transport.r`、`Material.r` |
| `multi-1d-ife` | m150304.f95 输入卡、六表加载与 id 匹配、群结构自动推导、fort.10/11 输出 | `r94/MULTI-IFE-2015/m150304.f95`、tables/README |
| `multi-materials-db` | 77 种材料清单、每种材料的文件位置/网格/来源/注意事项/验收状态 | `MULTI-2D_材料库清单.md`（主）、映射表 |

### 2.2 工具层 skill（2 个）

跨领域复用的功能，**包装引用** `work/eos_opacity_tools/` 与 EOS-tools，不复制实体。

| Skill | 职责 | 包装的工具 |
|---|---|---|
| `multi-table-tools` | 表文件验证/修复/转换/拆分 | check_multi_file.py / fix_multi_file.sh / split_ieos_table.py / opc2sgo.py / batch_migrate.py / tread.f95 / EOS-tools CLI |
| `multi-visualize` | 1D 结果可视化（热图+剖面）；2D 后处理入口 | plot_1d_validation.py 调用约定；MULTI1Dvisual2.2 适用范围说明；R94/mpp22 入口 |

### 2.3 操作层 skill（2 个）

端到端任务，含 `examples/` 与 `recipes/`。

| Skill | 职责 | 核心资产 |
|---|---|---|
| `multi-material-migration` | 端到端新材料迁移（S1-S9），含子 agent 验收与人工确认闸门 | `材料迁移验证规范.md`、`batch_migrate.py`、验收提示词模板 |
| `multi-case-runner` | 运行 1D/2D 算例（RUN 脚本、ktag 语义、output 判读、CLEAR 清理） | `validation_cases/` 模板、`run_all_cases.sh` |

### 2.4 Skill 总数

```
5（知识层） + 2（工具层） + 2（操作层） = 9 个
```

---

## 3. Skill 内部统一结构

```
.claude/skills/<skill-name>/
├── SKILL.md                    # ★ 必需：frontmatter + 行为协议
├── knowledge/                  # 该领域结构化知识（每篇带锚点）
│   ├── overview.md             # 原理 + 设计动机
│   ├── internals.md            # 源码机制/调用链
│   ├── recipes.md              # 典型操作/配置
│   └── pitfalls.md             # 领域踩坑集（摘要+指向 agent/pitfalls/）
├── examples/                   # 仅操作层必需：真实可复用例子
└── recipes/                    # 仅操作层必需：端到端流程单
```

**强制规则**：
- 知识层 skill 的 `knowledge/` 至少 4 篇（overview/internals/recipes/pitfalls 可合并调整，但不得少于 4 篇）
- 每个 md 文件必须按 `TEMPLATES/knowledge-entry.md` 格式，**每个论断带锚点**（源码 `文件:行号` 或治理文档 `文档名§节`）
- `SKILL.md` 必须按 `TEMPLATES/skill-template.md` 格式
- 不得在 skill 根目录直接放 md（一律进 `knowledge/`）
- 知识条目写"摘要+锚点"，不重复誊写治理文档大段内容（避免不一致）

---

## 4. SKILL.md 的关键字段

详细模板见 `TEMPLATES/skill-template.md`。必须字段：

```yaml
---
name: multi-eos-format               # 全局唯一，与目录名一致
description: |                     # ★ 决定客户端是否调用本 skill
  <一句话职责> + 触发词列表（中英文）
triggers:                          # 显式触发关键词（≥5）
when_to_use: |                     # 何时应该用本 skill
when_not_to_use: |                 # 何时**不**该用（避免误触发）
layer: knowledge                   # knowledge / tool / operator
phase: 1                           # MULTI 系统全部 phase 1（一次性交付）
status: draft                      # draft / beta / stable / deprecated
last_updated: 2026-08-11
---
```

**关键点**：
- `description` 字段是客户端匹配用户意图的主要依据——写得越精准，越不会被错误触发；必须覆盖中英文触发词
- `when_not_to_use` 同等重要——避免 skill 之间职责重叠
- `status`：draft=骨架、beta=可测试、stable=验收通过、deprecated=废弃中

---

## 5. 调度协议

### 5.1 客户端如何选 skill

1. 读取所有 skill 的 `description` 字段（系统自动）
2. 根据用户问题语义匹配最相关的 skill
3. 命中 → 调用 `Skill` 工具传入 skill 名
4. 未命中 → 回退到主上下文

### 5.2 多 skill 协作（典型协作链）

| 场景 | 协作链 |
|---|---|
| "这个 IEOS 文件格式对不对" | `multi-eos-format`（格式知识）→ `multi-table-tools`（跑 check_multi_file.py） |
| "帮我加一种新材料 Ta" | `multi-material-migration`（端到端；内部引用 `multi-table-tools`/`multi-case-runner`/`multi-visualize` 的调用约定） |
| "跑一下 TiCheck 并出图" | `multi-case-runner`（跑）→ `multi-visualize`（出图） |
| "MULTI 有哪些材料可用" | `multi-materials-db` |
| "多群不透明度怎么用" | `multi-opacity`（机制）→ `multi-1d-ife`（1D 挂载） |
| "跑完报 head line size != 60" | `multi-eos-format`（原因）→ `multi-table-tools`（fix_multi_file.sh 修复） |

### 5.3 Skill 之间禁止直接调用

skill A 不能在 SKILL.md 里写"调用 skill B"。需要协作时由 Orchestrator 串起来。
skill 内可以写"该类问题通常还需 <另一领域> 的知识"作为给 Orchestrator 的提示。

---

## 6. 命名约定

| 类型 | 规则 | 示例 |
|---|---|---|
| Skill 目录名 | `multi-<领域>` 全小写连字符 | `multi-eos-format`, `multi-case-runner` |
| Knowledge 文件 | 全小写下划线 | `overview.md`, `ieos_format.md` |
| 陷阱文件 | 全小写连字符 | `agent/pitfalls/crlf-line-endings.md` |

---

## 7. Skill 生命周期

```
draft → beta → stable → (deprecated → archived)
```

| 状态 | 判据 | 行动 |
|---|---|---|
| `draft` | 仅有 SKILL.md 骨架 | 不被 Orchestrator 优先选择 |
| `beta` | knowledge 文件齐 + 通过基本问答测试 | 可被调用 |
| `stable` | 通过验收（触发测试+任务测试+锚点抽查） | 正式使用 |
| `deprecated` | 长期不用/被替代 | 标记废弃 |

**状态变更流程**：
1. 修改 SKILL.md 的 `status` 字段
2. 更新 `agent/PROJECT_PLAN.md` 状态表
3. 在 PROJECT_PLAN.md 变更日志加一行

---

## 8. 与 `agent/` 目录的关系

```
MULTI-2D.2026.3/
├── .claude/skills/          # ★ 9 个 skill（运行时被客户端加载）
├── agent/                   # ★ 治理目录（不被自动加载，按需 Read）
│   ├── ARCHITECTURE.md      # 本文件
│   ├── PROJECT_PLAN.md      # 项目指挥塔
│   ├── LESSONS_LEARNED.md   # 运行中积累的教训
│   ├── TEMPLATES/           # skill / knowledge / pitfall 模板
│   └── pitfalls/            # 陷阱库（现象/根因/修复/预防）
├── work/eos_opacity_tools/  # ★ 工具实体（skills 只引用，不移动）
└── 项目根 4 份治理文档       # ★ 知识的一手来源（迁移指南/验证规范/清单/映射表/梳理文档）
```

**知识层级**：治理文档是一手来源（single source of truth）；skill 的 knowledge 是"摘要 + 锚点"的导航层。二者冲突时以治理文档与源码为准，并修正 skill。

---

## 9. CLAUDE.md / AGENTS.md 的角色

项目根的 CLAUDE.md / AGENTS.md 是客户端入口提示，包含：
- MULTI skill 系统简介（9 个 skill 清单）
- 调用规则（优先匹配 skill；跨领域可多 skill；不知道就老实说）
- 触发示例（对应 §5.2 协作链）
- 项目状态入口（`agent/PROJECT_PLAN.md`）

---

## 10. 特别约束（MULTI 项目特定）

- **不要移动** `work/eos_opacity_tools/` 的实体文件——移动会破坏既有文档与脚本中的路径引用。
- `validation_cases/` 内容**永久保留**（人工验收依据），任何 skill 不得建议删除；`validation_cases/*/CLEAR` 禁止执行。
- 2D 算例（M2D_*）运行验证暂未纳入（周期长）；multi-case-runner 注明 2D 运行方法但标记"未逐一实测"。
- pitfalls 持续增补：每发现一个坑按模板追加到 `agent/pitfalls/`，并在 LESSONS_LEARNED.md 登记。

---

## 附录：架构决策溯源

| 决策 | 来源 | 状态 |
|---|---|---|
| 仿 FLASH-Expert multi-skill 架构 | MULTI_Skill_规划文档.md §1 | 采纳 |
| Skill 划分（5+2+2=9） | MULTI_Skill_规划文档.md §4 | 采纳 |
| 工具实体不移动，skill 只写调用约定 | MULTI_Skill_规划文档.md §9 | 强制 |
| 知识条目写"摘要+锚点"不誊写 | MULTI_Skill_规划文档.md §9 | 强制 |
| 2D 算例验证本轮不逐一实测 | MULTI_Skill_规划文档.md §9 | 采纳 |

---

> 版本：v1.0（2026-08-11，初始版本，仿 FLASH-Expert v1.0 改写）
