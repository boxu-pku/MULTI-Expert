# 算例内 multi.f95 是符号链接：就地打补丁会污染模块源码

**日期**：2026-08-14
**状态**：已确认（当日事故已修复并复盘）

## 事故

1D 算例的 `RUN` 脚本用 `cp -s $module/m150304.f95 multi.f95` 建**符号链接**。
为调试 tridia 奇异在算例目录给 `multi.f95` 打补丁时：
- `cp patched.f95 multi.f95`（dest 是指向模块源码的符号链接）
  → **GNU cp 默认跟随符号链接，直接覆写了 `r94/MULTI-IFE-2015/m150304.f95` 本体**；
- 后续 `open('multi.f95','w')` 写补丁同样穿透符号链接。

结果：模块源码被注入 9 处调试代码，其后所有算例（含其他材料）都在跑
"带调试打印的源码"。数值不受影响（纯 print），但属严重环境污染。

## 修复

对照发行包 `$MULTI_LIBS/MULTI-IFE-2015.tar.xz` diff，
**手术式**只回退调试 hunks（保留更早会话做的 4 处 CJK 注释乱码清理），
`gfortran -fsyntax-only` 通过。教训：**不能**简单用 tar.xz 全量覆盖恢复——
模块源码含有 tar 包之后的历史修正。

## 规程（今后算例内调试源码）

1. 先 `rm multi.f95`（删符号链接），再 `cp`（真拷贝），再改；
   或一律 `cp --remove-destination`。
2. 改完算例目录后，验收/正式运行前确认 `multi.f95` 是否为符号链接，
   若是则模块源码必未被污染（`grep tridia_site` 之类快速自检）。
3. 模块源码与发行 tar 的 diff 应只含已知历史 hunks；出现陌生 diff 即报警。

## 相关

[[water-cold-pe-and-opc-lowt-singular]]（当时正在调试的问题）
