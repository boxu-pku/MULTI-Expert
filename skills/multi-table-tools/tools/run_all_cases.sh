#!/bin/bash
# run_all_cases.sh — 批量运行全部材料验证算例并生成可视化
set -u
export MULTI=/home/ubuntu/local/MULTI-2D.2026.3
export PATH=$PATH:$MULTI/r94/boot-3.2:.
TOOLS=$MULTI/work/eos_opacity_tools

for d in $MULTI/validation_cases/*Check; do
    name=$(basename "$d")
    [ "$name" == "TiCheck" ] && continue   # Ti 已验收
    echo "===== $name ====="
    cd "$d" || continue
    rm -f ktag
    if [ ! -f multi ]; then
        ./RUN > /dev/null 2>&1
    else
        rm -f fort.10 fort.11 fort.12 block multidata.mod output cputime
        ./RUN > /dev/null 2>&1
    fi
    # 等待结束(ktag 消失)
    for i in $(seq 1 60); do
        [ ! -f ktag ] && break
        sleep 2
    done
    if [ -f ktag ]; then
        echo "  超时仍在运行, 跳过绘图"
        continue
    fi
    if grep -q "normal program termination" output; then
        err=$(grep "relative error in energy" output | grep -oE "[0-9.E+-]+" | tail -1)
        echo "  完成, 能量误差: $err"
        python3 $TOOLS/plot_1d_validation.py "$d" 2>/dev/null | grep "已生成" -A2 | tail -2
    else
        echo "  !! 未正常结束"
        tail -5 output 2>/dev/null
    fi
done
echo "===== 全部完成 ====="
