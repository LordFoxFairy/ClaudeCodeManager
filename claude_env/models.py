#!/usr/bin/env python3
# claude_env/models.py
# 描述: 定义所有 Pydantic 数据模型

from pydantic import BaseModel, Field
from typing import List, Optional
from pathlib import Path

# --- 路径常量 ---
HOME_DIR = Path.home()
# 新的配置根目录, 替换 ~/.claude_manager
CONFIG_ROOT_DIR = HOME_DIR / ".claude_env"


# --- 模型定义 ---


class AppConfig(BaseModel):
    """
    定义 config.yaml 的结构
    使用 Pydantic 的 Field 来提供默认值
    """

    base_dir: Path = Field(default=CONFIG_ROOT_DIR)
    claude_json_path: Path = Field(default=HOME_DIR / ".claude.json")
    claude_dir_path: Path = Field(default=HOME_DIR / ".claude")
    managed_paths: List[str] = Field(
        default_factory=lambda: [
            ".claude.json",  # OAuth token 或 API Key 配置
            ".claude",  # Claude Code 相关配置目录
        ]
    )


class EnvState(BaseModel):
    """
    定义 env.yaml 的结构
    """

    active_env: Optional[str] = None
    last_active_env: Optional[str] = None  # 记录上次激活的环境（用于自动保存）
    environments: List[str] = Field(default_factory=list)
