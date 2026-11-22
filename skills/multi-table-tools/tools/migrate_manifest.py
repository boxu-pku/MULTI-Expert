# -*- coding: utf-8 -*-
"""
migrate_manifest.py — 材料批量迁移清单

每条记录:
  name     材料名(用于目录/文件名, 如 'Pb', 'SiO2', 'LiD')
  A, Z     有效原子量/原子序(来自 hyades EOS.list)
  rho0     参考密度 g/cm3 (EOS.list)
  eos      EOS 数据源: ('hyades', 文件号) / ('celia', 文件名) / ('mpqeos', 2026.3已有文件)
  opa      不透明度源: ('thermos', 符号) / ('celia', 前缀) / None
  batch    'full' = 全套(1D 验证) / 'eos_only' = 仅 EOS(2D 登记)
"""

HYADES = "/home/ubuntu/local/newmulti/Multi_BACK/matter++/hyades/sesame"
CELIA = "/home/ubuntu/local/newmulti/Multi_BACK/matter++/mat_CELIA"
THERMOS = "/home/ubuntu/local/newmulti/Multi_BACK/matter++/Thermos"
MPQ = "/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_2019"
MPQ2 = "/home/ubuntu/local/MULTI-2D.2026.3/r94/mat_Si-1.0"

# ---------- 批次 1: 元素, hyades EOS + Thermos 不透明度(Planck/Rosseland/Zeff) ----------
BATCH_FULL = [
    # name,    A,       Z,   rho0,     eos_file,       thermos符号
    ("H",  1.008,   1,  0.0884, f"{HYADES}/eos_61.dat",  "H"),
    ("He", 4.003,   2,  0.4,    f"{HYADES}/eos_191.dat", "He"),
    ("Li", 6.939,   3,  0.5326, f"{HYADES}/eos_71.dat",  "Li"),
    ("N",  14.007,  7,  0.8572, f"{HYADES}/eos_251.dat", "N"),
    ("O",  16.000,  8,  1.2620, f"{HYADES}/eos_221.dat", "O"),
    ("Ne", 20.183, 10,  1.44,   f"{HYADES}/eos_101.dat", "Ne"),
    ("Mg", 24.305, 12, 1.740,   f"{HYADES}/eos_451.dat", "Mg"),
    ("Si", 28.08,  14,  2.42,   f"{MPQ2}/SI.INV",       "Si"),
    ("Ar", 39.948, 18,  1.4,    f"{HYADES}/eos_91.dat",  "Ar"),
    ("V",  50.942, 23,  6.11,   f"{HYADES}/eos_521.dat", "V"),
    ("Ni", 58.71,  28,  8.882,  f"{HYADES}/eos_291.dat", "Ni"),
    ("Zn", 65.37,  30,  7.139,  f"{HYADES}/eos_531.dat", "Zn"),
    ("Kr", 83.80,  36,  2.5005, f"{HYADES}/eos_201.dat", "Kr"),
    ("Mo", 95.94,  42, 10.2,    f"{HYADES}/eos_281.dat", "Mo"),
    ("Ag", 107.87, 47, 10.50,   f"{HYADES}/eos_491.dat", "Ag"),
    ("Xe", 131.30, 54,  3.0551, f"{HYADES}/eos_371.dat", "Xe"),
    ("Gd", 157.25, 64,  7.898,  f"{HYADES}/eos_471.dat", "Gd"),
    ("Ta", 180.95, 73, 16.654,  f"{HYADES}/eos_271.dat", "Ta"),
    ("Pb", 207.19, 82, 11.34,   f"{HYADES}/eos_231.dat", "Pb"),
    ("U",  238.03, 92, 18.983,  f"{HYADES}/eos_131.dat", "U"),
    # 2026.3 已有 2D EOS, 补 1D 表(拆分总表 + Thermos 不透明度)
    ("Fe", 55.845, 26, 7.874,   f"{MPQ}/Fe_MPQEOS.i301", "Fe"),
    ("Cu", 63.546, 29, 8.96,    f"{MPQ}/Cu_MPQEOS.i301", "Cu"),
    ("W",  183.84, 74, 19.25,   f"{MPQ}/W_MPQEOS.i301",  "W"),
]

