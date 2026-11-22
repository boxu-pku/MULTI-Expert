# MULTI-Expert 路径变量约定（本机对照）
# skill 文本中的 $MULTI_ROOT/$MULTI_LIBS/$MULTI_APP 在此还原为本机实际路径。
# 用法：source multi_env.sh

export MULTI_ROOT="${MULTI_ROOT:-/home/ubuntu/local/MULTI-2D.2026.3}"
export MULTI_LIBS="${MULTI_LIBS:-/home/ubuntu/local}"
export MULTI_APP="${MULTI_APP:-/home/ubuntu/myapp}"

# 运行算例所需环境（铁律 5）
export MULTI="$MULTI_ROOT"
export PATH="$MULTI_ROOT/r94/boot-3.2:$PATH"
