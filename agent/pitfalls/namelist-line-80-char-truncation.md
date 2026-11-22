# fort.12 namelist 行长 80 字符硬限（2026-09-10，P3 扫描段错误定位）

## 现象

m150304.f95 的 `namelistblock` 用 `character(len=80) :: inputline` 逐行
拷贝 fort.12 → block。**超过 80 字符的行被静默截断**：

- 截断只吃尾随注释时无害（如 tquiet 行 83 字符，'!' 在 30 列，先截断后
  剥注释，值完好——库内 data.in 多有此类长注释行，历史上一直"能用"）；
- **截断吃掉数据时致命**：P3 扫描的 ptab 行 88 字符，第 10 个值被截掉，
  `read_pulse` 的局部 ttab/ptab **未初始化**，垃圾值拷进 typesimpulse，
  在 integrate 第一步查表时段错误（core dumped，output 停在 banner 后）。

## 规则

1. **data.in 中任何携带数据值的行（尤其 ttab/ptab 数值串）必须 ≤80 字符**；
   长表用 namelist 续行（值表换行续写，次行缩进对齐即可）。
2. 生成 data.in 的脚本必须对**生成的行**断言 `len ≤ 80`（预存长注释行
   可豁免，但新写注释也应留界内）。
3. 段错误 + output 停在 print_pulse/integrate 附近 + 改过 namelist 表行
   → 首先查行长。

## 关联

`work/visar_precursor_program/FEEDBACK.md` §R4.3（首例）；原表 9 项的
ttab/ptab 行 ~66 字符，作者惯例即为此限。
