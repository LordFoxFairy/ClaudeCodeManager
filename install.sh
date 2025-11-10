#!/usr/bin/env bash
# install.sh - 全局安装 ClaudeCodeManager
# 使用方法: bash install.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检测脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${GREEN}[安装] ClaudeCodeManager${NC}"
echo "项目路径: $SCRIPT_DIR"

# 检查 Python 版本
echo -e "${YELLOW}[检查] Python 版本...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "检测到 Python: $PYTHON_VERSION"

# 检查 uv 是否安装
echo -e "${YELLOW}[检查] uv 包管理器...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv 未安装, 正在安装...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# 同步依赖
echo -e "${YELLOW}[安装] 依赖包...${NC}"
cd "$SCRIPT_DIR"
uv sync

# 创建全局命令链接
echo -e "${YELLOW}[创建] 全局命令 'claude_env'...${NC}"

# 创建启动脚本
LAUNCHER_PATH="$HOME/.local/bin/claude_env"
mkdir -p "$HOME/.local/bin"

cat > "$LAUNCHER_PATH" <<EOF
#!/usr/bin/env bash
# ClaudeCodeManager 全局启动器
# 自动生成于: $(date)

INSTALL_DIR="$SCRIPT_DIR"
cd "\$INSTALL_DIR"

# 使用 uv 运行
exec uv run python -m claude_env.cli "\$@"
EOF

chmod +x "$LAUNCHER_PATH"

# 检查 PATH
echo -e "${YELLOW}[检查] PATH 配置...${NC}"
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}警告: $HOME/.local/bin 不在 PATH 中${NC}"
    echo "请在您的 shell 配置文件中添加:"
    echo ""
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "例如 ~/.zshrc 或 ~/.bashrc"
    echo ""
fi

# 完成
echo ""
echo -e "${GREEN}✓ 安装完成!${NC}"
echo ""
echo "现在可以直接使用以下命令:"
echo ""
echo -e "  ${GREEN}claude_env init${NC}        # 初始化管理器"
echo -e "  ${GREEN}claude_env add <name>${NC}  # 添加新环境"
echo -e "  ${GREEN}claude_env switch <name>${NC} # 切换环境"
echo -e "  ${GREEN}claude_env list${NC}        # 列出所有环境"
echo -e "  ${GREEN}claude_env status${NC}      # 查看当前状态"
echo -e "  ${GREEN}claude_env --help${NC}      # 查看所有命令"
echo ""

# 提示重新加载 shell
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}注意: 请重新加载 shell 配置或运行:${NC}"
    echo "  source ~/.zshrc  # 或 source ~/.bashrc"
    echo ""
fi
