#!/usr/bin/env python3
# claude_env/utils.py
# 描述: 提供通用的文件操作和辅助工具 (已更新为使用 pathlib.Path)

import os
import json
import shutil
from pathlib import Path
from typing import Optional

# 注意：这个文件不再需要 config_loader 或 models，它只接收 Path 对象


def get_current_email(claude_json_path: Path) -> Optional[str]:
    """
    尝试从 .claude.json 文件中读取当前登录的 email 或 userID
    """
    if not claude_json_path.is_file():
        return None
    try:
        with open(claude_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 先尝试传统的 user.email 格式
        email = data.get("user", {}).get("email")
        if email:
            return email

        # Claude Code 使用 userID 字段
        user_id = data.get("userID")
        if user_id:
            return f"User: {user_id[:12]}..."  # 显示前12位

        return None
    except Exception as e:
        print(f"读取 {claude_json_path} 出错: {e}")
        return None


def get_auth_type(claude_json_path: Path) -> str:
    """
    检测认证类型：OAuth 或 API Key
    返回: "OAuth", "API Key", 或 "Unknown"
    """
    if not claude_json_path.is_file():
        return "Unknown"
    try:
        with open(claude_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 检查是否存在 API Key 相关字段
        if "apiKey" in data or "api_key" in data:
            return "API Key"
        # 检查是否存在 OAuth token 或 userID (Claude Code 格式)
        elif (
            "token" in data
            or "accessToken" in data
            or "user" in data
            or "userID" in data
        ):
            return "OAuth"
        else:
            return "Unknown"
    except Exception:
        return "Unknown"


def is_auth_valid(claude_json_path: Path) -> bool:
    """
    检查认证是否有效（环境是否真正可用）
    返回: True 表示可用，False 表示需要登录/配置
    """
    if not claude_json_path.is_file():
        return False

    try:
        with open(claude_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        auth_type = get_auth_type(claude_json_path)

        if auth_type == "OAuth":
            # OAuth: 检查是否有 userID 或 token
            has_user_id = bool(data.get("userID"))
            has_token = bool(data.get("token") or data.get("accessToken"))
            has_user = bool(data.get("user", {}).get("email"))
            return has_user_id or has_token or has_user

        elif auth_type == "API Key":
            # API Key: 必须同时有 apiKey 和 endpoint
            has_api_key = bool(data.get("apiKey") or data.get("api_key"))
            has_endpoint = bool(
                data.get("apiEndpoint")
                or data.get("api_endpoint")
                or data.get("endpoint")
            )
            return has_api_key and has_endpoint

        else:
            return False

    except Exception:
        return False


def get_api_endpoint(claude_json_path: Path) -> Optional[str]:
    """
    获取 API endpoint（用于镜像站）
    返回: endpoint URL 或 None
    """
    if not claude_json_path.is_file():
        return None
    try:
        with open(claude_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 检查常见的 endpoint 字段
        endpoint = (
            data.get("apiEndpoint") or data.get("api_endpoint") or data.get("endpoint")
        )
        return endpoint
    except Exception:
        return None


def safe_copy_file(src: Path, dest: Path):
    """
    安全地复制文件
    """
    try:
        os.makedirs(dest.parent, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"  [复制文件] {src} -> {dest}")
    except IOError as e:
        print(f"复制文件失败: {e}")


def safe_copy_tree(src: Path, dest: Path):
    """
    安全地复制目录树
    """
    try:
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        print(f"  [复制目录] {src} -> {dest}")
    except Exception as e:
        print(f"复制目录失败: {e}")


def safe_remove_file(path: Path):
    """
    安全地删除文件
    """
    if path.is_file():
        try:
            os.remove(path)
            print(f"  [删除文件] {path}")
        except OSError as e:
            print(f"删除文件失败: {e}")


def safe_remove_tree(path: Path):
    """
    安全地删除目录树
    """
    if path.is_dir():
        try:
            shutil.rmtree(path)
            print(f"  [删除目录] {path}")
        except OSError as e:
            print(f"删除目录失败: {e}")


def safe_move_file(src: Path, dest: Path):
    """
    安全地移动文件
    """
    try:
        os.makedirs(dest.parent, exist_ok=True)
        shutil.move(str(src), str(dest))
        print(f"  [移动文件] {src} -> {dest}")
    except Exception as e:
        print(f"移动文件失败: {e}")


def safe_move_tree(src: Path, dest: Path):
    """
    安全地移动目录树
    """
    try:
        os.makedirs(dest.parent, exist_ok=True)
        shutil.move(str(src), str(dest))
        print(f"  [移动目录] {src} -> {dest}")
    except Exception as e:
        print(f"移动目录失败: {e}")


def get_symlink_target_env(link_path: Path, base_dir: Path) -> Optional[str]:
    """
    检查 symlink 指向哪个环境
    返回环境名称，如果不是有效的 symlink 则返回 None
    """
    if not link_path.is_symlink():
        return None

    try:
        target = link_path.resolve()
        # 检查目标是否在 base_dir 下
        if base_dir in target.parents:
            # 提取环境名称（base_dir 的下一级目录）
            relative = target.relative_to(base_dir)
            env_name = relative.parts[0] if relative.parts else None
            return env_name
    except Exception as e:
        print(f"解析 symlink 失败: {e}")

    return None


def safe_create_symlink(target: Path, link_path: Path):
    """
    安全地创建符号链接
    如果链接已存在，先删除
    """
    try:
        # 确保链接的父目录存在
        os.makedirs(link_path.parent, exist_ok=True)

        # 如果链接已存在，先删除
        if link_path.exists() or link_path.is_symlink():
            if link_path.is_symlink():
                link_path.unlink()
            elif link_path.is_file():
                link_path.unlink()
            elif link_path.is_dir():
                shutil.rmtree(link_path)

        # 创建符号链接
        link_path.symlink_to(target)
        print(f"  [创建链接] {link_path} -> {target}")
    except Exception as e:
        print(f"创建符号链接失败: {e}")


def safe_remove_symlink(link_path: Path):
    """
    安全地删除符号链接（不删除目标）
    """
    if link_path.is_symlink():
        try:
            link_path.unlink()
            print(f"  [删除链接] {link_path}")
        except OSError as e:
            print(f"删除符号链接失败: {e}")
    elif link_path.exists():
        print(f"  [警告] {link_path} 不是符号链接，跳过删除")
