# MULTI-Expert — CLAUDE.md

> 与 `AGENTS.md` 同内容，供以 AGENTS.md 为入口的 agent 客户端使用。
> 本仓库是 `$MULTI_ROOT`（源项目 `MULTI-2D.2026.3`）skill 系统的发行镜像；
> 真身在 `skills/`，`.claude/skills`、`.zcode/skills`、`.agents/skills`
> 是挂载链接。路径变量约定见 `multi_env.sh`。

## MULTI Skill 系统

本项目包含 **10 个专门 skill**（5 知识 + 3 工具 + 2 操作）。
架构定义见 `agent/ARCHITECTURE.md`，项目状态见 `agent/PROJECT_PLAN.md`。

| Skill | 层 | 职责 | 典型触发 |
|---|---|---|---|
| `multi-architecture` | 知识 | r94 模块体系、编译链、2D 核心模块、GUI | "模块怎么组织的"、"x.2.build 做了什么" |
| `multi-eos-format` | 知识 | IEOS/mgo/sgo 字节级格式、单位换算、电子/离子拆分 | "这个 IEOS 文件格式对不对"、"head line size != 60" |
| `multi-opacity` | 知识 | 单群/多群输运模型、freepath/opafun、四个不透明度数据源 | "多群不透明度怎么用"、"opc 表是什么" |
| `multi-1d-ife` | 知识 | m150304.f95 输入卡、六表加载、群结构推导、fort.10 输出 | "eeos_file 怎么填"、"群数怎么来的" |
| `multi-materials-db` | 知识 | 79 种材料总账（分类/位置/网格/验收状态） | "MULTI 有哪些材料可用"、"Ta 有多少群" |
| `multi-table-tools` | 工具 | 表验证/修复/转换/拆分（`skills/multi-table-tools/tools/` 收编副本；源项目实体在 `work/eos_opacity_tools/`） | "验证这个文件"、"修 CRLF"、"拆分 EOS 表" |
| `multi-visualize` | 工具 | 1D 标准出图 v1.0（9 张；实体在 MULTI1Dvisual utils/standard_visuals，旧入口薄壳；frozen）+验收剖面；2D mpp22 入口 | "画密度热图"、"看 TiCheck 结果"、"出标准图" |
| `multi-prl-figure` | 工具 | 出版级曲线图（IM_tool PRL 配方 15/12/10.5、仅左下刻度、图例进空白区、英文标签、激光线性折线+总能角标） | "出出版图"、"汇总图美化"、"PRL 风格" |
| `multi-material-migration` | 操作 | 新材料端到端迁移（S1-S9 + 子 agent 验收 + 人工确认） | "帮我加一种新材料 Ta" |
| `multi-case-runner` | 操作 | 跑 1D/2D 算例（RUN/ktag/output 判读） | "跑一下 TiCheck"、"跑 2015CPC" |

### 调用规则

- 用户提问时，**优先**匹配最相关的 skill 而不是从主上下文回答
- 跨领域问题可以串多个 skill（由主 agent 编排；skill 之间不直接互调）
- 不知道答案时**老实说**，建议把新知识点补进对应 skill 的 knowledge/ 或 `agent/pitfalls/`

### 典型协作链

- "这个 IEOS 文件格式对不对" → `multi-eos-format` → `multi-table-tools`（跑验证）
- "帮我加一种新材料" → `multi-material-migration`（内部引用 tools/runner/visualize 的约定）
- "跑一下 TiCheck 并出图" → `multi-case-runner` → `multi-visualize`
- "跑完报 head line size != 60" → `multi-eos-format`（原因）→ `multi-table-tools`（修复）

## 一手治理文档（知识源，优先级最高，位于 `docs/`）

| 文档 | 内容 |
|---|---|
| `docs/MULTI-2D_梳理文档.md` | 软件总体架构（模块/编译链/算例/运行） |
| `docs/MULTI-2D_材料库迁移指南.md` | 数据格式规范、消费路径、资源分级、操作手册、物理注意事项 |
| `docs/材料迁移验证规范.md` | 迁移 S1-S9 流程、验收标准、子 agent 提示词、人工确认闸门 |
| `docs/MULTI-2D_材料库清单.md` | 材料总账与验收记录 |
| `docs/Multi_BACK_材料不透明度映射表.md` | Multi_BACK 187+9 条材料的不透明度映射 |
| `docs/Hugoniot校验流程.md` | Hugoniot 二轮核验工具链与门禁 |
| `agent/pitfalls/` | 陷阱库（51 条，持续增补） |

## 铁律（源项目运营规则，镜像仓同样遵守）

1. **不要移动** 源项目 `work/eos_opacity_tools/` 的实体文件（路径被脚本与文档写死；
   本仓 `skills/multi-table-tools/tools/` 只是收编副本）
2. 源项目 `validation_cases/` 全部产物**永久保留**，禁止执行其中的 CLEAR、禁止删除
3. 新材料迁移必须走 S1-S9 + 子 agent 独立验收 + 用户人工确认，
   机器 ACCEPT 不等于"完全迁移 ✅"
4. 任何表文件修改后必跑 `check_multi_file.py`；给 1D 用的再验 type 串兼容性
5. 运行算例前确认环境：`export MULTI=$MULTI_ROOT` + PATH 含 `r94/boot-3.2`
6. **EOS 格式转换一律用 EOS-tools**（`$MULTI_LIBS/EOS_converter_xubo/EOS-tools`，
   用户指定唯一信任工具）；FEOS 项目自带 `feos2multi.py`/`feos2r94.py` 有
   布局+能量单位双 bug，禁用（唯一例外：2D 单温总表无 EOS-tools 路径，
   用 feos2r94 后必须按 `agent/pitfalls/feos-converter-layout-energyunit.md`
   做两步修复）
7. **【死命令 2026-09-10】动 MULTI 原始代码（源项目 `r94/` 下任何源码，含
   m150304.f95）之前必须先 Git 备份**：`r94/` 已是 git 仓库，基线 commit
   `dbd117a`；改码前先 `git -C r94 status` 确认干净（脏则先提交），修改
   按逻辑分块 commit 并写明改动点，验收不过 `git checkout` 回滚。
   tables/ 大体积数据不入库（.gitignore），磁盘照常保留

## 项目状态

当前进度见 `agent/PROJECT_PLAN.md`。用户问"做到哪了"或"下一步是什么"时，先读它。
