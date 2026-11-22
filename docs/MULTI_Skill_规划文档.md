# MULTI Skill 系统 — 规划文档（交接实施版）

> **本文档用途**：交给一个新的对话，按此文档即可完整实现 MULTI skill 系统，无需了解此前对话上下文。
> 参考架构：`$MULTI_LIBS/flash/FLASH4.8/FLASH/FLASH4.8/`（FLASH-Expert multi-skill 系统）。
> 目标项目：`$MULTI_ROOT/`（MULTI-2D 辐射流体模拟程序 + 已扩充材料库）。
> 编写日期：2026-08-11。

---

## 0. 给实施者的一句话

在 `MULTI-2D.2026.3/` 下，仿照 FLASH-Expert 的 multi-skill 架构，建立一个 **MULTI-Expert** skill 系统：把 MULTI-2D/1D 程序的领域知识、我们已建成的材料迁移工具链、验证流水线，固化为可被 ZCode/Claude Code 自动触发的 skill 集合。所有需要的知识、工具、数据路径都已在本文件中给出。

---

## 1. 参考架构要点（来自 FLASH-Expert，必读）

先阅读这些文件，理解要模仿的结构：

| 文件 | 内容 |
|---|---|
| `FLASH4.8/agent/ARCHITECTURE.md` | multi-skill 架构权威定义（Orchestrator/skill/knowledge/tools 分层，反模式清单） |
| `FLASH4.8/agent/TEMPLATES/skill-template.md` | SKILL.md 强制模板（frontmatter 字段：name/description/triggers/when_to_use/when_not_to_use/layer/phase/status） |
| `FLASH4.8/agent/TEMPLATES/knowledge-entry.md`、`pitfall.md` | 知识条目与陷阱条目模板 |
| `FLASH4.8/.claude/skills/flash-eos/SKILL.md` | 知识层 skill 实例（看 description 写法和 triggers 覆盖度） |
| `FLASH4.8/.claude/skills/flash-case-runner/` | 操作层 skill 实例（含 knowledge/examples/recipes 子目录） |

**核心原则**（摘自 ARCHITECTURE.md，必须遵守）：
- 主 Agent 不写业务逻辑，业务逻辑全部下沉到 skill
- Skill 之间不直接互相调用（经 Orchestrator）
- 每个 knowledge md 必须带源码锚点（`文件:行号`）
- 单一职责：一个 skill 一个领域
- 分三层：知识层（knowledge）、工具层（tool）、操作层（operator，端到端任务）

**FLASH 的划分**（供对照）：知识层按物理单元切（flash-eos/flash-radtrans/...），工具层按功能切（flash-param-query/...），操作层端到端（flash-case-runner/flash-result-analyzer）。

---

## 2. 目标系统总览

在 `MULTI-2D.2026.3/` 下创建：

```
MULTI-2D.2026.3/
├── agent/                          # 治理目录(仿 FLASH agent/)
│   ├── ARCHITECTURE.md             # 本系统架构定义(可从 FLASH 版改写)
│   ├── PROJECT_PLAN.md             # 状态跟踪
│   ├── LESSONS_LEARNED.md          # 运行中积累的教训
│   ├── pitfalls/                   # 陷阱库(初始 12 条见 §6)
│   └── TEMPLATES/                  # 从 FLASH agent/TEMPLATES 复制改写
├── .claude/skills/                 # skill 集合(同时兼容 ZCode 发现机制, 见 §7)
│   ├── multi-architecture/         # 知识层
│   ├── multi-eos-format/           # 知识层
│   ├── multi-opacity/              # 知识层
│   ├── multi-1d-ife/               # 知识层
│   ├── multi-materials-db/         # 知识层(材料库总账)
│   ├── multi-table-tools/          # 工具层(验证/修复/转换)
│   ├── multi-visualize/            # 工具层
│   ├── multi-material-migration/   # 操作层(端到端迁移流水线)
│   └── multi-case-runner/          # 操作层(算例运行)
└── work/eos_opacity_tools/         # 已存在的工具实体(skills 引用它们, 不移动)
```

