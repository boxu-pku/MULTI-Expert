#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hugoniot_report.py — 汇总某材料多强度算例的 Hugoniot 点, 叠加全部理论线出图

理论数据: IM-tool 标准库 (/home/ubuntu/local/IM_tool/IM_tool/im_app/
          standard_library/materials/), Al 共 4 条 —— 全部画出:
          SESAME 3717 / SESAME 3720 / Celliers 2005 (PRL, 带误差带) / FEOS
可视化风格: 复用 IM-tool 的 PRL 风格 (im_app/core/plot_style.py):
          serif 字体、刻度朝内+次刻度、无框图例、理论线实线、
          模拟点为黑填充 marker + 黑边 (IM-tool scatter 约定)

产物 (写入 <材料>/hugoniot_summary/):
  <mat>_hugoniot_points.csv — 全部采信点(含溯源与质量信息)
  <mat>_hugoniot_UsUp.png   — Us-Up 图 (PRL 风格, 全部理论线)
  <mat>_hugoniot_Prho.png   — P-rho 图 (同上)

用法: python3 hugoniot_report.py <材料名> <rho0> <算例目录1> [算例目录2 ...]
"""
import os
import sys
import numpy as np

sys.path.insert(0, "/home/ubuntu/local/MULTI-2D.2026.3/work/eos_opacity_tools")
from extract_hugoniot import extract_series

# IM-tool PRL 风格(只依赖 matplotlib, 直接复用, 不复制)
sys.path.insert(0, "/home/ubuntu/local/IM_tool/IM_tool/im_app/core")
import plot_style as ps

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IM_MAT = "/home/ubuntu/local/IM_tool/IM_tool/im_app/standard_library/materials"

# IM-tool 理论线标签(按 IM-tool mat.name (source) 约定)
THEORY_TXT = {
    "Al": [("Al_3717_sesame.txt", "Al (SESAME 3717)"),
           ("Al_3720_sesame.txt", "Al (SESAME 3720)"),
           ("Al_Celliers2005.txt", "Al (Celliers 2005)"),
           ("Al_FEOS.hug", "Al (FEOS)")],
    # AlFEOS（FEOS mat 3717 迁移版）：同源基准 Al_FEOS.hug 即真值线
    "AlFEOS": [("Al_3717_sesame.txt", "Al (SESAME 3717)"),
               ("Al_3720_sesame.txt", "Al (SESAME 3720)"),
               ("Al_Celliers2005.txt", "Al (Celliers 2005)"),
               ("Al_FEOS.hug", "Al (FEOS)")],
    # 石英族(α-quartz rho0=2.65): 适用 Silica / SiO2wk12 (rho0 2.648~2.65)
    "Quartz": [("Quartz_7360_sesame.txt", "SiO2 (SESAME 7360)"),
               ("Quartz_7385_sesame.txt", "SiO2 (SESAME 7385)"),
               ("Quartz_Hamel2012.txt", "SiO2 (Hamel 2012)"),
               ("Quartz_FEOS.hug", "SiO2 (FEOS)")],
    "SiO2wk12": [("Quartz_7360_sesame.txt", "SiO2 (SESAME 7360)"),
                 ("Quartz_7385_sesame.txt", "SiO2 (SESAME 7385)"),
                 ("Quartz_Hamel2012.txt", "SiO2 (Hamel 2012)"),
                 ("Quartz_FEOS.hug", "SiO2 (FEOS)")],
    # Silica(2.204 熔石英玻璃): 理论线为 α-quartz 2.65, 仅高压段可参照;
    # 另有表自洽线 (SELF_HUG) 作为一致性判据
    "Silica": [("Quartz_7360_sesame.txt", "SiO2 2.65 (SESAME 7360)"),
               ("Quartz_7385_sesame.txt", "SiO2 2.65 (SESAME 7385)"),
               ("Quartz_Hamel2012.txt", "SiO2 2.65 (Hamel 2012)"),
               ("Quartz_FEOS.hug", "SiO2 2.65 (FEOS)")],
    # FEOS 模型表: 四条 α-quartz 线 + 自身 FEOS 基准(对 QuartzFEOS 是直接同源基准)
    "QuartzFEOS": [("Quartz_7360_sesame.txt", "SiO2 (SESAME 7360)"),
                   ("Quartz_7385_sesame.txt", "SiO2 (SESAME 7385)"),
                   ("Quartz_Hamel2012.txt", "SiO2 (Hamel 2012)"),
                   ("Quartz_FEOS.hug", "SiO2 (FEOS)")],
    "SilicaFEOS": [("Quartz_7360_sesame.txt", "SiO2 2.65 (SESAME 7360)"),
                   ("Quartz_7385_sesame.txt", "SiO2 2.65 (SESAME 7385)"),
                   ("Quartz_Hamel2012.txt", "SiO2 2.65 (Hamel 2012)"),
                   ("Quartz_FEOS.hug", "SiO2 2.65 (FEOS)")],
    # CH 固体聚苯乙烯 SESAME 7592 (IM-tool reference_curves, 2026-08-14 加入;
    # compression/rho/P 三列, Us/Up 由 RH 质量+动量关系换算, P0≈0)
    "CH": [("PS_LiuXing_A3_PBE.txt", "PS (LiuXing A.3, PBE)"),
           ("PS_LiuXing_A3_LDA.txt", "PS (LiuXing A.3, LDA)"),
           ("../reference_curves/CH_sesame7592.csv", "CH (SESAME 7592)")],
    "PSFlash": [("../reference_curves/CH_sesame7592.csv", "CH (SESAME 7592)")],
    # PS (hyades 源聚苯乙烯): LiuXing A.3 即聚苯乙烯 C8H8, 为本材料的独立 DFT 线;
    # SESAME 7592 (CH) 作跨源参考 (2026-08-25 补注册 — 此前 PS 无理论线, 图只有自洽线)
    "PS": [("PS_LiuXing_A3_PBE.txt", "PS (LiuXing A.3, PBE)"),
           ("PS_LiuXing_A3_LDA.txt", "PS (LiuXing A.3, LDA)"),
           ("../reference_curves/CH_sesame7592.csv", "CH (SESAME 7592)")],
    "hBNFEOS": [("__HUG__:/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/hBNFEOS/hBN.hug",
                 "hBN (FEOS showeos .hug, source RH)"),
                ("__HUG__:/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/hBNFEOS/zhanghuan_usup.csv",
                 "hBN Us-Up (ZhangHuan, rho0=2.04)"),
                ("__HUG__:/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/hBNFEOS/zhanghuan_usup_208.csv",
                 "hBN Us-Up (ZhangHuan, rho0=2.08)"),
                ("__HUG__:/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/hBNFEOS/zhanghuan_prho.csv",
                 "hBN P-rho (ZhangHuan, rho0=2.04)")],
    "CHHub": [("PS_LiuXing_A3_PBE.txt", "PS (LiuXing A.3, PBE)"),
              ("../reference_curves/CH_sesame7592.csv", "CH (SESAME 7592)")],
    # AlHub: 同 Al 四条理论线 (SESAME 3717/3720, Celliers 2005, FEOS)
    "AlHub": [("Al_3717_sesame.txt", "Al (SESAME 3717)"),
              ("Al_3720_sesame.txt", "Al (SESAME 3720)"),
              ("Al_Celliers2005.txt", "Al (Celliers 2005)"),
              ("Al_FEOS.hug", "Al (FEOS)")],
    # LiFHub: Quartz 理论线作阻抗参考 (LiF ρ0=2.64 与 α-石英 2.65 阻抗相近,
    # 惯用阻抗匹配对; 两线 Hugoniot 本应接近)
    "LiFHub": [("LiF_Hawreliak2023.txt", "LiF (Hawreliak 2023 PRB)"),
               ("Quartz_7360_sesame.txt", "Quartz 2.65 (SESAME 7360, impedance ref)"),
               ("Quartz_7385_sesame.txt", "Quartz 2.65 (SESAME 7385, impedance ref)"),
               ("Quartz_Hamel2012.txt", "Quartz 2.65 (Hamel 2012, impedance ref)"),
               ("Quartz_FEOS.hug", "Quartz 2.65 (FEOS, impedance ref)")],
    # hBNHub (邢展彬 FP hBN, rho0=2.04; 2026-08-18 身份翻案: 原误名 cBNHub):
    # 同源参考 ZhangHuan Us-Up 两档 + P-压缩比参考线(hBN-P-CR.xlsx 转换,
    # P-rho 面为准; Us-Up 换算用 P0=0 近似) + 用户 FEOS hBN 源线(跨模型参考)
    "hBNHub": [("/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/hBNHub/zhanghuan_prho_204.csv",
                "hBN 2.04 (ZhangHuan P-CR)"),
               ("/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/hBNHub/zhanghuan_usup_204.csv",
                "hBN 2.04 (ZhangHuan, same source)"),
               ("/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/hBNHub/zhanghuan_usup_208.csv",
                "hBN 2.08 (ZhangHuan, same source)"),
               ("__HUG__:/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/hBNFEOS/hBN.hug",
                "hBN 2.04 (FEOS .hug source)")],
    # FEOS 重算 cBN (本表 rho0=3.40 与 kang 3.40 变体同初态;
    # cBN.hug 为 FEOS 源自解主 Hugoniot 线——源级真值参考, 列首位)
    "cBNFEOS": [("__HUG__:/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/cBNFEOS/cBN.hug",
                 "cBN 3.40 (FEOS .hug source)"),
                ("cBN_rho3.40.txt", "cBN 3.40 (kang2025)"),
                ("cBN_rho3.42.txt", "cBN 3.42 (kang2025)"),
                ("cBN_rho3.44.txt", "cBN 3.44 (kang2025)"),
                ("__HUG__:/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/cBNFEOS/omega_paper_prho.csv",
                 "BN (Omega paper EOS, rho0=3.40 assumed)")],
    # 邢展彬新 FP cBN (2026-08-30, rho0=3.45): kang2025 三变体 + ZhangShuai P-CR
    # (PRB 99.165103 同目录; kang↔zhangshuai 互差 ~2%, 表自洽线 vs 两者 +5~17%,
    # 见 材料表信息.md —— 用户裁定中)
    "cBNHub": [("/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/cBNHub/zhangshuai_prho_345.csv",
                "cBN 3.45 (ZhangShuai P-CR, PRB 99.165103)"),
               ("cBN_rho3.44.txt", "cBN 3.44 (kang2025)"),
               ("cBN_rho3.40.txt", "cBN 3.40 (kang2025)")],
    # 碳表代理 cBN (2026-09-10, Diamond 表仅改初密度 3.45): 判据线同 cBNHub
    # (ZhangShuai 同初密度居首) + Romero 2007 为代理源 Diamond 的本征 DFT 线
    # (非 BN 线, 显示代理与源本身的偏差)
    "cBNCpx": [("/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/cBNHub/zhangshuai_prho_345.csv",
                "cBN 3.45 (ZhangShuai P-CR, PRB 99.165103)"),
               ("cBN_rho3.44.txt", "cBN 3.44 (kang2025)"),
               ("cBN_rho3.40.txt", "cBN 3.40 (kang2025)"),
               ("Diamond_Romero2007_solid.txt", "Diamond 3.473 (Romero2007, proxy-source native)")],
    # 碳表代理 hBN (2026-09-10, Cliquid 液态碳表仅改初密度 2.04): 判据线同 hBNHub
    "hBNCpx": [("/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/hBNHub/zhanghuan_prho_204.csv",
                "hBN 2.04 (ZhangHuan P-CR)"),
               ("/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/hBNHub/zhanghuan_usup_204.csv",
                "hBN 2.04 (ZhangHuan, same source)"),
               ("__HUG__:/home/ubuntu/local/MULTI-2D.2026.3/validation_cases/hBNFEOS/hBN.hug",
                "hBN 2.04 (FEOS .hug source)")],
    # AlFlash (FLASH IONMIX4 al-imx-003): 铝四条理论线作参照(非独立验证)
    "AlFlash": [("Al_3717_sesame.txt", "Al (SESAME 3717)"),
                ("Al_3720_sesame.txt", "Al (SESAME 3720)"),
                ("Al_Celliers2005.txt", "Al (Celliers 2005)"),
                ("Al_FEOS.hug", "Al (FEOS)")],
    # Diamond: Romero & Mattsson 2007 DFT-MD Hugoniot (PRB 76,214113),
    # Table III(固)/IV(液) Te0 行, ρ0=3.473(GGA 平衡密度), 2026-08-24 提取入库
    # (RH 能量闭合校验中位残差 0.009 eV/atom; 对拍结论库表偏硬 ~1-3%)
    "Diamond": [("Diamond_Romero2007_solid.txt", "Diamond (Romero 2007, DFT solid)"),
                ("Diamond_Romero2007_liquid.txt", "Diamond (Romero 2007, DFT liquid)")],
    # C_wk (刘兴碳 D 构型支, 锚同 Diamond 3.51): Romero DFT 线适用作独立参考
    "C_wk": [("Diamond_Romero2007_solid.txt", "Diamond (Romero 2007, DFT solid)"),
             ("Diamond_Romero2007_liquid.txt", "Diamond (Romero 2007, DFT liquid)")],
}
# 表自洽 Hugoniot 线(无独立理论线时的替代判据; 灰虚线绘制, 非独立验证)
TABLES_DIR = "/home/ubuntu/local/MULTI-2D.2026.3/r94/MULTI-IFE-2015"
SELF_HUG = {
    "Silica": dict(eeos=f"{TABLES_DIR}/tables/Silica_eos_e",
                   ieos=f"{TABLES_DIR}/tables/Silica_eos_i",
                   rho0=2.204, T0_eV=0.1, eta_max=4.5),
    "SilicaFEOS": dict(eeos=f"{TABLES_DIR}/tables/SilicaFEOS_eos_e",
                       ieos=f"{TABLES_DIR}/tables/SilicaFEOS_eos_i",
                       rho0=2.204, T0_eV=0.1, eta_max=4.5),
    "hBNFEOS": dict(eeos=f"{TABLES_DIR}/tables/hBNFEOS_eos_e",
                    ieos=f"{TABLES_DIR}/tables/hBNFEOS_eos_i",
                    rho0=2.04, T0_eV=0.0259, eta_max=4.5),
    "hBNHub": dict(eeos=f"{TABLES_DIR}/tables/hBNHub_eos_e",
                   ieos=f"{TABLES_DIR}/tables/hBNHub_eos_i",
                   rho0=2.04, T0_eV=0.0259, eta_max=6.0),
    "cBNHub": dict(eeos=f"{TABLES_DIR}/tables/cBNHub_eos_e",
                   ieos=f"{TABLES_DIR}/tables/cBNHub_eos_i",
                   rho0=3.45, T0_eV=0.02585257, eta_max=4.5),
    # 碳表代理 BN (2026-09-10): 副本表在 BN 初密度下的自洽线 —— 检验程序忠实性;
    # 物理合理性判据是 vs THEORY_TXT 的 BN 文献线
    "cBNCpx": dict(eeos=f"{TABLES_DIR}/tables/cBNCpx_eos_e",
                   ieos=f"{TABLES_DIR}/tables/cBNCpx_eos_i",
                   rho0=3.45, T0_eV=0.02585257, eta_max=4.5),
    "hBNCpx": dict(eeos=f"{TABLES_DIR}/tables/hBNCpx_eos_e",
                   ieos=f"{TABLES_DIR}/tables/hBNCpx_eos_i",
                   rho0=2.04, T0_eV=0.0259, eta_max=4.5),
    "cBNFEOS": dict(eeos=f"{TABLES_DIR}/tables/cBNFEOS_eos_e",
                    ieos=f"{TABLES_DIR}/tables/cBNFEOS_eos_i",
                    rho0=3.4, T0_eV=0.02585257, eta_max=4.5),
    "CHHub": dict(eeos=f"{TABLES_DIR}/tables/CHHub_eos_e",
                  ieos=f"{TABLES_DIR}/tables/CHHub_eos_i",
                  rho0=1.044, T0_eV=0.1, eta_max=4.5),
    "CH": dict(eeos=f"{TABLES_DIR}/tables/CH_eos_e",
               ieos=f"{TABLES_DIR}/tables/CH_eos_i",
               rho0=1.044, T0_eV=0.1, eta_max=4.5),
    # PSFlash 不入 SELF_HUG: 表自洽线对该材料无判据意义(方法失效, 点贴等温线,
    # 见 pitfalls/ionmix-preheat-shell-merger.md); 诊断用 COLD_LOCUS 等温线
    # AlFlash 表 T 下限 1 eV: 初态钳到 de=0 (T0 取 1 eV)
    "AlFlash": dict(eeos=f"{TABLES_DIR}/tables/AlFlash_eos_e",
                    ieos=f"{TABLES_DIR}/tables/AlFlash_eos_i",
                    rho0=2.7, T0_eV=1.0, eta_max=4.5),

# ==== 2026-08-20 批量二轮补验: 新材料表自洽线 (配置同 MAT_TABLES) ====
    "Ag": dict(eeos=f"{TABLES_DIR}/tables/Ag_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Ag_eos_i",
                    rho0=10.5, T0_eV=0.1, eta_max=4.5),
    "Air": dict(eeos=f"{TABLES_DIR}/tables/Air_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Air_eos_i",
                    rho0=0.00129, T0_eV=0.1, eta_max=4.5),
    "Al2O3": dict(eeos=f"{TABLES_DIR}/tables/Al2O3_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Al2O3_eos_i",
                    rho0=3.97, T0_eV=0.1, eta_max=4.5),
    "Ar": dict(eeos=f"{TABLES_DIR}/tables/Ar_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Ar_eos_i",
                    rho0=1.4, T0_eV=0.1, eta_max=4.5),
    "Be_wk": dict(eeos=f"{TABLES_DIR}/tables/Be_wk_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Be_wk_eos_i",
                    rho0=1.845, T0_eV=0.1, eta_max=4.5),
    "CD2": dict(eeos=f"{TABLES_DIR}/tables/CD2_eos_e",
                    ieos=f"{TABLES_DIR}/tables/CD2_eos_i",
                    rho0=1.0475, T0_eV=0.1, eta_max=4.5),
    "CH2_wk": dict(eeos=f"{TABLES_DIR}/tables/CH2_wk_eos_e",
                    ieos=f"{TABLES_DIR}/tables/CH2_wk_eos_i",
                    rho0=0.954, T0_eV=0.1, eta_max=4.5),
    "Cliquid": dict(eeos=f"{TABLES_DIR}/tables/Cliquid_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Cliquid_eos_i",
                    rho0=3.688, T0_eV=0.1, eta_max=4.5),
    "Cphenolic": dict(eeos=f"{TABLES_DIR}/tables/Cphenolic_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Cphenolic_eos_i",
                    rho0=1.4503, T0_eV=0.1, eta_max=4.5),
    "Cu": dict(eeos=f"{TABLES_DIR}/tables/Cu_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Cu_eos_i",
                    rho0=8.96, T0_eV=0.1, eta_max=4.5),
    "D": dict(eeos=f"{TABLES_DIR}/tables/D_eos_e",
                    ieos=f"{TABLES_DIR}/tables/D_eos_i",
                    rho0=0.1766, T0_eV=0.1, eta_max=4.5),
    "DD": dict(eeos=f"{TABLES_DIR}/tables/DD_eos_e",
                    ieos=f"{TABLES_DIR}/tables/DD_eos_i",
                    rho0=0.353, T0_eV=0.1, eta_max=4.5),
    "C_wk": dict(eeos=f"{TABLES_DIR}/tables/C_wk_eos_e",
                 ieos=f"{TABLES_DIR}/tables/C_wk_eos_i",
                 rho0=3.51, T0_eV=0.1, eta_max=4.5),
    "Diamond": dict(eeos=f"{TABLES_DIR}/tables/Diamond_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Diamond_eos_i",
                    rho0=3.51, T0_eV=0.1, eta_max=4.5),
    "Eu": dict(eeos=f"{TABLES_DIR}/tables/Eu_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Eu_eos_i",
                    rho0=5.253, T0_eV=0.1, eta_max=4.5),
    "Fe": dict(eeos=f"{TABLES_DIR}/tables/Fe_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Fe_eos_i",
                    rho0=7.874, T0_eV=0.1, eta_max=4.5),
    "Fe_wk": dict(eeos=f"{TABLES_DIR}/tables/Fe_wk_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Fe_wk_eos_i",
                    rho0=7.874, T0_eV=0.1, eta_max=4.5),
    "Gd": dict(eeos=f"{TABLES_DIR}/tables/Gd_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Gd_eos_i",
                    rho0=7.898, T0_eV=0.1, eta_max=4.5),
    "Glass": dict(eeos=f"{TABLES_DIR}/tables/Glass_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Glass_eos_i",
                    rho0=2.65, T0_eV=0.1, eta_max=4.5),
    "H": dict(eeos=f"{TABLES_DIR}/tables/H_eos_e",
                    ieos=f"{TABLES_DIR}/tables/H_eos_i",
                    rho0=0.0884, T0_eV=0.1, eta_max=4.5),
    "He": dict(eeos=f"{TABLES_DIR}/tables/He_eos_e",
                    ieos=f"{TABLES_DIR}/tables/He_eos_i",
                    rho0=0.4, T0_eV=0.1, eta_max=4.5),
    "H_wk": dict(eeos=f"{TABLES_DIR}/tables/H_wk_eos_e",
                    ieos=f"{TABLES_DIR}/tables/H_wk_eos_i",
                    rho0=0.0884, T0_eV=0.1, eta_max=4.5),
    "Kr": dict(eeos=f"{TABLES_DIR}/tables/Kr_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Kr_eos_i",
                    rho0=2.5005, T0_eV=0.1, eta_max=4.5),
    "Li": dict(eeos=f"{TABLES_DIR}/tables/Li_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Li_eos_i",
                    rho0=0.5326, T0_eV=0.1, eta_max=4.5),
    "LiD": dict(eeos=f"{TABLES_DIR}/tables/LiD_eos_e",
                    ieos=f"{TABLES_DIR}/tables/LiD_eos_i",
                    rho0=0.883, T0_eV=0.1, eta_max=4.5),
    "LiH": dict(eeos=f"{TABLES_DIR}/tables/LiH_eos_e",
                    ieos=f"{TABLES_DIR}/tables/LiH_eos_i",
                    rho0=0.775, T0_eV=0.1, eta_max=4.5),
    "Mg": dict(eeos=f"{TABLES_DIR}/tables/Mg_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Mg_eos_i",
                    rho0=1.74, T0_eV=0.1, eta_max=4.5),
    "Mo": dict(eeos=f"{TABLES_DIR}/tables/Mo_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Mo_eos_i",
                    rho0=10.2, T0_eV=0.1, eta_max=4.5),
    "Mylar": dict(eeos=f"{TABLES_DIR}/tables/Mylar_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Mylar_eos_i",
                    rho0=1.38, T0_eV=0.1, eta_max=4.5),
    "N": dict(eeos=f"{TABLES_DIR}/tables/N_eos_e",
                    ieos=f"{TABLES_DIR}/tables/N_eos_i",
                    rho0=0.8572, T0_eV=0.1, eta_max=4.5),
    "Ne": dict(eeos=f"{TABLES_DIR}/tables/Ne_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Ne_eos_i",
                    rho0=1.44, T0_eV=0.1, eta_max=4.5),
    "Ni": dict(eeos=f"{TABLES_DIR}/tables/Ni_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Ni_eos_i",
                    rho0=8.882, T0_eV=0.1, eta_max=4.5),
    "O": dict(eeos=f"{TABLES_DIR}/tables/O_eos_e",
                    ieos=f"{TABLES_DIR}/tables/O_eos_i",
                    rho0=1.262, T0_eV=0.1, eta_max=4.5),
    "Parylene": dict(eeos=f"{TABLES_DIR}/tables/Parylene_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Parylene_eos_i",
                    rho0=1.42, T0_eV=0.1, eta_max=4.5),
    "Pb": dict(eeos=f"{TABLES_DIR}/tables/Pb_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Pb_eos_i",
                    rho0=11.34, T0_eV=0.1, eta_max=4.5),
    "Pb_wk": dict(eeos=f"{TABLES_DIR}/tables/Pb_wk_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Pb_wk_eos_i",
                    rho0=11.34, T0_eV=0.1, eta_max=4.5),
    "PE": dict(eeos=f"{TABLES_DIR}/tables/PE_eos_e",
                    ieos=f"{TABLES_DIR}/tables/PE_eos_i",
                    rho0=0.954, T0_eV=0.1, eta_max=4.5),
    "PS": dict(eeos=f"{TABLES_DIR}/tables/PS_eos_e",
                    ieos=f"{TABLES_DIR}/tables/PS_eos_i",
                    rho0=1.044, T0_eV=0.1, eta_max=4.5),
    "PU": dict(eeos=f"{TABLES_DIR}/tables/PU_eos_e",
                    ieos=f"{TABLES_DIR}/tables/PU_eos_i",
                    rho0=1.265, T0_eV=0.1, eta_max=4.5),
    "Si": dict(eeos=f"{TABLES_DIR}/tables/Si_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Si_eos_i",
                    rho0=2.42, T0_eV=0.1, eta_max=4.5),
    "SiO2wk14": dict(eeos=f"{TABLES_DIR}/tables/SiO2wk14_eos_e",
                    ieos=f"{TABLES_DIR}/tables/SiO2wk14_eos_i",
                    rho0=2.648, T0_eV=0.1, eta_max=4.5),
    "Sn": dict(eeos=f"{TABLES_DIR}/tables/Sn_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Sn_eos_i",
                    rho0=7.29, T0_eV=0.1, eta_max=4.5),
    "SS": dict(eeos=f"{TABLES_DIR}/tables/SS_eos_e",
                    ieos=f"{TABLES_DIR}/tables/SS_eos_i",
                    rho0=7.91, T0_eV=0.1, eta_max=4.5),
    "Ta": dict(eeos=f"{TABLES_DIR}/tables/Ta_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Ta_eos_i",
                    rho0=16.654, T0_eV=0.1, eta_max=4.5),
    "Ti": dict(eeos=f"{TABLES_DIR}/tables/Ti_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Ti_eos_i",
                    rho0=4.54, T0_eV=0.1, eta_max=4.5),
    "U": dict(eeos=f"{TABLES_DIR}/tables/U_eos_e",
                    ieos=f"{TABLES_DIR}/tables/U_eos_i",
                    rho0=18.983, T0_eV=0.1, eta_max=4.5),
    "V": dict(eeos=f"{TABLES_DIR}/tables/V_eos_e",
                    ieos=f"{TABLES_DIR}/tables/V_eos_i",
                    rho0=6.11, T0_eV=0.1, eta_max=4.5),
    "W": dict(eeos=f"{TABLES_DIR}/tables/W_eos_e",
                    ieos=f"{TABLES_DIR}/tables/W_eos_i",
                    rho0=19.25, T0_eV=0.1, eta_max=4.5),
    "WC": dict(eeos=f"{TABLES_DIR}/tables/WC_eos_e",
                    ieos=f"{TABLES_DIR}/tables/WC_eos_i",
                    rho0=14.97, T0_eV=0.1, eta_max=4.5),
    "Xe": dict(eeos=f"{TABLES_DIR}/tables/Xe_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Xe_eos_i",
                    rho0=3.0551, T0_eV=0.1, eta_max=4.5),
    "Zn": dict(eeos=f"{TABLES_DIR}/tables/Zn_eos_e",
                    ieos=f"{TABLES_DIR}/tables/Zn_eos_i",
                    rho0=7.139, T0_eV=0.1, eta_max=4.5),
}
# 等温(冷)压缩线: 诊断用——若提取点贴此线而非 Hugoniot 自洽线, 说明波前是
# 辐射介导的等温压缩波而非惯性冲击(光学薄材料的典型失效模式, 见 pitfalls)
COLD_LOCUS = {
    "PSFlash": dict(eeos=f"{TABLES_DIR}/tables/PSFlash_eos_e",
                    ieos=f"{TABLES_DIR}/tables/PSFlash_eos_i",
                    rho0=1.05, T_eV=2.0, eta_max=10.0),
    "AlFlash": dict(eeos=f"{TABLES_DIR}/tables/AlFlash_eos_e",
                    ieos=f"{TABLES_DIR}/tables/AlFlash_eos_i",
                    rho0=2.7, T_eV=1.0, eta_max=10.0),
}
# 交叉参照线: 用库内其他材料的表自洽线对比 (点线, 非独立理论)
REF_HUG = {
    # 碳表代理 BN (2026-09-10): 交叉参照被代理的邢展彬表自洽线, 直接显示
    # "换碳表" 相对 "库内 BN 表" 的偏移
    "cBNCpx": [dict(label="cBNHub table self (cross-ref, ρ0=3.45)",
                    eeos=f"{TABLES_DIR}/tables/cBNHub_eos_e",
                    ieos=f"{TABLES_DIR}/tables/cBNHub_eos_i",
                    rho0=3.45, T0_eV=0.02585257, eta_max=4.5)],
    "hBNCpx": [dict(label="hBNHub table self (cross-ref, ρ0=2.04)",
                    eeos=f"{TABLES_DIR}/tables/hBNHub_eos_e",
                    ieos=f"{TABLES_DIR}/tables/hBNHub_eos_i",
                    rho0=2.04, T0_eV=0.0259, eta_max=6.0)],
    "CH": [dict(label="PS table self (cross-ref, ρ0=1.044)",
                eeos=f"{TABLES_DIR}/tables/PS_eos_e",
                ieos=f"{TABLES_DIR}/tables/PS_eos_i",
                rho0=1.044, T0_eV=0.1, eta_max=4.5)],
    # 库内另一张铝表交叉参照 (AlFEOS=FEOS 3717; ρ0=2.7); stock Al 为打包多节
    # 文件(read_ieos 只读首表), 不列入交叉参照
    "AlFlash": [dict(label="AlFEOS table self (cross-ref, ρ0=2.7)",
                     eeos=f"{TABLES_DIR}/tables/AlFEOS_eos_e",
                     ieos=f"{TABLES_DIR}/tables/AlFEOS_eos_i",
                     rho0=2.7, T0_eV=0.1, eta_max=4.5)],
}
# ParyleneHub: 交叉参照库内 hyades 源 Parylene 表 (独立第二来源)
REF_HUG["ParyleneHub"] = [dict(label="Parylene hyades table (cross-ref, rho0=1.28)",
                               eeos=f"{TABLES_DIR}/tables/Parylene_eos_e",
                               ieos=f"{TABLES_DIR}/tables/Parylene_eos_i",
                               rho0=1.28, T0_eV=0.1, eta_max=4.5)] if __import__("os").path.exists(f"{TABLES_DIR}/tables/Parylene_eos_e") else []

# LiFHub: 交叉参照库内 WeiKang LiF 表 (独立第二来源, 12x128)
REF_HUG["LiFHub"] = [dict(label="LiF_wk table (cross-ref, rho0=2.64)",
                          eeos=f"{TABLES_DIR}/tables/LiF_wk_eos_e",
                          ieos=f"{TABLES_DIR}/tables/LiF_wk_eos_i",
                          rho0=2.64, T0_eV=5.0, eta_max=4.0)]
# 解析拟合误差模型(按标签子串匹配), 与 IM-tool data_loader.compute_material_error_bands 一致
ERR_MODELS = {
    "Celliers": dict(model="linear", a0=17.992, s_a0=0.078,
                     a1=1.167, s_a1=0.026, beta=9.838),
    "Hamel": dict(model="piecewise_quadratic", a=2.4, s_a=0.1,
                  b=1.68, s_b=0.02, c=-0.0155, s_c=0.001, break_up=15.0),
}


def err_band(key, up):
    """返回 (Us, sigma_Us): 按 IM-tool 误差模型逐点计算 (up 单位 km/s)"""
    e = ERR_MODELS[key]
    up = np.asarray(up, dtype=float)
    if e["model"] == "linear":
        us = e["a0"] + e["a1"] * (up - e["beta"])
        sig = np.sqrt(e["s_a0"] ** 2 + (up - e["beta"]) ** 2 * e["s_a1"] ** 2)
    else:  # piecewise_quadratic
        a, b, c, br = e["a"], e["b"], e["c"], e["break_up"]
        us = np.where(up < br, a + b * up + c * up ** 2,
                      (a - c * br ** 2) + b * up + 2 * c * br * up)
        ddc = np.where(up < br, up ** 2, 2 * br * up - br ** 2)
        sig = np.sqrt(e["s_a"] ** 2 + up ** 2 * e["s_b"] ** 2 + ddc ** 2 * e["s_c"] ** 2)
    return us, sig

# IM-tool 材料线颜色轮换顺序
LINE_COLORS = [ps.PRL_COLORS["blue"], ps.PRL_COLORS["red"],
               ps.PRL_COLORS["green"], ps.PRL_COLORS["orange"],
               ps.PRL_COLORS["purple"], ps.PRL_COLORS["black"]]


def load_theory_txt(path):
    """IM-tool txt: # 注释 + 列头行, tab 分隔: Up Us P rho ... (km/s, Mbar, g/cc)"""
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith("#") or not line.strip() or line.startswith("Up("):
                continue
            parts = line.rstrip("\n").split("\t")
            try:
                rows.append(tuple(float(parts[i]) for i in range(4)))
            except (ValueError, IndexError):
                continue
    return np.array(rows)          # columns: Up, Us, P, rho


