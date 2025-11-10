#!/usr/bin/env bash
# uninstall.sh - 卸载 ClaudeCodeManager
# 使用方法: bash uninstall.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[卸载] ClaudeCodeManager${NC}"
echo ""

# 检查全局命令是否存在
LAUNCHER_PATH="$HOME/.local/bin/claude_env"

if [ -f "$LAUNCHER_PATH" ]; then
    echo -e "${YELLOW}[删除] 全局命令 'claude_env'...${NC}"
    rm -f "$LAUNCHER_PATH"
    echo "✓ 已删除: $LAUNCHER_PATH"
else
    echo -e "${YELLOW}全局命令未找到，跳过${NC}"
fi

# 询问是否删除环境数据
echo ""
echo -e "${YELLOW}注意: 环境数据位于 ~/.claude_env${NC}"
echo "这包含您所有保存的 Claude Code 环境配置"
echo ""
read -p "是否删除所有环境数据? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "$HOME/.claude_env" ]; then
        echo -e "${YELLOW}[删除] 环境数据 ~/.claude_env...${NC}"
        rm -rf "$HOME/.claude_env"
        echo "✓ 已删除所有环境数据"
    else
        echo "环境数据目录不存在，跳过"
    fi
else
    echo "保留环境数据"
fi

# 完成
echo ""
echo -e "${GREEN}✓ 卸载完成!${NC}"
echo ""
echo "项目源代码仍保留在:"
echo "  $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo ""
echo "如需完全删除，请手动删除该目录"
echo ""
