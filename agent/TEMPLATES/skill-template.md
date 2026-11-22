# SKILL.md 统一模板（MULTI-Expert 版）

> 本文件是所有 `.claude/skills/<skill-name>/SKILL.md` 的强制模板。
> 新建 skill 时复制本文件的"模板正文"部分到 SKILL.md，按注释填充。
> **不要删 section**，没用的填 "N/A"。
> 仿自 FLASH-Expert `agent/TEMPLATES/skill-template.md` v1.0，MULTI 化改写。

---

## 使用流程

1. 创建目录 `.claude/skills/<skill-name>/`
2. 复制下方"模板正文"到 `SKILL.md`
3. 把所有 `<...>` 占位符替换为实际内容
4. 删除所有 `> [说明]` 注释行
5. 在 `agent/PROJECT_PLAN.md` 更新该 skill 的状态与变更日志

---

## 模板正文（复制下面 ``` 包围的内容到 SKILL.md）

```markdown
---
name: <skill-name>                          # 全局唯一，与目录名一致
description: |                              # ★ 客户端用此字段匹配用户意图
  <一句话总结：本 skill 是什么、做什么、何时用>
  触发词：<关键词列表，逗号分隔，中英文都要>
triggers:                                   # 显式触发关键词列表（至少 5 个）
  - <关键词1>
  - <关键词2>
  - <关键词3>
  - <关键词4>
  - <关键词5>
when_to_use: |                              # 何时应该调用本 skill
  <列出适用场景，要具体>
when_not_to_use: |                          # 何时**不**该调用（避免误触发）
  <列出易混淆但不属于本 skill 的场景>
layer: <knowledge | tool | operator>        # skill 层级
phase: 1
status: <draft | beta | stable | deprecated>
created: 2026-08-11
last_updated: 2026-08-11
owner: <用户名 or agent>
---

# <Skill 标题>

## 1. 角色与边界

### 1.1 我是做什么的
<2-3 句话说明本 skill 的核心职责>

### 1.2 我不做什么
<列出会推给其他 skill 的事>

| 用户问题类型 | 归属 skill |
|---|---|
| <示例问题1> | <其他 skill 名> |
| <示例问题2> | <其他 skill 名> |

## 2. 行为协议

### 2.1 接到查询时（on_query）

按以下步骤处理：

1. **理解意图**：明确用户问的是什么（格式/机制/参数/调试/操作）
2. **检索本 skill 的 knowledge/**：
   - 用 `grep` / `rg` 在 `knowledge/*.md` 找相关段落
   - 命中 → 基于内容回答，**必须引用锚点**（源码 `路径:行号` 或治理文档 `文档§节`）
   - 未命中 → 进入 2.3
3. **回答格式**：
   ```
   <直接答案>

   > **锚点**: r94/.../file.r:LXX（或 MULTI-2D_材料库迁移指南.md §X）
   > **相关工具**: <如适用，work/eos_opacity_tools/ 下的脚本>
   > **相关陷阱**: <如适用，agent/pitfalls/xxx.md>
   ```

### 2.2 接到执行任务时（on_run / on_analyze）

<如果本 skill 是 operator/tool 层，描述执行流程；
knowledge 层 skill 此节填 "N/A"。>

### 2.3 知识库未覆盖时（on_unknown）

**严格禁止**编造答案。按下面流程：

1. 老实告诉用户："本 skill 当前知识库未覆盖此问题"
2. 给出可能的解决路径：
   - 查项目根 4 份治理文档（迁移指南/验证规范/材料清单/映射表/梳理文档）
   - 直接读源码（r94/...）并带行号引用
   - 查陷阱库 `agent/pitfalls/`
3. **询问用户**："要不要我把这个新知识点按模板补进知识库/陷阱库？"
4. 用户同意 → 按 `knowledge-entry` / `pitfall` 模板追加

## 3. 知识维护规则

- 知识条目写"摘要+锚点"，不重复誊写治理文档大段内容
- 发现新坑 → 按 `agent/TEMPLATES/pitfall.md` 追加到 `agent/pitfalls/`，
  并在 `agent/LESSONS_LEARNED.md` 登记
- 治理文档与 skill 知识冲突时，以治理文档与源码为准，修正 skill
- 不要把推测写成事实（用"待验证"标注）

## 4. knowledge/ 子目录索引

| 文件 | 内容 | 当前状态 |
|---|---|---|
| `knowledge/overview.md` | <内容> | <draft/beta/stable> |
| `knowledge/...md` | <内容> | <draft/beta/stable> |

## 5. 示例问答（至少 3 个，作为基准）

### Q1: <典型问题1>
**A**: <答案摘要，含锚点>

### Q2: <典型问题2>
**A**: <答案摘要，含锚点>

### Q3: <典型问题3>
**A**: <答案摘要，含锚点>

## 6. 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | <name> |

## 7. 待办与已知问题

- [ ] <待补充的知识点>
```

---

## 关键设计点

### `description` 字段是关键

客户端主要靠这个字段决定是否调用本 skill。写法：
- **第一句**：本 skill 是什么 + 做什么
- **第二句**：典型用例
- **第三句**：触发关键词列表（**中英文都覆盖**，MULTI 用户以中文提问为主）

❌ 反例：`"MULTI 助手"`（太泛，会被各种问题误触发）
✅ 正例：`"MULTI IEOS/mgo/sgo 数据表格式专家。验证表文件、解释字节级格式与单位换算。触发词：IEOS, mgo, sgo, 状态方程表, 不透明度表, Zeff"`

### `when_not_to_use` 同样重要

避免 skill 之间职责重叠。例如：
- `multi-eos-format` 不该被"帮我迁移新材料"触发——推给 `multi-material-migration`
- `multi-materials-db` 不该被"这个文件格式对不对"触发——推给 `multi-eos-format`/`multi-table-tools`

---

## 模板版本

v1.0（2026-08-11，仿 FLASH-Expert v1.0 改写）