def load_theory_hug(path):
    """FEOS .hug: Rho[g/cc] T[eV] P[1e12dyn/cm2=Mbar] E Us[1e5cm/s=km/s] Up"""
    a = np.loadtxt(path, comments="#")
    return np.column_stack([a[:, 5], a[:, 4], a[:, 2], a[:, 0]])


def load_theory_usup_csv(path):
    """ZhangHuan Us-Up csv: # 注释 + 列名行 Up,Us (km/s)。无 P/rho 列 → NaN 填充"""
    a = np.loadtxt(path, delimiter=",", comments="#", skiprows=2)
    return np.column_stack([a[:, 0], a[:, 1], np.full(len(a), np.nan), np.full(len(a), np.nan)])


def load_theory_csv_prho(path):
    """IM-tool reference_curves CSV: 前 2 行为列名/单位行, 数据列 compression,rho,P
    (rho g/cc, P Mbar)。Us/Up 由 RH 质量+动量关系换算 (P0≈0):
    Us = sqrt(P1/(rho0*(1-rho0/rho1))), Up = Us*(1-rho0/rho1)"""
    a = np.loadtxt(path, delimiter=",", skiprows=2)
    comp, rho, p = a[:, 0], a[:, 1], a[:, 2]
    rho0 = rho[0] / comp[0]
    m = comp > 1.0
    comp, rho, p = comp[m], rho[m], p[m]
    us = np.sqrt(p * 1e12 / (rho0 * (1.0 - rho0 / rho))) / 1e5
    up = us * (1.0 - rho0 / rho)
    out = np.column_stack([up, us, p, rho])
    # 源文件高能段为往返扫描(Up 非单调), 按 Up 排序保证曲线与插值良构
    return out[np.argsort(out[:, 0])]


