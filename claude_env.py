#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# claude_env.py - 主程序入口
# -----------------------------------------------------------------------------
# 描述:
#   这是 Claude 环境管理器 (claude_env) 的主执行文件。
#   它唯一的职责就是导入并运行 claude_env/cli.py 中定义的 typer 应用。
#
# 用法:
#   python claude_env.py --help
#   python claude_env.py list
#   python claude_env.py add <env_name>
#   python claude_env.py switch <env_name>
# -----------------------------------------------------------------------------

import sys
import os

# 将 claude_env 包目录添加到 Python 路径中
# 这允许我们从包（如 claude_env.cli）中导入
sys.path.insert(0, os.path.dirname(__file__))

try:
    from claude_env.cli import app
except ImportError as e:
    print(f"错误: 导入 claude_env 包失败: {e}", file=sys.stderr)
    print("请确保 claude_env 目录与此文件位于同一级别。", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    # Typer 将从此
    app()
