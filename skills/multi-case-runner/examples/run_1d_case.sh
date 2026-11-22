#!/bin/bash
# run_1d_case.sh — 跑 1D 算例的完整示例（环境 + RUN + 等待 + 判读）
# 用法: bash run_1d_case.sh <算例目录>
# 例:  bash run_1d_case.sh /home/ubuntu/local/MULTI-2D.2026.3/validation_cases/TiCheck
set -u
export MULTI=/home/ubuntu/local/MULTI-2D.2026.3
export PATH=$PATH:$MULTI/r94/boot-3.2:.

CASE="${1:?用法: bash run_1d_case.sh <算例目录>}"
cd "$CASE" || exit 1
[ -f data.in ] || { echo "!! 无 data.in —— 这不是 1D 算例目录"; exit 1; }

# ktag 残留检查
if [ -f ktag ]; then
    if ps aux | grep -E 'multi|a\.out' | grep -v grep > /dev/null; then
        echo "!! 算例正在运行中（ktag + 进程都在），等待或稍后重试"; exit 1
    fi
    echo "清理异常残留 ktag"; rm -f ktag
fi

./RUN

# 等待结束（ktag 消失）；1D 验证算例秒级，官方算例分钟级
for i in $(seq 1 150); do
    [ ! -f ktag ] && break
    sleep 2
done
if [ -f ktag ]; then
    echo "!! 超过 5 分钟仍在运行（大算例正常），用 tail -f $CASE/output 观察"
    exit 2
fi

# 判读（材料迁移验证规范 §B 口径）
echo "===== 判读 ====="
if grep -q "normal program termination" output; then
    echo "B1 正常终止: PASS"
    grep "relative error in energy" output | tail -1
    grep -iE "ERROR|STOP|premature eof" output && echo "B6 有异常字样: FAIL" || echo "B6 无异常字样: PASS"
    echo "产物: $(ls fort.10 fort.11 2>/dev/null | tr '\n' ' ')"
    echo "下一步（出图）: python3 $MULTI/work/eos_opacity_tools/plot_1d_validation.py $CASE"
else
    echo "B1 正常终止: FAIL —— output 尾部:"
    tail -15 output
fi
