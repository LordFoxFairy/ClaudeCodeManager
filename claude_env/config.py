#!/usr/bin/env python3
# claude_env/config.py
# 描述: 负责加载和保存 YAML 配置文件，并使用 Pydantic 模型进行验证

import os
import sys
import yaml
from claude_env.models import AppConfig, EnvState, CONFIG_ROOT_DIR

# --- 确保 PyYAML 已安装 ---
try:
    import yaml
except ImportError:
    print("错误: 未找到 PyYAML 库。", file=sys.stderr)
    print("请先安装: pip install pyyaml", file=sys.stderr)
    exit(1)

# --- 配置文件路径 ---
CONFIG_PATH = CONFIG_ROOT_DIR / "config.yaml"
ENV_STATE_PATH = CONFIG_ROOT_DIR / "env.yaml"


def load_config() -> AppConfig:
    """
    加载 config.yaml。如果不存在，则创建并返回默认配置。
    """
    os.makedirs(CONFIG_ROOT_DIR, exist_ok=True)
    if not CONFIG_PATH.is_file():
        print(f"未找到配置文件，正在创建默认配置: {CONFIG_PATH}")
        config = AppConfig()  # 从模型创建默认实例
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config.model_dump(mode="json"), f)
        return config

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        # 使用 Pydantic 模型进行验证
        return AppConfig(**config_data)
    except Exception as e:
        print(f"加载 config.yaml 出错: {e}。将使用默认配置。")
        return AppConfig()


def load_env_state() -> EnvState:
    """
    加载 env.yaml。如果不存在，则创建并返回默认状态。
    """
    os.makedirs(CONFIG_ROOT_DIR, exist_ok=True)
    if not ENV_STATE_PATH.is_file():
        print(f"未找到环境状态文件，正在创建: {ENV_STATE_PATH}")
        state = EnvState()  # 默认实例
        save_env_state(state)
        return state

    try:
        with open(ENV_STATE_PATH, "r", encoding="utf-8") as f:
            state_data = yaml.safe_load(f)
        return EnvState(**state_data)
    except Exception as e:
        print(f"加载 env.yaml 出错: {e}。将使用默认状态。")
        return EnvState()


def save_env_state(state: EnvState):
    """
    将 EnvState Pydantic 模型实例保存回 env.yaml
    """
    os.makedirs(CONFIG_ROOT_DIR, exist_ok=True)
    with open(ENV_STATE_PATH, "w", encoding="utf-8") as f:
        # Pydantic 的 .model_dump() 确保了数据是可序列化的
        yaml.dump(state.model_dump(), f, default_flow_style=False)
