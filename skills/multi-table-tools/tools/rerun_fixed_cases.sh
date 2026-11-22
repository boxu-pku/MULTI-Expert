#!/bin/bash
# rerun_fixed_cases.sh — 重跑 ×1000 修复涉及的 41 个 Check 算例（2026-08-13）
# 判读: B1 normal program termination / B2 能量相对误差
R=/home/ubuntu/local/MULTI-2D.2026.3
export MULTI=$R
export PATH=$R/r94/boot-3.2:$PATH:.

CASES="H He Li N O Ne Mg Ar V Ni Zn Kr Mo Ag Xe Gd Ta Pb U D Glass Quartz Silica Al2O3 WC CD2 LiD LiH Diamond Cliquid Cphenolic SS Sn PE PS PU Parylene Mylar Water Air Eu"

printf "%-12s %-6s %-12s %-8s\n" case B1 error steps
for m in $CASES; do
  d="$R/validation_cases/$m/${m}Check"
  [ -d "$d" ] || { printf "%-12s MISSING\n" "$m"; continue; }
  cd "$d" || continue
  rm -f ktag
  ./RUN > /dev/null 2>&1
  # 等待完成（ktag 消失），超时 300 s
  t=0
  while [ -f ktag ] && [ $t -lt 300 ]; do sleep 2; t=$((t+2)); done
  b1=$(grep -c "normal program termination" output 2>/dev/null)
  err=$(grep "relative error in energy" output 2>/dev/null | tail -1 | sed 's/.*= *//;s/ .*//')
  steps=$(grep -cE "^ +[0-9]+ +0\." output 2>/dev/null)
  timeout_flag=""; [ -f ktag ] && timeout_flag="TIMEOUT"
  printf "%-12s %-6s %-12s %-8s %s\n" "$m" "$b1" "$err" "$steps" "$timeout_flag"
done
