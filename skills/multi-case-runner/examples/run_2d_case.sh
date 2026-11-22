#!/bin/bash
# run_2d_case.sh — 跑 2D 算例的完整示例（环境 + RUN + 后台观察）
# 用法: bash run_2d_case.sh <算例目录>
# 例:  bash run_2d_case.sh /home/ubuntu/local/MULTI-2D.2026.3/cases/M2D_Radia_110
#
# ⚠ 2D 算例时长分钟~小时级，本轮未逐一实测（agent/ARCHITECTURE.md §10）。
#    建议后台运行 + 定期 tail output 观察，不要前台死等。
set -u
export MULTI=/home/ubuntu/local/MULTI-2D.2026.3
export PATH=$PATH:$MULTI/r94/boot-3.2:.

CASE="${1:?用法: bash run_2d_case.sh <算例目录>}"
cd "$CASE" || exit 1
[ -f User.r ] || { echo "!! 无 User.r —— 这不是 2D 算例目录"; exit 1; }

# ktag 残留检查
if [ -f ktag ]; then
    if ps aux | grep -E 'multi|a\.out' | grep -v grep > /dev/null; then
        echo "!! 算例正在运行中"; exit 1
    fi
    echo "清理异常残留 ktag"; rm -f ktag
fi

./RUN     # 内部: x.2.library && x.2.build multi(或 multi2d) && nohup sh proceso &

sleep 5
if [ -f ktag ]; then
    echo "已后台启动。观察方法:"
    echo "  tail -f $CASE/output      # 步进日志"
    echo "  ls $CASE/ktag             # 存在=仍在跑"
    echo "  ls -ltr $CASE | tail      # 快照文件（<t> 与 <t>.d）"
    echo "结束后: 快照用 mpp22 查看（需 X11: $MULTI/R94）"
else
    echo "!! 启动后 ktag 立即消失——可能编译失败，查看 output:"
    tail -20 output
fi