# ---------- 批次 1b: CELIA 直读 (DD, D, CH) ----------
BATCH_CELIA = [
    # name, A, Z, rho0, eos文件, 不透明度前缀, zeff文件
    ("DD", 4.028, 2, 0.353,  f"{CELIA}/DD_ieos", "D_20G", "D.ZEFF"),
    ("D",  2.014, 1, 0.1766, f"{HYADES}/eos_151.dat", "D_20G", "D.ZEFF"),
    ("CH", 6.510, 3.5, 1.044, f"{CELIA}/CH_ieos", "C_20G", "C.ZEFF"),
]

# ---------- 批次 2: 仅 EOS (2D 登记, 无干净不透明度源) ----------
BATCH_EOS_ONLY = [
    # name, A, Z, rho0, eos_file
    ("Glass",  20.028, 10.0, 2.65,   f"{HYADES}/eos_21.dat"),
    ("Quartz", 20.028, 10.0, 2.204,  f"{HYADES}/eos_23.dat"),
    ("Silica", 20.028, 10.0, 2.65,   f"{HYADES}/eos_24.dat"),
    ("Al2O3",  20.392, 10.0, 3.97,   f"{HYADES}/eos_162.dat"),
    ("WC",     94.191, 38.75, 14.97, f"{HYADES}/eos_141.dat"),
    ("CD2",    5.347,  2.667, 1.0475, f"{HYADES}/eos_171.dat"),
    ("LiD",    4.4775, 2.0,  0.883,  f"{HYADES}/eos_213.dat"),
    ("LiH",    4.000,  2.0,  0.775,  f"{HYADES}/eos_241.dat"),
    ("Pt",     195.09, 78.0, 21.419, f"{HYADES}/eos_261.dat"),
    ("Diamond",12.011, 6.0,  3.51,   f"{HYADES}/eos_341.dat"),
    ("Cliquid",12.011, 6.0,  3.688,  f"{HYADES}/eos_342.dat"),
    ("Cphenolic",9.010, 4.648, 1.4503, f"{HYADES}/eos_343.dat"),
    ("SS",     55.368, 25.8, 7.91,   f"{HYADES}/eos_362.dat"),
    ("Sn",     118.7,  50.0, 7.29,   f"{HYADES}/eos_401.dat"),
    ("C8H7Br", 11.441, 5.625, 1.53,  f"{HYADES}/eos_431.dat"),
    ("BeO",    12.505, 6.0,  3.008,  f"{HYADES}/eos_441.dat"),
    ("Teflon", 16.669, 8.0,  2.152,  f"{HYADES}/eos_321.dat"),
    ("HE",     11.04,  5.626, 1.840, f"{HYADES}/eos_331.dat"),
    ("PBX9502",10.98,  5.598, 1.894, f"{HYADES}/eos_332.dat"),
    ("Epoxy",  5.9134, 3.2407, 1.185, f"{HYADES}/eos_502.dat"),
    ("Lucite", 6.674,  3.6,  1.186,  f"{HYADES}/eos_34.dat"),
    ("PVA",    6.782,  3.645, 1.264, f"{HYADES}/eos_37.dat"),
    ("PE",     4.676,  2.667, 0.954, f"{HYADES}/eos_31.dat"),
    ("PS",     6.510,  3.5,  1.044,  f"{HYADES}/eos_32.dat"),
    ("PU",     7.038,  3.763, 1.265, f"{HYADES}/eos_33.dat"),
    ("Parylene",10.815, 5.5, 1.42,   f"{HYADES}/eos_35.dat"),
    ("Mylar",  8.735,  4.545, 1.38,  f"{HYADES}/eos_36.dat"),
    ("Water",  6.005,  3.333, 0.9982, f"{HYADES}/eos_311.dat"),
    ("Air",    14.803, 7.373, 0.00129, f"{HYADES}/eos_301.dat"),
    ("Eu",     151.96, 63.0, 5.253,  f"{HYADES}/eos_461.dat"),
]
