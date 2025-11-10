#!/usr/bin/env python3
"""
claude_env_launcher.py - 启动器脚本
直接调用 CLI，让 typer 显示正确的命令名
"""
import sys
import os

# 将项目目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_env.cli import app

if __name__ == "__main__":
    # 设置程序名为 claude_env
    sys.argv[0] = "claude_env"
    app()