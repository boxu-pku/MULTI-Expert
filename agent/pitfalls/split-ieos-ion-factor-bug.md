# split_ieos_table.py 离子表 T/P 系统性偏大 2.25 倍 bug（2026-09-06 已修）

**日期**：2026-09-06（Au 表补齐时经拆分自洽抽查发现）
**影响**：所有经 `work/eos_opacity_tools/split_ieos_table.py` 拆分的
`*_eos_i` 离子表（库内 47+ 种迁移材料）的 **T_i、P_i 系统性偏大 2.25 倍**
（=1.5²，γ=5/3 时）。

## 1. Bug 本质

`make_ion_ideal` 原写法 `T = de/((gamma-1)*cte)`，把 (γ−1)=2/3 当除数；
物理正确（也是 2D 原版 `Mat2013_GasIEOS.r` 的写法 `tr=(gamma-1)*mu*u*er/k`）是
**乘** (γ−1)：`T = (gamma-1)*de/cte = de/(1.5*cte)`。P_i = ρ·cte·T 同因子错。
电子表不受影响（减除项 1.5·cte·T_tot 用的是**总表**温度，自洽）。
修复版：`T = (gamma-1.0)*de[j]/cte`；原文件备份
`split_ieos_table.py.bak_ionfactor_20260906`。

## 2. 为什么 47 种材料 Hugoniot 验收没抓住

- 验收主判据 dUs（激波速度）由**总压**决定；高压缩下电子压主导，
  离子理想压份额小，2.25 倍误差对 Us 影响 ≲1–2%，藏在验收带内；
- "模拟 vs 表自洽"类验收两边用同一张（错的）离子表，自洽恒真——
  这是**自洽检查无法发现系统性 bug** 的典型案例，必须对拍独立
  基准（如理想气体解析式 T=E/(1.5·cte)，本次即由此抓出：
  Ti/Ttot 恒为 2.2500 而非 1）。

## 3. 影响面与待办

- **fort.10/11 的 TI 列**（离子温度剖面）：所有历史双温算例的 TI 偏高
  2.25 倍（TE 不受影响）；依赖 T_i 的物理（电子-离子弛豫速率、离子声速
  相关量）同步受扰；
- HOPG/scheme2、preheat、decay wave、H2O、反演平台等**已发表结论里凡
  引用 TI 数值的需复核**；只用 TE/密度/总压/Us 的结论基本安全；
- 47+ 种库内 `*_eos_i` 建议批量重拆（脚本一次性可完成），重拆后
  Hugoniot 不必重验（Us 影响 < 验收带），温度剖面类产物需重出。

## 5. 批量重拆已执行（2026-09-06 收官）

- 实际带毒 **65 张**（比预估多 18：库存老表 CH/D/DD/H/Diamond/Quartz/Water 等
  当年也经同一脚本拆分）；驱动 `work/resplit_ionfactor/resplit_driver.py`
  （指纹分类 buggy/correct_ideal/native + 四道验证，幂等）；
- 全部 65 张安装成功并终态复核 q=1.0000；备份 65 对 `.bak_ionfactor_20260906`；
- 详见 `work/resplit_ionfactor/REPORT.md`（含历史 TI 引用复核清单：
  preheat 系列优先复核，decay-wave/inversion/tvv 结论安全）。

## 4. 验证方法（复用）

拆分自洽抽查的正确姿势：给定 (ρ, de) 取总表 T_tot → E_i=1.5·cte·T_tot、
E_e=de−E_i → 分别查离子/电子表 → P_e+P_i≈P_tot（中高能区 ≤1%）且
**T_i(E_i)=T_tot 精确**（理想气体解析式，独立于拆分算法本身）。
低能端偏差大是电子能量截断（max(·,0)）的固有行为，与算法预期一致。