---

## 3. 背景知识（实施者必须掌握的既有事实）

### 3.1 软件构成

MULTI-2D.2026.3 包含两个程序：
- **2D 程序**：`r94/m2d-*` 模块族（r94 自定义语言→翻译为 C→gcc）。入口 `entry multi2d()` 于各算例 `User.r`；总控 `m2d-core-9.1/M20_Step.r`。GUI 入口 `./R94`。
- **1D 程序（MULTI-IFE-2015）**：`r94/MULTI-IFE-2015/m150304.f95`（自包含 Fortran，多群非 LTE 辐射流体）。算例 `cases/2015*`。
- 既有架构文档：`MULTI-2D_梳理文档.md`（项目根目录，内容详尽可直接引用）。

### 3.2 数据格式（已逐字节验证，可直接作为权威知识）

**IEOS（反演 EOS）表**：60 字符头（id|type|NR|NE，4×15 字符）+ 15 字符定宽数据（每行 4 值，跨节连续打包）：`r[NR](g/cc) de[NE](Mbar·cm³/g) e0[NR] p[NE×NR](Mbar, E行ρ列) t[NE×NR](K)`。读取换算：×1e12→cgs，÷11604.519→eV。**布局陷阱：p[j*NR+i] 能量主序**。

**mgo 多群不透明度**：头（id|`PLANCK M       `等|NR|NT）+ 次行 f1,f2（eV）+ log10(ρ)、log10(T/eV)、log10(κ cm²/g)。

**sgo 单群/Zeff 表**：无 f1f2 行；type 串：Planck=` 0.70000000E+01`，Rosseland=` 0.40000000E+01`，Zeff=` 0.60000000E+01`（注意 1D Fortran 与 r94 接受的变体不同——见 pitfalls/zeff-type-string.md）。
**Zeff 表 T 网格是 log10(T[keV])**（已由 1D 源码 `zbr` 的 `log10(t)-3` 证实；r94 注释写 eV 是陈旧文档）。

**hyades 库文件**（Multi_BACK）：EOS = [标题2行, NR, NT, ρ(g/cc), T(keV), P(dyne/cm², T行ρ列), E(erg/g)]；opc 不透明度 = [标题2行, NR, NT, ρ(g/cc), T(keV), Rosseland平均(NT×NR), Planck平均(NT×NR)]（**平均表非多群**；Planck 全零=仅 Rosseland）。

**1D 输出 fort.10（ASCII）**：头计数+变量名+索引+值 ×2 节，之后每条记录定长值序列；变量 R/PT/TE/PE/TI/ZI/XC/X/TR 等。**fortran e12.5 溢出场省略 e**（`-0.33689-232`）。

### 3.3 辐射模型要点

- 2D：单群（灰体）扩散，`control.transport.freepath` 回调（hydro,mid,rho,t)→λ[cm]，标准实现走各材料解析 `opafun`。**多群表在 2D 无消费者**。
- 1D：真多群非 LTE；材料挂 eeos/ieos/z/planck/ross/eps 六表（按 id 检索）；**群结构自动从表边界并集推导**；sgo 单群表可作灰体材料跑。

### 3.4 材料库现状（2026-08-11）

- 自带：DT/C/Al/Be/Au/Cu/Fe/W/Si/CH 等（`r94/mat_*`、`r94/MULTI-IFE-2015/tables/`）
- **已迁移 67 种**（全部机器验收通过，详见 `MULTI-2D_材料库清单.md`）：
  - 27+1 种全套（多群不透明度+Zeff+1D 验证算例）
  - 21 种单群 opc 表（含借用规则：SiO2族→opc_1022、LiD→Li表等，见 `Multi_BACK_材料不透明度映射表.md`）
  - 9 种仅 EOS（Lucite/PVA/Pt/Teflon/HE/PBX9502/Epoxy/BeO/C8H7Br）
  - 4 种无源（Ca/Nd/Ge/Se）
  - 已知数据局限：Diamond/Cliquid（EOS 表密度下限高，烧蚀算例越界）
