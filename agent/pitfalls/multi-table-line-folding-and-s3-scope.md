# 自写 MULTI 表脚本漏行折叠：2D 总表单行写出不可加载（且 S3 漏验）

**日期**：2026-08-18（cBNFEOS 迁移）
**状态**：已修复（重排 2644 行 + 复验 ✓）；验收 agent 首轮 REJECT 暴露

## 症状

`r94/mat_cBNFEOS-1.0/cBNFEOS_eos`（2D 总表，feos2r94 两步修复路径的
自写脚本 `fix_r94_2d.py` 产物）：`check_multi_file.py` 报
`✗ ValueError: unexpected EOF`；r94 真实加载器 `Mat2013_LoadMF.c`
的 `get_line()`（MAXLINE=1024）对超长行直接失败——**2D 代码实际加载
也会报 bad file format**。

## 根因（两个叠加）

1. **脚本 bug**：`pack()` 用 `"".join(...)` 把全部 10572 个数据字段写进
   单行 158580 字符，漏了"每行 4 个 15 字符字段（60 字符/行）"的行折叠
   （1D 表由 EOS-tools 写出天然合规；自写脚本没有这个约束保障）。
2. **流程漏洞**：S3 格式验证只跑了 `r94/MULTI-IFE-2015/tables/` 下的
   1D 三表，**漏验 `r94/mat_*/` 目录的 2D 总表**——迁移者自查未发现，
   由独立验收 agent 抓出。

## 修复

- 数据无损（字段数与数值指纹逐位一致），仅按 4×15/行重排为 2644 行
  （与 hBNFEOS_eos 同构）；重跑 `check_multi_file.py` ✓ + spot-check
  P(3.4,1eV)=0.7424 MBar 精确；生成脚本的 `pack()` 同步修正。

## 教训

1. **S3 的 check_multi_file.py 必须覆盖本材料的全部产出表**，包括
   `r94/mat_<X>-1.0/` 的 2D 总表（与 1D tables/ 同等对待）；
2. 自写任何 MULTI 表写出脚本，行折叠（4×15）是硬约束——写完必跑
   checker，不能因"数据对了"跳过；
3. 独立子 agent 验收的价值实证：迁移者自查两次都没发现的布局缺陷
   被验收方用"checker + 真实加载器约束交叉验证"抓出。

## 相关

[[feos-converter-layout-energyunit]]（feos2r94 两步修复主 pitfall，
本条是其写出环节的补充）、[[crlf-line-endings]]（同属行级格式族）
