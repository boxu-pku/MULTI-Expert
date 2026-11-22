# EOS-tools ZEFF 表头 type 字段与 1D 加载器不兼容

**日期**：2026-08-14（PSFlash 迁移时发现）
**状态**：已确认，库内产物已修复

## 现象

EOS-tools 转换（ionmix→multi）产出的 `_zeff.multi` 能通过
`check_multi_file.py`（sgo[type=6.00000000e+00] ✓），但 1D 算例一加载就死：

```
ERROR in subroutine load_table_skip
      premature eof
```

## 原因

1D 加载器（`m150304.f95` `load_table_heading`）按**字符串精确匹配**识别表类型，
电离度 sgo 只认两个 magic 字符串：

```fortran
if(a2==' 0.60000000E+01')itype=2
if(a2==' 0.60000000e+01')itype=2
```

EOS-tools 写的是数值等价的 `' 6.00000000e+00'`（同样是 6.0，但字符串不同）
→ 不命中 → itype 保持 1（IEOS）→ numrec 按 IEOS 公式算（远大于实际）
→ 跳过记录数超过文件行数 → premature eof。

2D 加载器（r94 `Mat2013_LoadMF`）容忍两种写法（`check_multi_file.py` 的
SGO_TYPES 两种都收），所以格式验证发现不了。**给 1D 用的表必须过 1D 型
兼容性检查**（铁律 4 的"再验 type 串兼容性"即指此）。

## 修复

把表头第 2 字段（第 16–30 字符）改为 magic 字符串：

```python
txt = txt[:15] + ' 0.60000000E+01' + txt[30:]
```

## 排查要点

- `load_table_skip premature eof` 几乎总是"表头 type 字符串不识别 → numrec 算错"
- 1D 认的 magic 字符串全集（m150304.f95 `load_table_heading`）：
  - sgo 电离度：`' 0.60000000E+01'`/`e+01`
  - sgo Planck：`'PLANCK 1       '` 或 `' 0.70000000E+01'`
  - sgo Rosseland：`'ROSSELAND 1    '` 或 `' 0.40000000E+01'`
  - sgo EPS：`'EPS 1          '`
  - mgo：`'PLANCK M       '` / `'ROSSELAND M    '` / `'EPS M          '`
  - 其余一律按 IEOS（type=1）处理
- mgo 群边界行必须**单独占一行**（numrec 公式里 +1 记录；4e15.8 读取，
  不足 4 值补 0）——EOS-tools 原生输出即如此，但**重写 id 后重打包文件时
  必须保持 60 字符头行 + 30 字符边界行 + 4 值/行结构**（2026-08-14 PSFlash
  改写 id 时一度连成单行，超 1024 字符上限）。