- 2D 材料函数：`r94/m2d-core-9.1/Material.r`（自带+MaterialTi）+ `Material_mig.r`（56 个迁移函数）

### 3.5 工具链（已存在，skills 引用这些路径，**不要移动文件**）

目录 `$MULTI_ROOT/work/eos_opacity_tools/`：

| 工具 | 功能 |
|---|---|
| `check_multi_file.py` | MULTI 数据文件严格验证器（复现 Mat2013_LoadMF C 语义；IEOS/mgo/sgo 通吃） |
| `fix_multi_file.sh` | 修 CRLF 行尾 + Windows `-1.#INF000e+000` |
| `split_ieos_table.py` | 总 IEOS → 电子/离子表拆分（复刻 Mat2013_EleTab 算法） |
| `opc2sgo.py` | hyades opc 平均不透明度 → MULTI sgo 单群表 |
| `batch_migrate.py` + `migrate_manifest.py` | 清单驱动的批量迁移（hyades→EOS-tools 转换→拆分→Thermos/CELIA 表修复→验证→建算例） |
| `gen_material_functions.py` | 生成 2D 材料函数 Material_mig.r（含 Rosseland 拟合 opafun） |
| `plot_1d_validation.py` | 1D fort.10(ASCII) 解析 + 密度热图/中间时刻剖面图 |
| `tread.f95` | 1D Fortran 表头读取复刻（验证 1D 可读性） |
| `run_all_cases.sh` | 批量算例运行 |

外部依赖：**EOS-tools**（`$MULTI_LIBS/EOS_converter_xubo/EOS-tools`，格式转换与审计；CLI `cli/eos_convert.py` 等）。
可视化参考：`$MULTI_APP/MULTI1Dvisual2.2`（读**二进制** fort.10，Windows Multi1D 格式；与 IFE-2015 的 ASCII 不兼容——已入 pitfalls）。
源材料库：`$MULTI_LIBS/newmulti/Multi_BACK/matter++/`（Windows Multi1D 材料库）。
Hyades 转换参考代码：`$MULTI_LIBS/newmulti/Hyades相关/HYADES格式EOS转Multi代码/`（C++ 头文件，格式权威依据）。

### 3.6 治理文档（已存在，作为知识源引用）

- `MULTI-2D_材料库迁移指南.md` — 格式规范、消费路径、资源分级、操作手册、物理注意事项（10 条实测陷阱）
- `材料迁移验证规范.md` — S1-S9 迁移流程、13+4 条验收标准、子 agent 验收提示词模板、人工确认闸门、历史问题记录
- `MULTI-2D_材料库清单.md` — 材料总账（按全套/单群/仅EOS/无法迁移分类）+ 验收记录
- `Multi_BACK_材料不透明度映射表.md` — Multi_BACK 187+9 条材料记录的不透明度映射
- `validation_cases/` — 47 个验收算例目录（含 output 与两张 PNG，永久保留）

---

## 4. Skill 划分方案

### 4.1 知识层（5 个）

