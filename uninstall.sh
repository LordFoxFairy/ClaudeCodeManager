#!/usr/bin/env bash
# uninstall.sh - 卸载 ClaudeCodeManager
# 使用方法: bash uninstall.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}[卸载] ClaudeCodeManager${NC}"
echo ""

# 检查 claude_env 命令是否可用
if command -v claude_env &> /dev/null; then
    echo "使用 claude_env uninstall 命令进行卸载..."
    echo ""
    claude_env uninstall
elif [ -f "$HOME/.local/bin/claude_env" ]; then
    # 如果命令不在 PATH 中但文件存在，直接调用
    echo "使用 claude_env uninstall 命令进行卸载..."
    echo ""
    "$HOME/.local/bin/claude_env" uninstall
else
    # 如果命令不存在，使用 Python 直接运行
    echo "claude_env 命令未安装，使用 Python 直接运行卸载..."
    echo ""

    # 检查是否在项目目录中
    if [ -f "$SCRIPT_DIR/claude_env/__main__.py" ]; then
        cd "$SCRIPT_DIR"

        # 优先使用 uv，如果不存在则使用 python
        if command -v uv &> /dev/null; then
            uv run python -m claude_env uninstall
        else
            python -m claude_env uninstall
        fi
    else
        echo -e "${RED}错误: 找不到 claude_env 模块${NC}"
        echo "请在项目目录中运行此脚本"
        exit 1
    fi
fi
