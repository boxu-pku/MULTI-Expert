# N/O（Thermos 氮/氧）Hugoniot 算例首步非确定性 NaN 段错误

日期：2026-08-20（批量二轮 Hugoniot 补验时发现）

## 现象

- `validation_cases/N/hugoniot_T*`、`O/hugoniot_T*` 全档段错误（SIGSEGV）。
- 输出（有缓冲）看似死在 print_material 的群结构/T 网格打印中途，实际崩溃点在
  第一步积分后的首个 `write_output_record`：右边界单元（辐射浴入口）Te 从
  0.03 eV 一步跳到 ~94 eV 后，`s%r` 密度全 NaN → `compute_ifar` 中 `imax`
  未初始化（rho 全 NaN 时循环不命中）→ 越界索引段错误。
- bounds-check 编译报 `compute_ifar line ~3790: Index '369598480' of array 'rho'`。

## 关键结论：**非源码回归**

- 用 2026-08-10 时代的旧二进制（Ti/TiCheck/multi）复现同样段错误；
- 历史 `N/NCheck/output`（8-13 备份）本身就有三次运行记录：前两次正常结束、
  **第三次即同款崩溃**——同一输入、同一二进制，非确定性复现。
- iquiet/tempmin/inegpre/dttevar/nc/thick 逐一排除均无效。

## 待办

- 专项排查首步 NaN 的物理/数值来源（疑似 N_eos_e 表在 Te≈94 eV、
  ρ0≈0.86 g/cc 冷态区插值或 e-e 耦合系数出 NaN）；
- `compute_ifar` 的 `imax` 未初始化是放大器（NaN 输入变段错误），
  修表问题前可先给 `imax` 兜底初始化，把段错误变成可读错误。

## 附带事故（2026-08-20，已恢复）

- 排查时误删 `N/NCheck/{output,fort.10,multi}`（原 output 已从 /tmp 备份恢复，
  旧二进制与原 fort.10 不可恢复；验证图 density_heatmap/profiles_mid.png 完好）；
- 误删模块目录 `r94/MULTI-IFE-2015/multidata.mod`（已用当前源码重编译再生，无害）。