| skill | 职责 | 知识源（写入 knowledge/ 并带锚点） |
|---|---|---|
| **multi-architecture** | r94 模块体系、.s96_base 别名、编译链（x.2.*）、2D 核心模块（core/hydro2/radia/heat/ray/hib/ALE/malla）、GUI/后处理 | `MULTI-2D_梳理文档.md` + `r94/*/MODINFO` + `boot-3.2/x.2.*` |
| **multi-eos-format** | IEOS/mgo/sgo 字节级格式、单位换算链、EleTab/GasIEOS 拆分约定、双温 ieose/ieosi | `r94/matter-3.1/Mat2013_LoadMF.r`（锚点）、迁移指南 §1-2 |
| **multi-opacity** | 单群输运模型、freepath/opafun 机制、Thermos/CELIA/SNOP/opc 四个数据源的特征与选用、多群→单群聚合 | 迁移指南、映射表、`M20_Transport.r`、`Material.r` |
| **multi-1d-ife** | m150304.f95 输入卡（parameters/layer/material/pulse_wkb 块）、六表加载与 id 匹配、群结构自动推导、fort.10/11 输出结构 | `r94/MULTI-IFE-2015/m150304.f95` 锚点 + tables/README |
| **multi-materials-db** | 77 种材料清单、每种材料的文件位置/网格/来源/注意事项/验收状态 | `MULTI-2D_材料库清单.md`（主）、映射表 |

### 4.2 工具层（2 个）

| skill | 职责 | tools/ 内容（**包装引用**，不复制实体） |
|---|---|---|
| **multi-table-tools** | 表文件验证/修复/转换/拆分 | 对 `work/eos_opacity_tools/` 各脚本的调用约定（check/fix/split/opc2sgo/batch_migrate/tread）；EOS-tools CLI 调用约定 |
| **multi-visualize** | 1D 结果可视化（热图+剖面），2D 后处理入口（R94/mpp22） | `plot_1d_validation.py` 调用约定；MULTI1Dvisual2.2 的适用范围说明（二进制 fort.10） |

### 4.3 操作层（2 个）

| skill | 职责 | 核心资产 |
|---|---|---|
| **multi-material-migration** | 端到端新材料迁移：从源文件到验收登记全流程（S1-S9），含子 agent 验收与人工确认闸门 | `材料迁移验证规范.md`（流程本体）、`batch_migrate.py`、验收提示词模板 |
| **multi-case-runner** | 运行 1D/2D 算例（RUN 脚本、ktag 语义、output 判读、CLEAR 清理） | `validation_cases/` 模板、`run_all_cases.sh` |

---

## 5. 实施步骤（按序执行）

1. **建治理骨架**：`agent/` 目录；从 FLASH `agent/TEMPLATES/` 复制 3 个模板并做 MULTI 化改写；`ARCHITECTURE.md` 改写（skill 名单换成 §4 的 9 个）；`PROJECT_PLAN.md` 新建（9 个 skill 初始状态 draft）。
2. **逐 skill 实施**（建议顺序：multi-eos-format → multi-opacity → multi-1d-ife → multi-architecture → multi-materials-db → multi-table-tools → multi-visualize → multi-case-runner → multi-material-migration）：
   - 每个 skill：`SKILL.md`（按模板，description 要覆盖中英文触发词）+ `knowledge/`（overview/internals/pitfalls/recipes 至少 4 篇，**每篇带源码/文档锚点**）
   - 操作层另加 `examples/`（用 validation_cases 的真实例子）与 `recipes/`
3. **建陷阱库** `agent/pitfalls/`：初始 12 条见 §6，每条按 pitfall 模板写（现象/根因/修复/预防）。
4. **更新 PROJECT_PLAN.md**：每个 skill 完成后置 stable。
5. **自检验收**：用 §8 的测试用例集跑一遍触发测试与任务测试。

## 6. 初始陷阱库（12 条，直接可用）

