# MULTI-Expert — MULTI-2D / MULTI-IFE AI 专家 Agent 系统

> 多 harness 通用的多 skill 架构（Claude Code / ZCode / DSH / Codex CLI），
> 为 MULTI-2D（r94 体系）与 MULTI-IFE-2015（m150304.f95 一维程序）用户提供
> **物理问答、表工具、算例运行、结果可视化、材料迁移**的一站式 AI 辅助。
>
> 镜像来源：本仓库是 `MULTI-2D.2026.3` 工作项目（`$MULTI_ROOT`）中
> `.claude/skills/` + `agent/` 治理体系的发行镜像；真身在 `skills/` 目录。

---

## 1. 这是什么

MULTI-Expert 是一套**文件化的 AI 知识库系统**，由 10 个专门 skill 组成
（5 知识 + 3 工具 + 2 操作），覆盖 MULTI 2D/1D 程序的模块体系、数据表格式、
不透明度模型、材料库、算例运行与可视化。agent 根据问题自动匹配 skill，
给出**带字节级格式细节、带为什么、带诊断流程**的专业回答。

**它不是**：联网 Web 服务、RAG 数据库、需要训练的模型。

**它是**：一组精心组织的 markdown 知识文件 + 少量可直接运行的表工具脚本，
真身在 `skills/`，用 `./install.sh` 挂载到各 harness 的 skills 目录。

## 2. 包含什么

### 知识层（5 个）— 回答"MULTI 怎么工作"

| Skill | 覆盖 | 典型触发 |
|---|---|---|
| `multi-architecture` | r94 模块体系、编译链（boot-3.2/x.2.*）、2D 核心模块族、GUI | "模块怎么组织的"、"x.2.build 做了什么" |
| `multi-eos-format` | IEOS/mgo/sgo 字节级格式、单位换算、电子/离子表拆分 | "这个 IEOS 文件格式对不对"、"head line size != 60" |
| `multi-opacity` | 单群/多群输运模型、freepath/opafun、四个不透明度数据源 | "多群不透明度怎么用"、"opc 表是什么" |
| `multi-1d-ife` | m150304.f95 输入卡、六表加载、群结构推导、fort.10/11 输出 | "eeos_file 怎么填"、"群数怎么来的" |
| `multi-materials-db` | 79 种材料总账（分类/位置/网格/验收状态） | "MULTI 有哪些材料可用"、"Ta 有多少群" |

### 工具层（3 个）— 表与图

| Skill | 功能 |
|---|---|
| `multi-table-tools` | 表验证/修复/转换/拆分；`tools/` 内收编了 eos_opacity_tools 全套脚本（check/fix/split/opc2sgo/hugoniot 系列） |
| `multi-visualize` | 1D 标准出图 v1.0（9 张/例；实体在 MULTI1Dvisual utils/standard_visuals）+ 验收剖面；2D mpp22 入口 |
| `multi-prl-figure` | 出版级曲线图（IM_tool PRL 配方：15/12/10.5 字号、仅左下刻度、图例进空白区、英文标签） |

### 操作层（2 个）— 端到端流程

| Skill | 功能 |
|---|---|
| `multi-material-migration` | 新材料端到端迁移（S1-S9 + 子 agent 验收 + 人工确认闸门） |
| `multi-case-runner` | 跑 1D/2D 算例（RUN 脚本/ktag/output 判读/CLEAR 规则） |

### 配套知识资产

| 内容 | 位置 |
|---|---|
| 51 条陷阱库（持续增补） | `agent/pitfalls/` |
| 经验沉淀 | `agent/LESSONS_LEARNED.md` |
| 架构与项目状态 | `agent/ARCHITECTURE.md`、`agent/PROJECT_PLAN.md` |
| 事件复盘（双温 sloshing 等） | `agent/incidents/` |
| 流程提案（quiet-start 等） | `agent/proposals/` |
| 知识条目/陷阱/skill 模板 | `agent/TEMPLATES/` |
| 8 份一手治理文档（软件梳理、材料库清单/迁移指南、验证规范、BACK 映射表、Hugoniot 校验流程、Skill 规划、WeiKang 表评估） | `docs/` |

## 3. 安装

```bash
git clone git@github.com:boxu-pku/MULTI-Expert.git
cd MULTI-Expert
./install.sh                    # 用户级：~/.claude/skills, ~/.zcode/skills, ~/.agents/skills
./install.sh --scope project    # 或项目级：当前目录 .claude/skills 等
./install.sh --copy             # 复制模式（不支持符号链接的环境）
./install.sh --uninstall        # 按安装方式移除
```

安装 = 把 `skills/<name>` 挂载到各 harness 的 skills 目录（默认符号链接）。
更新方式：`git pull` 后符号链接自动生效（`--copy` 模式需重跑 `./install.sh`）。

## 4. 本机路径对照（变量约定）

skill 文本中的机器相关路径一律写成变量（约定见 `multi_env.sh`）：

| 变量 | 本机实际路径（源项目） | 含义 |
|---|---|---|
| `$MULTI_ROOT` | `/home/ubuntu/local/MULTI-2D.2026.3` | MULTI-2D 主项目（r94、work/、cases、validation_cases） |
| `$MULTI_LIBS` | `/home/ubuntu/local` | 外部工具安装前缀（EOS_converter_xubo/EOS-tools、newmulti/Multi_BACK、FEOS、IM_tool…） |
| `$MULTI_APP` | `/home/ubuntu/myapp` | 自研软件（MULTI1Dvisual GUI） |

在源项目里工作时 `source multi_env.sh` 即可还原全部路径。

注意：
- `skills/multi-table-tools/tools/` 里的脚本是从源项目
  `$MULTI_ROOT/work/eos_opacity_tools/` **收编的副本**（源项目铁律：原位置文件
  不得移动）；脚本内部的批处理默认路径是本机事实，跨机器使用时需自行调整。
- `agent/pitfalls/` 是踩坑实录豁免区，保留当时的原始路径与上下文。

## 5. 与源项目的关系

- 源项目（`$MULTI_ROOT`）是**唯一权威**：skill 在那里被日常使用和增补，
  本仓库定期镜像推送。
- 治理铁律（表工具不移动、validation_cases 永久保留、S1-S9 迁移流程、
  r94 改码前 Git 备份等）见 `CLAUDE.md`。
- MULTI 原始代码（`r94/`、m150304.f95）与材料表数据**不在本仓库**，
  仓库只含知识层与工具脚本。
