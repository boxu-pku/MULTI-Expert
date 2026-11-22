#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_hugoniot_cases.py — 生成 Hugoniot 校验算例（厚平板 + 恒定辐射浴驱动）

物理设计: 厚平板材料, 一端(右侧)施加恒定辐射温度浴 → 准定常冲击波向另一端传播。
提取波前轨迹得 Us, 波后质点速度 Up, 压力 P, 密度 rho → Hugoniot 关系点。

用法: python3 make_hugoniot_cases.py <材料名> <rho0> <厚度cm> <trad列表,逗号分隔>
示例: python3 make_hugoniot_cases.py Al 2.7 1e-2 50,100,200,300

2026-08-19 起标准配置 (用户定版, BN 族验证得出, 见 Hugoniot校验流程.md):
  - quiet start: iquiet=1, tquiet=0.05 eV (冻结冷固态单元流体, 消波前驱污染)
  - 冷初态: te0=ti0=0.03 eV (~350 K, 贴参考线 300 K 初态)
  - 注意: 需 2026-08-18 13:47 后含 quiet start 的 m150304.f95 重编译 multi,
    旧 binary 遇 iquiet 报 "Cannot match namelist object name iquiet"
"""
import os
import sys

MULTI = "/home/ubuntu/local/MULTI-2D.2026.3"
CASES = f"{MULTI}/validation_cases"

# 各材料的 1D 表配置: (eeos_file, eeos_id, ieos_file, ieos_id, z_file, z_id,
#                    planck_file, planck_id, ross_file, ross_id, zi, ai)
# inegpre: FEOS/AQUA 水表冷端 Pe 为源生负值, 钳正(inegpre=0)致 rad-电子耦合
# 奇异(solve3/tridia), 必须 inegpre=1 (2026-08-14 诊断, 见 pitfalls)
MAT_INEGPRE = {"WaterFEOS": 1, "WaterAQUA": 1, "hBNHub": 1, "cBNHub": 1,
               "cBNCpx": 1, "hBNCpx": 1}
# z_id=-1 表示不挂 Z 表 (load_table mode 3 对 id<0 直接跳过)
MAT_TABLES = {
    "Al": ("tables/Al", 10000304, "tables/Al", 10000305, "tables/Al", 10002000,
           "tables/Al", 10003000, "tables/Al", 10004000, 13.0, 26.9815),
    # CH 塑料 (Multi_BACK mat_CH-1.0, ρ0=1.044): CELIA 20 群不透明度 + ZEFF
    "CH": ("tables/CH_eos_e", 3500304, "tables/CH_eos_i", 3500305,
           "tables/CH_CELIA.ZEFF", 1, "tables/CH_CELIA.PLANCK", 10003000,
           "tables/CH_CELIA.ROSS", 10004000, 3.5, 6.51),
    # FLASH LaserSlab 聚苯乙烯 (IONMIX4 polystyrene-imx-008, EOS-tools 转换,
    # ρ0=1.05): 自带 6 群不透明度 + ZEFF + EPS(校验算例不挂发射, 保持族可比性)
    "PSFlash": ("tables/PSFlash_eos_e", 3501304, "tables/PSFlash_eos_i", 3501305,
                "tables/PSFlash.ZEFF", 1, "tables/PSFlash.PLANCK", 10013000,
                "tables/PSFlash.ROSS", 10014000, 3.5, 6.51),
    # Multi_BACK hyades 族 α-石英(ρ0=2.65; 2026-08-14 改名前叫 Silica), opc 1022
    "Quartz": ("tables/Quartz_eos_e", 10000304, "tables/Quartz_eos_i", 10000305,
               "", -1, "tables/Quartz_OPC.PLANCK", 1022,
               "tables/Quartz_OPC.ROSS", 1022, 10.0, 20.028),
    # Multi_BACK hyades 族熔石英玻璃(ρ0=2.204; 改名前叫 Quartz), opc 1022
    "Silica": ("tables/Silica_eos_e", 10000304, "tables/Silica_eos_i", 10000305,
               "", -1, "tables/Silica_OPC.PLANCK", 1022,
               "tables/Silica_OPC.ROSS", 1022, 10.0, 20.028),
    # WeiKang DFT 表(α-quartz 2.648), 不透明度借 Quartz opc 1022; 表 T≤10 eV,
    # 驱动 trad 不宜超 ~75 eV, 防止波后出表
    "SiO2wk12": ("tables/SiO2wk12_eos_e", 10000304, "tables/SiO2wk12_eos_i", 10000305,
                 "", -1, "tables/Quartz_OPC.PLANCK", 1022,
                 "tables/Quartz_OPC.ROSS", 1022, 10.0, 20.03),
    # FEOS 模型表 (EOS-tools 转换): SilicaFEOS=熔石英 2.204(mat 7386),
    # QuartzFEOS=α-石英 2.65(mat 7387); 不透明度借 opc 1022
    "SilicaFEOS": ("tables/SilicaFEOS_eos_e", 10000304, "tables/SilicaFEOS_eos_i", 10000305,
                   "", -1, "tables/Silica_OPC.PLANCK", 1022,
                   "tables/Silica_OPC.ROSS", 1022, 10.0, 20.028),
    "QuartzFEOS": ("tables/QuartzFEOS_eos_e", 10000304, "tables/QuartzFEOS_eos_i", 10000305,
                   "", -1, "tables/Quartz_OPC.PLANCK", 1022,
                   "tables/Quartz_OPC.ROSS", 1022, 10.0, 20.028),
    # FEOS 模型水 (EOS-tools 转换, mat 7100/SESAME 7154); 不透明度借 Water opc 1311
    "WaterFEOS": ("tables/WaterFEOS_eos_e", 3330304, "tables/WaterFEOS_eos_i", 3330305,
                  "", -1, "tables/Water_OPC.PLANCK", 1311,
                  "tables/Water_OPC.ROSS", 1311, 3.333, 6.005),
    # AQUA 水 (EOS-tools aqua reader + split; T<=8.6 eV, 驱动 trad<=8 eV);
    # 不透明度借 Water opc 1311
    "WaterAQUA": ("tables/WaterAQUA_eos_e", 3330304, "tables/WaterAQUA_eos_i", 3330305,
                  "", -1, "tables/Water_OPC.PLANCK", 1311,
                  "tables/Water_OPC.ROSS", 1311, 3.333, 6.005),
    # EOS_hub LiF (SESAME 7270 3eos 拆分 + CEA CENS 40 群, ρ0=2.64)
    "LiFHub": ("tables/LiFHub_eos_e", 72700304, "tables/LiFHub_eos_i", 72700305,
               "tables/LiFHub.ZEFF", 1, "tables/LiFHub.PLANCK", 72703000,
               "tables/LiFHub.ROSS", 72704000, 6.0, 12.97),
    # EOS_hub Al (SESAME 3717 原生 e/i 对 + NG 40 群含 EPS, ρ0=2.7)
    "AlHub": ("tables/AlHub_eos_e", 37171304, "tables/AlHub_eos_i", 37171305,
              "tables/AlHub.ZEFF", 37172017, "tables/AlHub.PLANCK", 37173017,
              "tables/AlHub.ROSS", 37174017, 13.0, 26.98),
    # EOS_hub 邢展彬 FP BN 对 —— 2026-08-30 换新表 (work/zhanbin, 修正低密度区错误);
    # hBN rho0=2.04 (2026-08-18 身份翻案定版); 无原生不透明度 — 验证借用 N_Thermos,
    # 生产使用需注意
    "hBNHub": ("tables/hBNHub_eos_e", 21521304, "tables/hBNHub_eos_i", 21521305,
               "", -1, "tables/N_Thermos.PLANCK", 0,
               "tables/N_Thermos.ROSSELAND", 0, 12.0, 24.82),
    # 邢展彬 2026-08-30 新 FP cBN 对 (work/zhanbin, id 21531304/305, rho0=3.45;
    # 与 hBNHub 共用 ρ>3.5 数据分支, 差异全在低密度冷区; 借 N_Thermos 不透明度)
    "cBNHub": ("tables/cBNHub_eos_e", 21531304, "tables/cBNHub_eos_i", 21531305,
               "", -1, "tables/N_Thermos.PLANCK", 0,
               "tables/N_Thermos.ROSSELAND", 0, 12.0, 24.82),
    # 碳表代理 BN (2026-09-10, 用户导师提议: C 与 BN 性质类似, 碳表仅改初密度作
    # BN EOS): cBNCpx = Diamond 表字节副本(仅改 id, 数据逐值无损) @rho0=3.45,
    # 立方结构对应; 冷压零点在 3.515>3.45, 初态为拉伸张力 → inegpre=1 同 BN 族;
    # 借 N_Thermos 不透明度与 cBNHub 完全同配置, 保证 EOS 单变量对比
    "cBNCpx": ("tables/cBNCpx_eos_e", 21541304, "tables/cBNCpx_eos_i", 21541305,
               "", -1, "tables/N_Thermos.PLANCK", 0,
               "tables/N_Thermos.ROSSELAND", 0, 12.0, 24.82),
    # hBNCpx = Cliquid 表字节副本(仅改 id) @rho0=2.04, 石墨层状结构对应 hBN;
    # 源为液态碳无固相冷曲线 → 弱激波段(低 Up)不可信, 仅中高压段有判据意义;
    # 表 T 上限 681 eV, 驱动档 ≤200 eV
    "hBNCpx": ("tables/hBNCpx_eos_e", 21551304, "tables/hBNCpx_eos_i", 21551305,
               "", -1, "tables/N_Thermos.PLANCK", 0,
               "tables/N_Thermos.ROSSELAND", 0, 12.0, 24.82),
    # FEOS 重算 hBN (EOS-tools 从 hBN.feos 主表转, ρ0=2.04, 无原生不透明度借 N_Thermos)
    "hBNFEOS": ("tables/hBNFEOS_eos_e", 77770304, "tables/hBNFEOS_eos_i", 77770305,
                "", -1, "tables/N_Thermos.PLANCK", 0,
                "tables/N_Thermos.ROSSELAND", 0, 12.0, 24.82),
    # FEOS 重算 cBN (EOS-tools 从 cBN.feos 主表转, ρ0=3.4, 无原生不透明度借 N_Thermos)
    "cBNFEOS": ("tables/cBNFEOS_eos_e", 77800304, "tables/cBNFEOS_eos_i", 77800305,
                "", -1, "tables/N_Thermos.PLANCK", 0,
                "tables/N_Thermos.ROSSELAND", 0, 12.0, 24.82),
    # EOS_hub CH/聚苯乙烯 (SESAME 7592 总表拆分 + LANL C1H1 30 群, ρ0=1.044)
    "CHHub": ("tables/CHHub_eos_e", 75921304, "tables/CHHub_eos_i", 75921305,
              "tables/CHHub.ZEFF", 75922004, "tables/CHHub.PLANCK", 75923004,
              "tables/CHHub.ROSS", 75924004, 3.5, 6.5),
    # EOS_hub Parylene (SESAME 7770 拆分 + CEA CENS 40 群, ρ0=1.29)
    "ParyleneHub": ("tables/ParyleneHub_eos_e", 77700304, "tables/ParyleneHub_eos_i", 77700305,
                    "tables/ParyleneHub.ZEFF", 1, "tables/ParyleneHub.PLANCK", 77703000,
                    "tables/ParyleneHub.ROSS", 77704000, 5.5, 10.815),
    # Multi_BACK hyades 族水 (eos_311 宽表, opc 1311 单群, ρ0=1.0)
    "Water": ("tables/Water_eos_e", 3330304, "tables/Water_eos_i", 3330305,
              "", -1, "tables/Water_OPC.PLANCK", 1311,
              "tables/Water_OPC.ROSS", 1311, 3.333, 6.005),
    # FEOS 模型铝 (EOS-tools 转换, mat 3717, id 13000304/305);
    # 不透明度/Zeff 借自带 tables/Al (SNOP 20 群, id 10003000/10004000/10002000)
    "AlFEOS": ("tables/AlFEOS_eos_e", 13000304, "tables/AlFEOS_eos_i", 13000305,
               "tables/Al", 10002000, "tables/Al", 10003000,
               "tables/Al", 10004000, 13.0, 26.9815),
    # FLASH LaserSlab 铝 (IONMIX4 al-imx-003.cn4, EOS-tools 转换, ρ0=2.7):
    # 自带 6 群不透明度 + ZEFF + EPS(校验算例不挂发射, 保持族可比性)
    "AlFlash": ("tables/AlFlash_eos_e", 13001304, "tables/AlFlash_eos_i", 13001305,
                "tables/AlFlash.ZEFF", 1, "tables/AlFlash.PLANCK", 10023000,
                "tables/AlFlash.ROSS", 10024000, 13.0, 26.9815386),

    # ==== 2026-08-20 批量二轮 Hugoniot 补验（配置自动解析自各 XCheck data.in） ====
    "Ag": ("tables/Ag_eos_e", 47000304, "tables/Ag_eos_i", 47000305,
              'tables/Ag_Thermos.ZEFF', 0, "tables/Ag_Thermos.PLANCK", 0,
              "tables/Ag_Thermos.ROSSELAND", 0, 47, 107.87),
    "Air": ("tables/Air_eos_e", 7370304, "tables/Air_eos_i", 7370305,
              "", -1, "tables/Air_OPC.PLANCK", 1301,
              "tables/Air_OPC.ROSS", 1301, 7.373, 14.803),
    "Al2O3": ("tables/Al2O3_eos_e", 10000304, "tables/Al2O3_eos_i", 10000305,
              "", -1, "tables/Al2O3_OPC.PLANCK", 1161,
              "tables/Al2O3_OPC.ROSS", 1161, 10.0, 20.392),
    "Ar": ("tables/Ar_eos_e", 18000304, "tables/Ar_eos_i", 18000305,
              'tables/Ar_Thermos.ZEFF', 0, "tables/Ar_Thermos.PLANCK", 0,
              "tables/Ar_Thermos.ROSSELAND", 0, 18, 39.948),
    "Be_wk": ("tables/Be_wk_eos_e", 4000304, "tables/Be_wk_eos_i", 4000305,
              "", -1, "tables/Be20keV.PLANCK", 20143000,
              "tables/Be20keV.ROSS", 20144000, 4.0, 9.012),
    "CD2": ("tables/CD2_eos_e", 2670304, "tables/CD2_eos_i", 2670305,
              "", -1, "tables/CD2_OPC.PLANCK", 1344,
              "tables/CD2_OPC.ROSS", 1344, 2.667, 5.347),
    "CH2_wk": ("tables/CH2_wk_eos_e", 2670304, "tables/CH2_wk_eos_i", 2670305,
              "", -1, "tables/PE_OPC.PLANCK", 1031,
              "tables/PE_OPC.ROSS", 1031, 2.667, 4.676),
    "Cliquid": ("tables/Cliquid_eos_e", 6000304, "tables/Cliquid_eos_i", 6000305,
              "", -1, "tables/Cliquid_OPC.PLANCK", 1344,
              "tables/Cliquid_OPC.ROSS", 1344, 6.0, 12.011),
    "Cphenolic": ("tables/Cphenolic_eos_e", 4650304, "tables/Cphenolic_eos_i", 4650305,
              "", -1, "tables/Cphenolic_OPC.PLANCK", 1344,
              "tables/Cphenolic_OPC.ROSS", 1344, 4.648, 9.01),
    "Cu": ("tables/Cu_eos_e", 29000304, "tables/Cu_eos_i", 29000305,
              'tables/Cu_Thermos.ZEFF', 0, "tables/Cu_Thermos.PLANCK", 0,
              "tables/Cu_Thermos.ROSSELAND", 0, 29, 63.546),
    "D": ("tables/D_eos_e", 1000304, "tables/D_eos_i", 1000305,
              'tables/D_CELIA.ZEFF', 1, "tables/D_CELIA.PLANCK", 10003000,
              "tables/D_CELIA.ROSS", 10004000, 1, 2.014),
    "DD": ("tables/DD_eos_e", 2000304, "tables/DD_eos_i", 2000305,
              'tables/DD_CELIA.ZEFF', 1, "tables/DD_CELIA.PLANCK", 10003000,
              "tables/DD_CELIA.ROSS", 10004000, 2, 4.028),
    # C_wk (刘兴碳, 2026-08-25 重建: Sheet1 修正源, 见 rebuild_cwk_corrected.py)
    "C_wk": ("tables/C_wk_eos_e", 6000304, "tables/C_wk_eos_i", 6000305,
             "tables/C_wk_CELIA.ZEFF", 1, "tables/C_wk_CELIA.PLANCK", 10003000,
             "tables/C_wk_CELIA.ROSS", 10004000, 6.0, 12.011),
    "Diamond": ("tables/Diamond_eos_e", 6000304, "tables/Diamond_eos_i", 6000305,
              "", -1, "tables/Diamond_OPC.PLANCK", 1344,
              "tables/Diamond_OPC.ROSS", 1344, 6.0, 12.011),
    "Eu": ("tables/Eu_eos_e", 63000304, "tables/Eu_eos_i", 63000305,
              "", -1, "tables/Eu_OPC.PLANCK", 1461,
              "tables/Eu_OPC.ROSS", 1461, 63.0, 151.96),
    "Fe": ("tables/Fe_eos_e", 26000304, "tables/Fe_eos_i", 26000305,
              'tables/Fe_Thermos.ZEFF', 0, "tables/Fe_Thermos.PLANCK", 0,
              "tables/Fe_Thermos.ROSSELAND", 0, 26, 55.845),
    "Fe_wk": ("tables/Fe_wk_eos_e", 26000304, "tables/Fe_wk_eos_i", 26000305,
              'tables/Fe_wk_Thermos.ZEFF', 0, "tables/Fe_wk_Thermos.PLANCK", 0,
              "tables/Fe_wk_Thermos.ROSSELAND", 0, 26.0, 55.845),
    "Gd": ("tables/Gd_eos_e", 64000304, "tables/Gd_eos_i", 64000305,
              'tables/Gd_Thermos.ZEFF', 0, "tables/Gd_Thermos.PLANCK", 0,
              "tables/Gd_Thermos.ROSSELAND", 0, 64, 157.25),
    "Glass": ("tables/Glass_eos_e", 10000304, "tables/Glass_eos_i", 10000305,
              "", -1, "tables/Glass_OPC.PLANCK", 1022,
              "tables/Glass_OPC.ROSS", 1022, 10.0, 20.028),
    "H": ("tables/H_eos_e", 1000304, "tables/H_eos_i", 1000305,
              'tables/H_Thermos.ZEFF', 0, "tables/H_Thermos.PLANCK", 0,
              "tables/H_Thermos.ROSSELAND", 0, 1, 1.008),
    "He": ("tables/He_eos_e", 2000304, "tables/He_eos_i", 2000305,
              'tables/He_Thermos.ZEFF', 0, "tables/He_Thermos.PLANCK", 0,
              "tables/He_Thermos.ROSSELAND", 0, 2, 4.003),
    "H_wk": ("tables/H_wk_eos_e", 1000304, "tables/H_wk_eos_i", 1000305,
              'tables/H_wk_Thermos.ZEFF', 0, "tables/H_wk_Thermos.PLANCK", 0,
              "tables/H_wk_Thermos.ROSSELAND", 0, 1.0, 1.008),
    "Kr": ("tables/Kr_eos_e", 36000304, "tables/Kr_eos_i", 36000305,
              'tables/Kr_Thermos.ZEFF', 0, "tables/Kr_Thermos.PLANCK", 0,
              "tables/Kr_Thermos.ROSSELAND", 0, 36, 83.8),
    "Li": ("tables/Li_eos_e", 3000304, "tables/Li_eos_i", 3000305,
              'tables/Li_Thermos.ZEFF', 0, "tables/Li_Thermos.PLANCK", 0,
              "tables/Li_Thermos.ROSSELAND", 0, 3, 6.939),
    "LiD": ("tables/LiD_eos_e", 2000304, "tables/LiD_eos_i", 2000305,
              "", -1, "tables/LiD_OPC.PLANCK", 1071,
              "tables/LiD_OPC.ROSS", 1071, 2.0, 4.4775),
    "LiH": ("tables/LiH_eos_e", 2000304, "tables/LiH_eos_i", 2000305,
              "", -1, "tables/LiH_OPC.PLANCK", 1071,
              "tables/LiH_OPC.ROSS", 1071, 2.0, 4.0),
    "Mg": ("tables/Mg_eos_e", 12000304, "tables/Mg_eos_i", 12000305,
              'tables/Mg_Thermos.ZEFF', 0, "tables/Mg_Thermos.PLANCK", 0,
              "tables/Mg_Thermos.ROSSELAND", 0, 12, 24.305),
    "Mo": ("tables/Mo_eos_e", 42000304, "tables/Mo_eos_i", 42000305,
              'tables/Mo_Thermos.ZEFF', 0, "tables/Mo_Thermos.PLANCK", 0,
              "tables/Mo_Thermos.ROSSELAND", 0, 42, 95.94),
    "Mylar": ("tables/Mylar_eos_e", 4540304, "tables/Mylar_eos_i", 4540305,
              "", -1, "tables/Mylar_OPC.PLANCK", 1036,
              "tables/Mylar_OPC.ROSS", 1036, 4.545, 8.735),
    "N": ("tables/N_eos_e", 7000304, "tables/N_eos_i", 7000305,
              'tables/N_Thermos.ZEFF', 0, "tables/N_Thermos.PLANCK", 0,
              "tables/N_Thermos.ROSSELAND", 0, 7, 14.007),
    "Ne": ("tables/Ne_eos_e", 10000304, "tables/Ne_eos_i", 10000305,
              'tables/Ne_Thermos.ZEFF', 0, "tables/Ne_Thermos.PLANCK", 0,
              "tables/Ne_Thermos.ROSSELAND", 0, 10, 20.183),
    "Ni": ("tables/Ni_eos_e", 28000304, "tables/Ni_eos_i", 28000305,
              'tables/Ni_Thermos.ZEFF', 0, "tables/Ni_Thermos.PLANCK", 0,
              "tables/Ni_Thermos.ROSSELAND", 0, 28, 58.71),
    "O": ("tables/O_eos_e", 8000304, "tables/O_eos_i", 8000305,
              'tables/O_Thermos.ZEFF', 0, "tables/O_Thermos.PLANCK", 0,
              "tables/O_Thermos.ROSSELAND", 0, 8, 16.0),
    "Parylene": ("tables/Parylene_eos_e", 5500304, "tables/Parylene_eos_i", 5500305,
              "", -1, "tables/Parylene_OPC.PLANCK", 1035,
              "tables/Parylene_OPC.ROSS", 1035, 5.5, 10.815),
    "Pb": ("tables/Pb_eos_e", 82000304, "tables/Pb_eos_i", 82000305,
              'tables/Pb_Thermos.ZEFF', 0, "tables/Pb_Thermos.PLANCK", 0,
              "tables/Pb_Thermos.ROSSELAND", 0, 82, 207.19),
    "Pb_wk": ("tables/Pb_wk_eos_e", 82000304, "tables/Pb_wk_eos_i", 82000305,
              'tables/Pb_wk_Thermos.ZEFF', 0, "tables/Pb_wk_Thermos.PLANCK", 0,
              "tables/Pb_wk_Thermos.ROSSELAND", 0, 82.0, 207.2),
    "PE": ("tables/PE_eos_e", 2670304, "tables/PE_eos_i", 2670305,
              "", -1, "tables/PE_OPC.PLANCK", 1031,
              "tables/PE_OPC.ROSS", 1031, 2.667, 4.676),
    "PS": ("tables/PS_eos_e", 3500304, "tables/PS_eos_i", 3500305,
              "", -1, "tables/PS_OPC.PLANCK", 1032,
              "tables/PS_OPC.ROSS", 1032, 3.5, 6.51),
    "PU": ("tables/PU_eos_e", 3760304, "tables/PU_eos_i", 3760305,
              "", -1, "tables/PU_OPC.PLANCK", 1033,
              "tables/PU_OPC.ROSS", 1033, 3.763, 7.038),
    "Si": ("tables/Si_eos_e", 14000304, "tables/Si_eos_i", 14000305,
              'tables/Si_Thermos.ZEFF', 0, "tables/Si_Thermos.PLANCK", 0,
              "tables/Si_Thermos.ROSSELAND", 0, 14, 28.08),
    "SiO2wk14": ("tables/SiO2wk14_eos_e", 10000304, "tables/SiO2wk14_eos_i", 10000305,
              "", -1, "tables/Quartz_OPC.PLANCK", 1022,
              "tables/Quartz_OPC.ROSS", 1022, 10.0, 20.03),
    "Sn": ("tables/Sn_eos_e", 50000304, "tables/Sn_eos_i", 50000305,
              "", -1, "tables/Sn_OPC.PLANCK", 1401,
              "tables/Sn_OPC.ROSS", 1401, 50.0, 118.7),
    "SS": ("tables/SS_eos_e", 25800304, "tables/SS_eos_i", 25800305,
              "", -1, "tables/SS_OPC.PLANCK", 1181,
              "tables/SS_OPC.ROSS", 1181, 25.8, 55.368),
    "Ta": ("tables/Ta_eos_e", 73000304, "tables/Ta_eos_i", 73000305,
              'tables/Ta_Thermos.ZEFF', 0, "tables/Ta_Thermos.PLANCK", 0,
              "tables/Ta_Thermos.ROSSELAND", 0, 73, 180.95),
    "Ti": ("tables/Ti_eos_e", 22000304, "tables/Ti_eos_i", 22000305,
              'tables/Ti_LTE.ZEFF', 27002000, "tables/Ti_LTE.PLANCK", 27003000,
              "tables/Ti_LTE.ROSS", 27004000, 22., 47.867),
    "U": ("tables/U_eos_e", 92000304, "tables/U_eos_i", 92000305,
              'tables/U_Thermos.ZEFF', 0, "tables/U_Thermos.PLANCK", 0,
              "tables/U_Thermos.ROSSELAND", 0, 92, 238.03),
    "V": ("tables/V_eos_e", 23000304, "tables/V_eos_i", 23000305,
              'tables/V_Thermos.ZEFF', 0, "tables/V_Thermos.PLANCK", 0,
              "tables/V_Thermos.ROSSELAND", 0, 23, 50.942),
    "W": ("tables/W_eos_e", 74000304, "tables/W_eos_i", 74000305,
              'tables/W_Thermos.ZEFF', 0, "tables/W_Thermos.PLANCK", 0,
              "tables/W_Thermos.ROSSELAND", 0, 74, 183.84),
    "WC": ("tables/WC_eos_e", 38750304, "tables/WC_eos_i", 38750305,
              "", -1, "tables/WC_OPC.PLANCK", 1121,
              "tables/WC_OPC.ROSS", 1121, 38.75, 94.191),
    "Xe": ("tables/Xe_eos_e", 54000304, "tables/Xe_eos_i", 54000305,
              'tables/Xe_Thermos.ZEFF', 0, "tables/Xe_Thermos.PLANCK", 0,
              "tables/Xe_Thermos.ROSSELAND", 0, 54, 131.3),
    "Zn": ("tables/Zn_eos_e", 30000304, "tables/Zn_eos_i", 30000305,
              'tables/Zn_Thermos.ZEFF', 0, "tables/Zn_Thermos.PLANCK", 0,
              "tables/Zn_Thermos.ROSSELAND", 0, 30, 65.37),
}

TEMPLATE = """!-----------------------------------------------------------------------------+
!  {name} - Hugoniot validation case (auto-generated {date})
!  Thick planar {mat} slab ({thick} cm, rho0={rho0}), constant {trad} eV radiation
!  bath from the right for {tau} s -> quasi-steady shock wave.
!  dttevar/dttivar=0.5: 每步 Te/Ti 相对变化限幅, 抑制双温交换振荡
!  (2026-08-14 FEOS 表波后 Ti=0 振荡的修复, 见 Hugoniot校验流程.md)
!-----------------------------------------------------------------------------+
&parameters
   igeo        = 1,
   xmin        = 0.,
   texit       = {texit},
   nfuel       = 0,
   iright      = 0,
   ileft       = 0,
   alphal      = 0.,
   alphar      = 0.,
   betal       = 0.,
   betar       = 1.,
   itype       = 2,
   tau         = {tau},
   trad        = {trad},
   iradia      = 1,
   ihydro      = 1,
   iheation    = 0,
   model       = 0,
   fheat       = 8.0,
   fei         = 2.0,
   flaser      = 26.0,
   zmin        = 0.1,
   flf         = 0.1,
   inegpre     = {inegpre},
   nsplit      = 5,
   dtmin       = 0,
   dtmax       = 1e-11,
   dtinit      = 1e-11,
   dtrvar      = 0.9,
   dttevar     = 0.5,
   dttivar     = 0.5,
   dtbreak     = 2.,
   dtfactor    = 2.,
   nexit       = 100000,
   iwctrl      = 1,
   dt_aout     = 1000000.,
   ns_aout     = 1000000,
   dt_bout     = {dt_bout},
   ns_bout     = 1000000,
   irad_left   = 1,
   irad_right  = {nif},
   nreduce     = 1,
   iquiet      = 1,
   tquiet      = 0.05,