| 文件 | 标题 | 核心内容 |
|---|---|---|
| crlf-line-endings.md | Windows CRLF 行尾致 r94 C 解析器报 head line size != 60 | Multi_BACK 文件需 dos2unix；1D Fortran 容忍但建议统一；fix_multi_file.sh |
| windows-inf-field.md | `-1.#INF000e+000` MSVC 输出 | Thermos 5 个文件；MULTI 标准 `-INF`→-40 |
| missing-e-exponent.md | Fortran 定宽溢出省略 e（`8.33534443-110`、`-0.33689-232`） | Epoxy EOS、2015CPC fort.10；正则插 e 修复 |
| pressure-unit-confusion.md | dyne/cm²→MPa 是 ×1e-7 非 ÷1e11（那是→Mbar） | 2026-08-10 事故；能量守恒查不出单位错，必须绝对值对照 |
| ieos-layout-order.md | IEOS p/t 是能量主序 p[j*NR+i] | numpy 默认 (NR,NE) reshape 会得到假象大偏差 |
| zeff-kev-not-ev.md | Zeff 表 T 网格是 log10(keV) 非 eV | r94 注释陈旧；1D zbr 源码 log10(t)-3 为证 |
| degenerate-opacity-group.md | f1==f2 退化子表致 1D 多群加载静默截断 | Ne 实例（77/78 群）；batch_migrate 已内置 drop_degenerate_groups() |
| eos-density-range-limit.md | EOS 表密度下限高致烧蚀算例越界 | Diamond/Cliquid 实例；选例时先查表覆盖范围 |
| gas-vs-solid-case-density.md | 验证算例密度选取 | Kr 固体密度算例辐射坍缩崩坏→气体密度；Air 初温需≥表 T 下限 |
| thermos-id-zero.md | Thermos 表头 id=0 | 1D 输入卡用 *_id=0 匹配任意 |
| fort10-ascii-vs-binary.md | IFE-2015 fort.10 是 ASCII，MULTI1Dvisual2.2 要二进制 | 用 plot_1d_validation.py；GUI 仅适用 Windows Multi1D |
| zeff-type-string-variants.md | Zeff type 串两读取器接受不同变体 | r94 认 ` 6.00000000e+00`，1D Fortran 不认；用 ` 0.60000000E+01` 双兼容 |

## 7. 安装/发现机制

- 主位置：`MULTI-2D.2026.3/.claude/skills/<name>/SKILL.md`（Claude Code 约定，与 FLASH 一致）
- ZCode 兼容：在 `MULTI-2D.2026.3/` 根部视客户端约定做软链或配置（可参考 zcode-guide:diagnosing-skills 的发现规则；若 ZCode 用 `.zcode/skills/` 则建软链）。实施时用 `Skill` 工具列表验证触发。
- 项目根的 `CLAUDE.md`/`AGENTS.md`：写入 skill 系统简介与各 skill 触发示例。

## 8. 验收标准

**触发测试**（对主 agent 说以下句子，应命中对应 skill）：
- "这个 IEOS 文件格式对不对" → multi-eos-format / multi-table-tools
- "帮我加一种新材料 Ta" → multi-material-migration
- "跑一下 TiCheck" → multi-case-runner
- "画密度热图" → multi-visualize
- "MULTI 有哪些材料可用" → multi-materials-db
- "多群不透明度怎么用" → multi-opacity

**任务测试**：
1. 用 multi-material-migration 完成一种新材料（建议 Gd 的同类复查或新增一种）端到端迁移并通过子 agent 验收
2. 用 multi-case-runner 跑通一个官方 1D 算例并用 multi-visualize 出图
3. 用 multi-table-tools 验证一个 Multi_BACK 原始文件（应能正确报出 CRLF 问题并修复）

**文档完备性**：每个 knowledge md 随机抽 3 个论断，锚点可查（文件:行号 真实存在）。

## 9. 注意事项

- **不要移动** `work/eos_opacity_tools/` 的实体文件——skills 只写调用约定；移动会破坏既有文档与脚本中的路径引用。
- `validation_cases/` 内容永久保留（人工验收依据），任何 skill 不得建议删除。
- 知识文件内容优先引用项目内已有 4 份治理文档与映射表，避免重复誊写导致不一致；知识条目写"摘要+锚点"。
- pitfalls 持续增补：后续运行中每发现一个坑按模板追加，并在 LESSONS_LEARNED.md 登记。
- 2D 算例（M2D_*）的运行验证暂未纳入本轮（周期长）；multi-case-runner 的知识条目里注明 2D 运行方法但标记"未逐一实测"。