def load_theory(mat):
    out = []
    for fname, label in THEORY_TXT.get(mat, []):
        if fname.startswith("__HUG__:"):
            path = fname[len("__HUG__:"):]
        else:
            path = os.path.join(IM_MAT, fname)
        if not os.path.exists(path):
            continue
        if "zhanghuan_usup" in fname:
            arr = load_theory_usup_csv(path)
        elif fname.endswith(".hug"):
            arr = load_theory_hug(path)
        elif fname.endswith(".csv"):
            arr = load_theory_csv_prho(path)
        else:
            arr = load_theory_txt(path)
        out.append((label, arr))
    return out


def main():
    mat, rho0 = sys.argv[1], float(sys.argv[2])
    case_dirs = sys.argv[3:]
    allpts = []
    for d in case_dirs:
        tag = os.path.basename(d.rstrip("/"))
        try:
            # HUG_NPOINTS: 每算例均匀采样记录数(默认 24; 提密只增采样不改门禁,
            # 用于后期记录才达内符合 ≤1% 的材料, 如 Diamond 2026-08-24)
            res = extract_series(d, rho0, n_points=int(os.environ.get("HUG_NPOINTS", 24)))
        except Exception as e:
            print(f"{tag}: 提取失败 {e}")
            continue
        print(f"{tag}: {len(res)} 个采信点 (门禁 A-E 全过)")
        for r in res:
            r["case"] = tag
        allpts.extend(res)

    outdir = os.path.join(os.path.dirname(case_dirs[0].rstrip("/")), "hugoniot_summary")
    os.makedirs(outdir, exist_ok=True)
    # CSV
    csv = os.path.join(outdir, f"{mat}_hugoniot_points.csv")
    with open(csv, "w") as f:
        f.write("case,t_ns,Us_kms,Up_kms,P_Mbar,rho1_gcc,rho0_gcc,P0_Mbar,"
                "v0_kms,RH_resid,fit_r2,rec,i_front\n")
        for r in allpts:
            f.write(f"{r['case']},{r['t']*1e9:.3f},{r['Us']/1e5:.4f},{r['Up']/1e5:.4f},"
                    f"{r['P1']/1e12:.4f},{r['rho1']:.4f},{r['rho0']:.4f},"
                    f"{r['P0']/1e12:.4f},{r['v0']/1e5:.4f},{r['resid']:+.4f},"
                    f"{r['fit_r2']:.5f},{r['rec']},{r['i_front']}\n")
    print(f"CSV: {csv}  ({len(allpts)} 点)")
    if not allpts:
        return

    theory = load_theory(mat)

    # ---- 绘图数据落盘: plot_data/ 下每条理论线一个 CSV + 模拟点 CSV ----
    pdir = os.path.join(outdir, "plot_data")
    os.makedirs(pdir, exist_ok=True)
    for label, arr in theory:
        fname = label.replace(" (", "_").replace(")", "").replace(" ", "_")
        tc = os.path.join(pdir, f"theory_{fname}.csv")
        with open(tc, "w") as f:
            f.write(f"# {label}, 来源: {IM_MAT}\n")
            f.write("Up_kms,Us_kms,P_Mbar,rho_gcc\n")
            for row in arr:
                f.write(f"{row[0]:.6e},{row[1]:.6e},{row[2]:.6e},{row[3]:.6e}\n")
        print(f"绘图数据: {tc}  ({len(arr)} 点)")
    # 误差带数据 (所有带误差模型的理论线)
    for label, _arr in theory:
        key = next((k for k in ERR_MODELS if k in label), None)
        if key is None:
            continue
        fname = label.replace(" (", "_").replace(")", "").replace(" ", "_")
        ec = os.path.join(pdir, f"theory_{fname}_errorband.csv")
        with open(ec, "w") as f:
            f.write(f"# {label} 误差带 (模型: {ERR_MODELS[key]['model']}, 参数: {ERR_MODELS[key]})\n")
            f.write("Up_kms,Us_kms,Us_sigma_kms\n")
            up = np.linspace(0, 30, 301)
            us, sig = err_band(key, up)
            for u, s, g in zip(up, us, sig):
                f.write(f"{u:.6e},{s:.6e},{g:.6e}\n")
        print(f"绘图数据: {ec}")
    mc = os.path.join(pdir, f"multi_points_{mat}.csv")
    with open(mc, "w") as f:
        f.write("# MULTI-1D 提取点(与 ../<mat>_hugoniot_points.csv 同内容, 绘图用列序)\n")
        f.write("case,Up_kms,Us_kms,P_Mbar,rho1_gcc,RH_resid,high_conf\n")
        for r in allpts:
            f.write(f"{r['case']},{r['Up']/1e5:.6e},{r['Us']/1e5:.6e},"
                    f"{r['P1']/1e12:.6e},{r['rho1']:.6e},{r['resid']:+.4f},"
                    f"{int(abs(r['resid']) <= 0.01)}\n")
    print(f"绘图数据: {mc}")

    # ---- 表自洽 Hugoniot 线 (SELF_HUG 登记的材料): 计算 + 落盘 ----
    self_locus = None
    if mat in SELF_HUG:
        from compute_table_hugoniot import solve_hugoniot
        cfg = SELF_HUG[mat]
        self_locus = solve_hugoniot(cfg["eeos"], cfg["ieos"], cfg["rho0"],
                                    cfg["T0_eV"], cfg["eta_max"])
        sc = os.path.join(pdir, f"self_hugoniot_{mat}.csv")
        with open(sc, "w") as f:
            f.write(f"# {mat} 表自洽 Hugoniot 线 (eeos+ieos 反解 RH 能量方程, "
                    f"rho0={cfg['rho0']}, T0={cfg['T0_eV']} eV; 非独立理论验证)\n")
            f.write("rho1_gcc,T_eV,P_Mbar,Us_kms,Up_kms\n")
            for i in range(len(self_locus["rho1"])):
                f.write(f"{self_locus['rho1'][i]:.6e},{self_locus['T_eV'][i]:.6e},"
                        f"{self_locus['P_Mbar'][i]:.6e},{self_locus['Us_kms'][i]:.6e},"
                        f"{self_locus['Up_kms'][i]:.6e}\n")
        print(f"绘图数据: {sc}  ({len(self_locus['rho1'])} 点)")

    # ---- 交叉参照自洽线 (REF_HUG: 其他材料表的自洽线) ----
    ref_loci = []
    if mat in REF_HUG:
        from compute_table_hugoniot import solve_hugoniot
        for cfg in REF_HUG[mat]:
            loc = solve_hugoniot(cfg["eeos"], cfg["ieos"], cfg["rho0"],
                                 cfg["T0_eV"], cfg["eta_max"])
            ref_loci.append((cfg["label"], loc))
            rc = os.path.join(pdir, f"ref_hugoniot_{cfg['label'].split(' ')[0]}.csv")
            with open(rc, "w") as f:
                f.write(f"# {cfg['label']} (交叉参照, 表自洽反解, 非独立理论)\n")
                f.write("rho1_gcc,T_eV,P_Mbar,Us_kms,Up_kms\n")
                for i in range(len(loc["rho1"])):
                    f.write(f"{loc['rho1'][i]:.6e},{loc['T_eV'][i]:.6e},"
                            f"{loc['P_Mbar'][i]:.6e},{loc['Us_kms'][i]:.6e},"
                            f"{loc['Up_kms'][i]:.6e}\n")
            print(f"绘图数据: {rc}  ({len(loc['rho1'])} 点)")

    # ---- 等温(冷)压缩线 (COLD_LOCUS 登记的材料): 计算 + 落盘 ----
    cold_locus = None
    if mat in COLD_LOCUS:
        from compute_table_hugoniot import IEOSEval
        cfg = COLD_LOCUS[mat]
        ele = IEOSEval(cfg["eeos"]); ion = IEOSEval(cfg["ieos"])
        TK = cfg["T_eV"] * 11604.519
        rhos, Ps, Uss, Ups = [], [], [], []
        for eta in np.linspace(1.01, cfg["eta_max"], 80):
            r1 = cfg["rho0"] * eta
            p1 = ele(r1, TK)[0] + ion(r1, TK)[0]
            p0 = ele(cfg["rho0"], TK)[0] + ion(cfg["rho0"], TK)[0]
            if p1 <= p0 or p1 * 1e12 / (cfg["rho0"] * (1 - cfg["rho0"] / r1)) <= 0:
                continue
            us = np.sqrt((p1 - p0) * 1e12 / (cfg["rho0"] * (1 - cfg["rho0"] / r1))) / 1e5
            rhos.append(r1); Ps.append(p1); Uss.append(us); Ups.append(us * (1 - cfg["rho0"] / r1))
        cold_locus = dict(rho1=np.array(rhos), P_Mbar=np.array(Ps),
                          Us_kms=np.array(Uss), Up_kms=np.array(Ups))
        cc = os.path.join(pdir, f"cold_isotherm_{mat}.csv")
        with open(cc, "w") as f:
            f.write(f"# {mat} 等温(冷)压缩线 T={cfg['T_eV']} eV (诊断参考: 贴此线=辐射介导等温波, 非冲击)\n")
            f.write("rho1_gcc,P_Mbar,Us_kms,Up_kms\n")
            for i in range(len(rhos)):
                f.write(f"{rhos[i]:.6e},{Ps[i]:.6e},{Uss[i]:.6e},{Ups[i]:.6e}\n")
        print(f"绘图数据: {cc}  ({len(rhos)} 点)")

    for plane in ("UsUp", "Prho"):
        fig, ax = plt.subplots(figsize=(6.0, 6.0))
        # 理论线: 实线, IM-tool 颜色轮换
        for i, (label, arr) in enumerate(theory):
            up, us, p, rho = arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3]
            if plane == "Prho" and np.isnan(p).all():
                continue  # 仅 Us-Up 关系线 (无 P/rho 数据), 不进 P-rho 面板
            # 理论线覆盖不足时, 沿末段线性外推 Us(Up) 并按 RH 换算 P/ρ, 虚线延长
            up_need = max(r["Up"] / 1e5 for r in allpts) * 1.1
            if up.max() < up_need and up[-1] > up[-2]:  # 需外推且斜率有限
                r0 = np.median(rho * (us - up) / us)   # 由线自身 RH 反推 ρ0
                k = (us[-1] - us[-2]) / (up[-1] - up[-2])
                upx = np.linspace(up[-1], up_need, 60)
                usx = us[-1] + k * (upx - up[-1])
                x2, y2 = ((upx, usx) if plane == "UsUp"
                          else (r0 * usx / (usx - upx), r0 * usx * upx * 1e-2))
                ax.plot(x2, y2, color=LINE_COLORS[i % len(LINE_COLORS)],
                        lw=1.2, ls="--", zorder=1)
            x, y = (up, us) if plane == "UsUp" else (rho, p)
            ax.plot(x, y, color=LINE_COLORS[i % len(LINE_COLORS)], lw=1.5,
                    ls="-", label=label, zorder=1)
            # 误差带 (仅 Us-Up 平面, 误差模型定义在 Us 上)
            key = next((k for k in ERR_MODELS if k in label), None)
            if plane == "UsUp" and key is not None:
                ug = np.linspace(up.min(), min(up.max(), 30), 200)
                usg, sig = err_band(key, ug)
                ax.fill_between(ug, usg - sig, usg + sig, alpha=0.12,
                                color=LINE_COLORS[i % len(LINE_COLORS)], zorder=0)
        # 等温(冷)压缩线: 点划线 (诊断参考)
        if cold_locus is not None:
            cx = cold_locus["Up_kms"] if plane == "UsUp" else cold_locus["rho1"]
            cy = cold_locus["Us_kms"] if plane == "UsUp" else cold_locus["P_Mbar"]
            ax.plot(cx, cy, color="0.55", lw=1.4, ls="-.",
                    label=f"{mat} isotherm T={COLD_LOCUS[mat]['T_eV']} eV (diagnostic)",
                    zorder=1.5)
        # 模拟点: 统一黑圆点, 只画高置信点 (RH 残差 ≤1%); 低置信点留在 CSV 不上图
        sel = [r for r in allpts if abs(r["resid"]) <= 0.01]
        xx = [r["Up"] / 1e5 if plane == "UsUp" else r["rho1"] for r in sel]
        yy = [r["Us"] / 1e5 if plane == "UsUp" else r["P1"] / 1e12 for r in sel]
        ax.plot(xx, yy, "o", ms=7, mfc="black", mec="black", mew=1.2, ls="None",
                label="MULTI-1D", zorder=6)
        # 表自洽线: 灰虚线 (非独立理论, 一致性判据)
        if self_locus is not None:
            sx = self_locus["Up_kms"] if plane == "UsUp" else self_locus["rho1"]
            sy = self_locus["Us_kms"] if plane == "UsUp" else self_locus["P_Mbar"]
            ax.plot(sx, sy, color="0.4", lw=1.5, ls="--",
                    label=f"{mat} table (self-consistency, ρ0={SELF_HUG[mat]['rho0']})",
                    zorder=2)
        # 交叉参照自洽线: 彩色点线
        for k, (rlabel, loc) in enumerate(ref_loci):
            rx = loc["Up_kms"] if plane == "UsUp" else loc["rho1"]
            ry = loc["Us_kms"] if plane == "UsUp" else loc["P_Mbar"]
            ax.plot(rx, ry, color=LINE_COLORS[(k + len(theory)) % len(LINE_COLORS)],
                    lw=1.3, ls=":", label=rlabel, zorder=2)
        # 轴范围跟随实际出图点(高置信), 无高置信点则回退到全部点
        ref = sel if sel else allpts
        if plane == "UsUp":
            xmax = max(r["Up"] / 1e5 for r in ref) * 1.12
            ymax = max(r["Us"] / 1e5 for r in ref) * 1.12
            ps.apply_prl_style(fig, ax, xlabel=ps.LABEL_UP, ylabel=ps.LABEL_US,
                               xlim=(0, xmax), ylim=(0, ymax))
        else:
            xmax = max(r["rho1"] for r in ref) * 1.12
            ymax = max(r["P1"] / 1e12 for r in ref) * 1.12
            ps.apply_prl_style(fig, ax, xlabel=ps.LABEL_RHO, ylabel=ps.LABEL_P,
                               xlim=(rho0 * 0.95, xmax), ylim=(0, ymax))
        ax.legend(loc="best", fontsize=ps.LEGEND_FONTSIZE * 0.8)
        png = os.path.join(outdir, f"{mat}_hugoniot_{plane}.png")
        ps.save_prl_figure(fig, png)
        plt.close(fig)
        print(f"图: {png}")


if __name__ == "__main__":
    main()
