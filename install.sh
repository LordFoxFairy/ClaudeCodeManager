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

# 使用 uv 运行 launcher
exec uv run python claude_env_launcher.py "\$@"
EOF

chmod +x "$LAUNCHER_PATH"

# 检查和配置 PATH
echo -e "${YELLOW}[检查] PATH 配置...${NC}"

# 定义 PATH 导出行
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'

# 检测 shell 配置文件
SHELL_NAME=$(basename "$SHELL")
CONFIG_FILES=()

# 根据不同 shell 添加配置文件
if [ "$SHELL_NAME" = "zsh" ]; then
    CONFIG_FILES+=("$HOME/.zshrc")
elif [ "$SHELL_NAME" = "bash" ]; then
    CONFIG_FILES+=("$HOME/.bashrc" "$HOME/.bash_profile")
fi

# 添加通用配置文件
CONFIG_FILES+=("$HOME/.profile")

# 标记是否已配置
PATH_CONFIGURED=false

# 检查并添加 PATH 到配置文件
for config_file in "${CONFIG_FILES[@]}"; do
    if [ -f "$config_file" ]; then
        # 检查是否已有 PATH 配置
        if ! grep -q "$HOME/.local/bin" "$config_file" 2>/dev/null; then
            echo "  添加 PATH 到 $config_file"
            echo "" >> "$config_file"
            echo "# Added by ClaudeCodeManager" >> "$config_file"
            echo "$PATH_LINE" >> "$config_file"
            PATH_CONFIGURED=true
        else
            echo "  $config_file 已配置 PATH"
            PATH_CONFIGURED=true
        fi
    fi
done

# 如果没有找到配置文件，创建一个
if [ "$PATH_CONFIGURED" = false ]; then
    if [ "$SHELL_NAME" = "zsh" ]; then
        echo "  创建 ~/.zshrc 并添加 PATH"
        echo "# Added by ClaudeCodeManager" >> "$HOME/.zshrc"
        echo "$PATH_LINE" >> "$HOME/.zshrc"
        PATH_CONFIGURED=true
    elif [ "$SHELL_NAME" = "bash" ]; then
        echo "  创建 ~/.bashrc 并添加 PATH"
        echo "# Added by ClaudeCodeManager" >> "$HOME/.bashrc"
        echo "$PATH_LINE" >> "$HOME/.bashrc"
        PATH_CONFIGURED=true
    fi
fi

# 立即导出 PATH 到当前会话
export PATH="$HOME/.local/bin:$PATH"

if [ "$PATH_CONFIGURED" = true ]; then
    echo -e "${GREEN}✓ PATH 已自动配置${NC}"
else
    echo -e "${YELLOW}警告: 无法自动配置 PATH${NC}"
    echo "请手动添加到 shell 配置文件:"
    echo ""
    echo "  $PATH_LINE"
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