/
&layer
   nc          = {nc},
   thick       = {thick},
   r0          = {rho0},
   te0         = 0.03,
   ti0         = 0.03,
   zonpar      = 1.0,
   material    = '{mat}',
/
&material
   name        = '{mat}',
   zi          = {zi},
   ai          = {ai},
   eeos_id     = {eeos_id},
   eeos_file   = '{eeos_file}',
   ieos_id     = {ieos_id},
   ieos_file   = '{ieos_file}',
   z_id        = {z_id},
   z_file      = '{z_file}',
   planck_id   = {planck_id},
   planck_file = '{planck_file}',
   ross_id     = {ross_id},
   ross_file   = '{ross_file}',
   eps_id      = -1,
/
"""


def main():
    mat, rho0, thick = sys.argv[1], sys.argv[2], sys.argv[3]
    trads = [float(x) for x in sys.argv[4].split(",")]
    cfg = MAT_TABLES[mat]
    (eeos_f, eeos_id, ieos_f, ieos_id, z_f, z_id,
     p_f, p_id, r_f, r_id, zi, ai) = cfg
    thick_f = float(thick)
    nc = 800            # 0.125 um/单元 @ thick=1e-2 cm, 保证波后平台与波前过渡分辨
    nrec = 400          # 输出记录数: 轨迹拟合需要密集时间采样
    # 时间尺度估计: Us ~ 5e5-1e6 cm/s, 穿 70% 厚度
    texit = 0.7 * thick_f / 5e5
    tau = texit * 3
    dt_bout = texit / nrec
    for trad in trads:
        # 产物一律收进 validation_cases/<材料>/hugoniot_T*（与 Check 同目录，
        # 勿再放根目录 —— 2026-08-18 CHHub 二次犯同错后修正）
        name = f"hugoniot_T{int(trad)}"
        d = f"{CASES}/{mat}/{name}"
        os.makedirs(d, exist_ok=True)
        with open(f"{d}/data.in", "w") as f:
            f.write(TEMPLATE.format(
                name=name, date="2026-08-11", mat=mat, thick=thick, rho0=rho0,
                trad=trad, tau=f"{tau:.3e}", texit=f"{texit:.3e}",
                dt_bout=f"{dt_bout:.3e}", nc=nc, nif=nc + 1,
                zi=zi, ai=ai, eeos_id=eeos_id, eeos_file=eeos_f,
                ieos_id=ieos_id, ieos_file=ieos_f, z_id=z_id, z_file=z_f,
                planck_id=p_id, planck_file=p_f, ross_id=r_id, ross_file=r_f,
                inegpre=MAT_INEGPRE.get(mat, 0)))
        for s in ["RUN", "CLEAR"]:
            src = f"{CASES}/Ti/TiCheck/{s}"
            dst = f"{d}/{s}"
            with open(src) as f1, open(dst, "w") as f2:
                f2.write(f1.read())
            os.chmod(dst, 0o755)
        with open(f"{d}/FILELIST", "w") as f:
            f.write("FILELIST\ndata.in\nRUN\nCLEAR\n*.png\n")
        print(f"已创建 {name} (trad={trad} eV, texit={texit:.2e} s)")


if __name__ == "__main__":
    main()
