---
title: data.in 注释里写 & 导致 namelist 块被截断（End of file）
category: 输入卡
severity: 崩溃（Fortran runtime error: End of file）
first_seen: 2026-08-13
last_verified: 2026-08-13
verifier: claude
status: stable
tags:
  - data.in
  - namelist
  - 注释
  - locblock
  - namelistblock
source_anchors:
  - r94/MULTI-IFE-2015/m150304.f95:L2806-L2832
  - r94/MULTI-IFE-2015/m150304.f95:L2838-L2855
---

# data.in 注释里写 & 导致 namelist 块被截断

## 错误信息 / 现象

运行瞬间退出（<1 s），`cputime` 中：

```
At line 2665 of file multi.f95 (unit = 3, file = 'block')
Fortran runtime error: End of file
```

`output` 为空。2665 行即 `read(3,parameters)`——从临时文件 `block` 读
namelist 时遇到文件尾；打开 `block` 可见内容在某行注释处被齐根截断。

## 原因

MULTI-IFE 不用 Fortran 原生 namelist 直读 `fort.12`，而是先用
`namelistblock(name,number)`（L2806）把目标块逐行拷到临时文件 `block` 再读。
块提取的终止条件（L2819）：

```fortran
j = locblock(name,inputline)
if(j>0.and.i==number)exit
```

而 `locblock`（L2838）的判定是 **`scan(line,'&')`——只要一行里出现 `&`
字符就返回 j>0**（认为是某个 namelist 的头部）。注释剥离发生在这之后
（L2823 才 `scan(inputline,"!")` 去注释），所以**块内注释中出现的 `&`
（例如 `! ... 见 &pulse_shape`）会立即终止块提取**，后面的参数全部丢失。

## 修复

`data.in` 中**任何 namelist 块内部（`&name` 到下一个 `&` 之间）的注释不得
包含 `&` 字符**。要写就用文字代替，如 `(tabulated, see pulse_shape)`。
块外的整行注释（文件头说明）不受影响。

## 锚点

- `r94/MULTI-IFE-2015/m150304.f95:L2806-L2832` — namelistblock 块提取
- `r94/MULTI-IFE-2015/m150304.f95:L2838-L2855` — locblock 的 `&` 扫描

## 预防

- 手写/生成 data.in 后检查：`grep -n "&" data.in` 应只命中块头行
  （`&parameters`、`&layer`、`&material`、`&pulse_shape` 等）。
- 实例：`cases/preheat/CH-Al-SiO2_rad140-60/data.in`（2026-08-13 首次踩中）。

---

## 维护日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-13 | 初始创建 | claude |
