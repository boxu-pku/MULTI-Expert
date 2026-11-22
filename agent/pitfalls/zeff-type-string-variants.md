---
title: Zeff type 串两个读取器接受不同变体（用 " 0.60000000E+01" 双兼容）
category: 文件格式
severity: 警告（能跑但结果错）
first_seen: 2026-08-10
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - Zeff
  - type 串
  - EOS-tools
  - 双兼容
  - IEOS 误读
source_anchors:
  - r94/matter-3.1/Mat2013_LoadMF.r:L133-L134
  - MULTI-2D_材料库迁移指南.md §2.3
---

# Zeff type 串两个读取器接受不同变体（用 " 0.60000000E+01" 双兼容）

## 错误信息 / 现象

EOS-tools 生成的 Zeff 表（type 串 ` 6.00000000e+00`）：
- r94（2D）能正确识别为 Zeff 表 ✓
- **1D Fortran 把它误读为 IEOS 表** ✗（表加载错乱或 id/网格解释错误）

## 原因

Zeff 的 type 字段（表头第 2 个 15 字符字段）各读取器接受的变体不同：

| 读取器 | 接受的 Zeff type 串 |
|---|---|
| r94（Mat2013_LoadMF） | ` 0.60000000E+01`、` 6.00000000e+00` |
| 1D Fortran（load_table_heading） | ` 0.60000000E+01`、` 0.60000000e+01` |

交集只有 **` 0.60000000E+01`**。type 不匹配任何已知串时走 IEOS 兜底分支。

**源码机制**：
```
r94/matter-3.1/Mat2013_LoadMF.r:L133-L134
   type~" 4.00000000e+00"|type~" 6.00000000e+00"|
   type~" 0.60000000E+01"){      ← Zeff 分支
```

## 修复

给 1D 用的 Zeff 表，把头行第 2 字段改成 ` 0.60000000E+01`（双兼容）：

```bash
python3 - <<'EOF'
path = "<zeff表>"
raw = open(path, "rb").read().decode()
head = raw[:60]
new = head[:15] + " 0.60000000E+01" + head[30:]
open(path, "w").write(new + raw[60:])
EOF
```

`opc2sgo.py` 与 `batch_migrate.py` 写表时已用双兼容串。

## 锚点

- `r94/matter-3.1/Mat2013_LoadMF.r:L133-L134` — r94 的 Zeff type 比较行
- `MULTI-2D_材料库迁移指南.md §2.3` — 两个读取器差异的注意点 1
- `work/eos_opacity_tools/opc2sgo.py:L13-L14` — 双兼容 type 串的说明注释

## 预防

- 任何生成 Zeff 表的工具：type 串固定用 ` 0.60000000E+01`。
- EOS-tools 产物给 1D 用之前先检查/改头。
- 同理单群 Planck 用 ` 0.70000000E+01`、Rosseland 用 ` 0.40000000E+01`（双兼容）。

## 延伸

- 相关踩坑：`zeff-kev-not-ev.md`

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
