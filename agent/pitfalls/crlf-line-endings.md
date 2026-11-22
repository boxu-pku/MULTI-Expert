---
title: Windows CRLF 行尾致 r94 C 解析器报 head line size != 60
category: 文件格式
severity: 阻塞（不能跑）
first_seen: 2026-08-10
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - CRLF
  - dos2unix
  - head line size
  - Multi_BACK
  - fix_multi_file
source_anchors:
  - r94/matter-3.1/Mat2013_LoadMF.r:L101-L102
  - work/eos_opacity_tools/fix_multi_file.sh:L27
  - MULTI-2D_材料库迁移指南.md §2.3
---

# Windows CRLF 行尾致 r94 C 解析器报 head line size != 60

## 错误信息 / 现象

### 形式 1：r94（2D）加载表
```
Format error: head line size != 60
```

### 形式 2：check_multi_file.py 验证时
```
✗ <文件>
    ValueError: 表1: 头行长度=61 != 60
```

## 原因

MULTI 表头必须**恰好 60 字符**。r94 的 C 解析器用 `getc` 逐字符读行，`\r` 会保留在行内，
Windows CRLF 文件的表头因此变成 61 字符，直接报格式错误。

- 根因分类：**源文件问题**（Multi_BACK 是 Windows 版 Multi1D 的材料库，大量文件带 CRLF）
- 1D Fortran 顺序格式读按记录换行，**对 CRLF 天然容忍**（已编译实测）；但建议统一转 LF。

**源码机制**：
```
触发位置：r94/matter-3.1/Mat2013_LoadMF.r:L101-L102
   if(#a!=60){ return([["Format error: head line size != 60"]]); }
```

## 修复

```bash
# 单文件（自动备份 .bak）
$MULTI/work/eos_opacity_tools/fix_multi_file.sh <文件>

# 整个目录
$MULTI/work/eos_opacity_tools/fix_multi_file.sh -d <目录>

# 或手工
sed -i 's/\r$//' <文件>
```

修复后必须验证：
```bash
python3 $MULTI/work/eos_opacity_tools/check_multi_file.py <文件>
```

## 锚点

- `r94/matter-3.1/Mat2013_LoadMF.r:L101-L102` — 60 字符表头检查的报错行
- `work/eos_opacity_tools/fix_multi_file.sh:L27` — `sed -i 's/\r$//'` 修复行
- `MULTI-2D_材料库迁移指南.md §2.3` — 两个读取器对 CRLF 容忍度差异的说明

## 预防

- 任何来自 Multi_BACK（`$MULTI_LIBS/newmulti/Multi_BACK/matter++/`）的文件，
  先跑 `fix_multi_file.sh` 再使用。
- `batch_migrate.py` 的 `dos2unix_file()` 已内置此处理（批量迁移无需手工干预）。

## 延伸

- 相关踩坑：`windows-inf-field.md`（同批 Windows 文件的另一问题）
- 对应 skill：`.claude/skills/multi-eos-format/knowledge/pitfalls.md`

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
