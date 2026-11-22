#!/bin/bash
#===============================================================
# fix_multi_file.sh — 修复 Windows 版 MULTI 数据文件的常见问题
#
#   1. CRLF 行尾 → LF（MULTI-2D 的 C 解析器遇 \r 会报
#      "head line size != 60"）
#   2. Windows MSVC 的 -inf 输出 "-1.#INF000e+000" → MULTI 标准
#      的 "           -INF"（MULTI 读入时映射为 log 值 -40）
#
# 用法:
#   ./fix_multi_file.sh <文件> [文件2 ...]     # 原地修复(先备份 .bak)
#   ./fix_multi_file.sh -d <目录>              # 修复目录下所有文件
#
# 2026-08: 为 MULTI-2D.2026.3 材料迁移整理
#===============================================================
set -e

fix_one() {
    f="$1"
    [ -f "$f" ] || { echo "跳过(不存在): $f"; return; }
    # 已是纯 LF 且无 -inf 的文件不动
    if ! grep -q $'\r' "$f" && ! grep -q '#INF' "$f"; then
        echo "无需修复: $f"
        return
    fi
    cp -n "$f" "$f.bak"
    sed -i 's/\r$//' "$f"
    sed -i 's/-1\.#INF000e+000/           -INF/g' "$f"
    sed -i 's/-1\.\#INF[0-9.e+]*/           -INF/g' "$f"
    echo "已修复: $f (备份: $f.bak)"
}

if [ "$1" == "-d" ]; then
    find "$2" -type f | while read -r f; do fix_one "$f"; done
else
    for f in "$@"; do fix_one "$f"; done
fi
