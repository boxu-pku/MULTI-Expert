---
title: f1==f2 退化子表致 1D 多群加载静默截断（Ne 实例）
category: 表加载
severity: 警告（能跑但结果错）
first_seen: 2026-08-10
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - 多群
  - 退化子表
  - f1==f2
  - Ne
  - load_table_multi
  - Thermos
source_anchors:
  - r94/MULTI-IFE-2015/m150304.f95:L3068-L3071
  - work/eos_opacity_tools/batch_migrate.py:L71-L95
  - 材料迁移验证规范.md §6-1
---

# f1==f2 退化子表致 1D 多群加载静默截断（Ne 实例）

## 错误信息 / 现象

无报错。1D 程序正常跑完，但表加载摘要中**群数比源表少**（Ne 实例：77/78 群，
第 50 子表之后的群被静默丢弃）。

## 原因

Thermos 源文件可能含 f1==f2 的退化子表（Ne：第 50 子表 f1==f2=1200 eV）。
1D 的 `load_table_multi` 遇 `fmax==fmin` 即认为"单群表，立即返回"——
把多群表中途截断，后续群**静默丢弃**。

- 根因分类：**源文件问题 + 源码行为（合理的单群判断被退化子表误触发）**

**源码机制**：
```
r94/MULTI-IFE-2015/m150304.f95:L3068-L3071
   ! for a single group table, return inmediatelly
   if(grouptab%fmax==grouptab%fmin)then
      ind=1
      return
```

## 修复

删除退化子表。`batch_migrate.py` 已内置自动处理：

```python
# work/eos_opacity_tools/batch_migrate.py:L71-L95  drop_degenerate_groups()
# 遍历 mgo 子表，f2-f1<=0 的整块跳过，并 log "删除 N 个退化子表"
```

手工迁移时：迁移后对 mgo 文件跑一遍检查群数是否与源一致
（1D output 的表加载摘要中 `ng` 与源表群数对比——验收标准 B3）。

## 锚点

- `r94/MULTI-IFE-2015/m150304.f95:L3068-L3071` — 结束误判位置
- `work/eos_opacity_tools/batch_migrate.py:L71-L95` — drop_degenerate_groups() 实现
- `材料迁移验证规范.md §6-1` — Ne 实例记录

## 预防

- Thermos 不透明度表迁移一律过 `drop_degenerate_groups()`（batch_migrate 已内置）。
- 验收时核对群数（output 摘要 ng vs 源表子表数）。

## 延伸

- 相关踩坑：`thermos-id-zero.md`

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
