#!/usr/bin/env python3
# claude_env/manager.py
# 描述: 包含所有核心业务逻辑，封装在 EnvironmentManager 类中
# [已重构] 使用符号链接 (Symlink) 架构，移除了复制/删除逻辑。
# [已重构] [v4] 逻辑现在由 config.yaml 中的 'managed_paths' 列表驱动。

import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Optional
from pathlib import Path
from claude_env.models import AppConfig, EnvState
from claude_env.config import load_config, load_env_state, save_env_state
from claude_env.utils import (
    get_current_email,
    get_auth_type,
    get_api_endpoint,
    is_auth_valid,
    get_symlink_target_env,
    safe_create_symlink,
    safe_remove_symlink,
    safe_move_file,
    safe_move_tree,
)


class EnvironmentManager:
    """
    封装 Claude 环境管理的所有逻辑 (基于 Symlink)
    """

    def __init__(self):
        self.config: AppConfig = load_config()
        self.state: EnvState = load_env_state()
        self.console = Console()

        # [新] 定义一个“主”配置文件，用于检查 email 和状态
        # 我们假设它是 managed_paths 中的第一项
        if not self.config.managed_paths:
            self.console.print(
                "[bold red]错误: 'managed_paths' 列表为空。请检查你的 config.yaml。[/bold red]"
            )
            exit(1)
        self.primary_config_file = self.config.managed_paths[0]
        self.primary_config_path_home = Path.home() / self.primary_config_file

    def _get_active_env(self) -> Optional[str]:
        """
        [新] 检查符号链接以确定哪个环境是激活的。
        这是状态的"唯一来源"。
        """
        # [修改] 使用 'primary_config_path_home' 作为检查点
        return get_symlink_target_env(
            self.primary_config_path_home, self.config.base_dir
        )

    def _save_current_env(self, env_name: str):
        """
        保存当前环境的修改（如果 symlink 被覆盖为真实文件）
        """
        for rel_path_str in self.config.managed_paths:
            home_path = Path.home() / rel_path_str
            env_path = self.config.base_dir / env_name / rel_path_str

            # 如果 home_path 是真实文件/目录（不是 symlink），需要保存回环境
            if home_path.exists() and not home_path.is_symlink():
                try:
                    if home_path.is_file():
                        # 文件：复制回环境目录
                        import shutil

                        os.makedirs(env_path.parent, exist_ok=True)
                        shutil.copy2(home_path, env_path)
                        print(f"  [自动保存] {home_path} -> {env_path}")
                    elif home_path.is_dir():
                        # 目录：rsync 同步（保留新内容）
                        import subprocess

                        os.makedirs(env_path.parent, exist_ok=True)
                        subprocess.run(
                            ["rsync", "-a", f"{home_path}/", f"{env_path}/"],
                            check=True,
                            capture_output=True,
                        )
                        print(f"  [自动保存] {home_path}/ -> {env_path}/")
                except Exception as e:
                    print(f"  [警告] 保存 {home_path} 失败: {e}")

    def _activate_env(self, env_name: str) -> bool:
        """
        [新] 核心切换逻辑：激活一个环境
        1. 保存当前环境（如果有真实文件被创建）
        2. 删除旧链接
        3. 创建新链接
        """
        env_path = self.config.base_dir / env_name
        if not env_path.is_dir():
            self.console.print(
                f"[bold red]错误[/bold red]: 环境目录 {env_path} 未找到。"
            )
            return False

        # [新增] 保存当前环境的修改
        current_env = self._get_active_env()
        if not current_env:
            # symlink 可能被覆盖，使用上次记录的环境
            current_env = self.state.last_active_env

        if current_env and current_env != env_name:
            self._save_current_env(current_env)

        # [修改] 遍历 config.yaml 中定义的所有 'managed_paths'

        self.console.print("正在清理工作区 (移除旧链接)...")
        for rel_path_str in self.config.managed_paths:
            link_path = Path.home() / rel_path_str
            safe_remove_symlink(link_path)

        self.console.print(f"正在链接到 [bold]{env_name}[/bold] ...")
        for rel_path_str in self.config.managed_paths:
            rel_path = Path(rel_path_str)
            target_path = env_path / rel_path  # e.g., ~/.claude_env/work/.claude.json
            link_path = Path.home() / rel_path  # e.g., ~/.claude.json

            # [修改] 确保 *目标* 父目录存在 (e.g., ~/.claude_env/work/Library/Application Support/)
            os.makedirs(target_path.parent, exist_ok=True)

            # [修改] 如果目标是 .claude 这样的目录，确保它存在
            if rel_path_str.endswith("/"):  # 简单的启发式
                os.makedirs(target_path, exist_ok=True)

            safe_create_symlink(target_path, link_path)

        # [新增] 记录当前激活的环境
        self.state.last_active_env = env_name
        save_env_state(self.state)

        return True

    # --- 公共命令 ---

    def init_manager(self):
        """
        初始化管理器。
        如果检测到现有的 .claude.json，将其“吸收”为第一个环境。
        """
        if self.state.environments:
            # 已经初始化过了
            return

        self.console.print("ClaudeEnv 首次运行：正在初始化...")

        # [修改] 检查主配置文件
        primary_link = self.primary_config_path_home

        if primary_link.is_file() and not primary_link.is_symlink():
            self.console.print("检测到现有的 Claude 配置。")
            email = get_current_email(primary_link)
            env_name = email if email else "default"

            self.console.print(
                f"正在将现有配置“吸收”为新环境: '[bold]{env_name}[/bold]'"
            )
            env_path = self.config.base_dir / env_name
            os.makedirs(env_path, exist_ok=True)

            # [修改] 遍历所有 managed_paths 并移动它们
            for rel_path_str in self.config.managed_paths:
                src_path = Path.home() / rel_path_str
                dest_path = env_path / rel_path_str

                if src_path.is_file() and not src_path.is_symlink():
                    safe_move_file(src_path, dest_path)
                elif src_path.is_dir() and not src_path.is_symlink():
                    safe_move_tree(src_path, dest_path)

            # 1. 更新 state 对象
            self.state.environments.append(env_name)
            save_env_state(self.state)

            # 2. 激活这个新环境 (创建符号链接)
            self._activate_env(env_name)

            self.console.print(f"初始化完成。已激活 '[bold]{env_name}[/bold]'。")
        else:
            self.console.print("未检测到现有配置。初始化完成。")
            self.console.print("请运行 'add <name>' 来创建你的第一个环境。")

    def add(self, env_name: str):
        """
        添加一个新环境。
        """
        if env_name in self.state.environments:
            self.console.print(f"[bold red]错误[/bold red]: 环境 '{env_name}' 已存在。")
            self.console.print(
                "如果你想切换，请使用: python claude_env.py switch <name>"
            )
            return

        self.console.print(f"正在添加新环境: [bold]{env_name}[/bold] ...")

        env_path = self.config.base_dir / env_name

        # [修改] 遍历 managed_paths 为链接创建目标父目录
        for rel_path_str in self.config.managed_paths:
            # e.g., ~/.claude_env/work/Library/Application Support/Claude
            target_path = env_path / Path(rel_path_str)

            # 确保父目录存在 (e.g., .../work/Library/Application Support/)
            os.makedirs(target_path.parent, exist_ok=True)

            # 启发式：如果路径没有扩展名或是 .claude，则假定它是一个目录
            # (这不完美，但对于 symlink 目标来说足够了)
            if not Path(rel_path_str).suffix or rel_path_str == ".claude":
                os.makedirs(target_path, exist_ok=True)

        # 2. 更新状态文件
        self.state.environments.append(env_name)
        save_env_state(self.state)

        # 3. 立即切换到这个新环境
        self.switch(env_name)

        self.console.print(f"[green]成功创建新环境 '[bold]{env_name}[/bold]'。[/green]")
        self.console.print()
        self.console.print("[yellow]接下来请：[/yellow]")
        self.console.print(
            "  1️⃣  [bold]OAuth 订阅用户[/bold]: 运行 'claude' 并登录你的账号"
        )
        self.console.print("  2️⃣  [bold]API Key 镜像用户[/bold]: 手动编辑配置文件")
        self.console.print(
            f"      配置文件位置: [cyan]{self.config.base_dir / env_name / '.claude.json'}[/cyan]"
        )
        self.console.print()
        self.console.print(
            "[dim]提示: 配置完成后，运行 'python claude_env.py status' 查看状态[/dim]"
        )

    def switch(self, env_name: str):
        """
        切换到已存在的环境
        """
        if env_name not in self.state.environments:
            self.console.print(f"[bold red]错误[/bold red]: 环境 '{env_name}' 不存在。")
            self.console.print(
                "请先使用 'add' 命令创建: python claude_env.py add <name>"
            )
            return

        active_env = self._get_active_env()
        if env_name == active_env:
            self.console.print(f"你已在环境 '[bold]{env_name}[/bold]' 中。")
            return

        self.console.print(f"正在切换到环境: [bold]{env_name}[/bold] ...")

        if self._activate_env(env_name):
            self.console.print(f"成功切换到环境: [bold]{env_name}[/bold]")
        else:
            self.console.print(f"[bold red]切换到 {env_name} 失败。[/bold red]")

    def rename(self, new_name: str):
        """
        重命名当前激活的环境
        """
        active_env = self._get_active_env()
        if not active_env:
            self.console.print("[bold red]错误[/bold red]: 没有激活的环境可以重命名。")
            return

        if new_name in self.state.environments:
            self.console.print(
                f"[bold red]错误[/bold red]: 环境名称 '{new_name}' 已存在。"
            )
            return

        old_name = active_env
        self.console.print(
            f"正在将环境 '[bold]{old_name}[/bold]' 重命名为 '[bold]{new_name}[/bold]'..."
        )

        old_path = self.config.base_dir / old_name
        new_path = self.config.base_dir / new_name

        try:
            # 1. 重命名备份目录
            old_path.rename(new_path)

            # 2. 更新 state 对象
            self.state.environments.remove(old_name)
            self.state.environments.append(new_name)
            save_env_state(self.state)

            # 3. 重新激活 (更新符号链接以指向新路径)
            self._activate_env(new_name)

            self.console.print("[green]重命名成功！[/green]")

        except Exception as e:
            self.console.print(f"[bold red]重命名失败[/bold red]: {e}")
            # 尝试恢复
            if new_path.is_dir() and not old_path.is_dir():
                new_path.rename(old_path)
            self.console.print("操作已回滚。")

    def list_envs(self):
        """
        列出所有已保存的环境 (包含 email)，并使用表格显示。
        """
        if not self.state.environments:
            self.console.print("未找到任何环境。")
            self.console.print(
                "请运行 'init' 来自动检测当前配置，或 'add' 来创建新环境。"
            )
            return

        self.console.print()  # 添加一个空行

        table = Table(
            title="[bold]Claude 环境列表[/bold]",
            show_header=True,
            header_style="bold magenta",
            border_style="dim",
        )

        table.add_column("状态", style="cyan", justify="center")
        table.add_column("环境名称", style="bold cyan")
        table.add_column("认证", style="magenta")
        table.add_column("用户信息", style="yellow")
        table.add_column("Endpoint", style="green")
        table.add_column("路径", style="dim")

        active_env = self._get_active_env()

        for env in self.state.environments:
            config_path = self.config.base_dir / env / self.primary_config_file

            # 1. 状态（激活 + 可用性）
            is_active = env == active_env
            is_valid = is_auth_valid(config_path)

            if is_active and is_valid:
                status_marker = "[green]✓ 激活[/green]"
            elif is_active and not is_valid:
                status_marker = "[yellow]⚠ 激活[/yellow]"
            elif not is_active and is_valid:
                status_marker = "[cyan]○ 就绪[/cyan]"
            else:
                status_marker = "[dim]○ 未配置[/dim]"

            # 2. 环境名称
            env_name = env

            # 3. 认证类型
            auth_type = get_auth_type(config_path)
            auth_display = (
                "OAuth"
                if auth_type == "OAuth"
                else "API Key"
                if auth_type == "API Key"
                else "未知"
            )

            # 4. 用户信息（邮箱或 userID）
            email = get_current_email(config_path)
            if email:
                user_display = email
            else:
                user_display = (
                    "[dim]未登录[/dim]" if auth_type == "OAuth" else "[dim]-[/dim]"
                )

            # 5. Endpoint（镜像 URL）
            endpoint = get_api_endpoint(config_path)
            if endpoint:
                endpoint_display = endpoint
            elif auth_type == "API Key":
                endpoint_display = "[red]需配置[/red]"
            else:
                endpoint_display = "[dim]官方[/dim]"  # OAuth 默认官方

            # 6. 路径
            location_display = f"~/.claude_env/{env}"

            table.add_row(
                status_marker,
                env_name,
                auth_display,
                user_display,
                endpoint_display,
                location_display,
            )

        self.console.print(table)
        self.console.print()

    def status(self):
        """
        显示一个面板，包含当前工具状态和实际登录状态。
        """
        # 1. 工具认为的激活环境 (通过读取 symlink)
        tool_env = self._get_active_env()

        # 2. 获取认证类型
        auth_type = get_auth_type(self.primary_config_path_home)

        # 3. 根据认证类型显示不同信息
        if auth_type == "OAuth":
            real_email = get_current_email(self.primary_config_path_home)
            if real_email:
                user_info = f"[green]{real_email}[/green]"
                auth_status = "[green]✓ 已登录[/green]"
            else:
                user_info = "[red]未登录[/red]"
                auth_status = "[red]✗ 未登录[/red]"
            auth_info = (
                f"[bold]认证类型:[/bold] [magenta]OAuth 订阅[/magenta]\n"
                f"[bold]用户信息:[/bold] {user_info}\n"
                f"[bold]状态:[/bold] {auth_status}"
            )
        elif auth_type == "API Key":
            endpoint = get_api_endpoint(self.primary_config_path_home)
            if endpoint:
                endpoint_info = f"[green]{endpoint}[/green]"
                auth_status = "[green]✓ 已配置[/green]"
            else:
                endpoint_info = "[red]未配置[/red]"
                auth_status = "[red]✗ 未配置[/red]"
            auth_info = (
                f"[bold]认证类型:[/bold] [magenta]API Key 镜像[/magenta]\n"
                f"[bold]Endpoint:[/bold] {endpoint_info}\n"
                f"[bold]状态:[/bold] {auth_status}"
            )
        else:
            auth_info = (
                "[bold]认证类型:[/bold] [yellow]未知[/yellow]\n"
                "[bold]状态:[/bold] [red]✗ 未配置[/red]"
            )

        status_message = (
            f"[bold]激活环境:[/bold] [cyan]{tool_env if tool_env else '无 (已断开链接)'}[/cyan]\n"
            + auth_info
        )

        # 4. 交叉验证
        warning = ""
        if (
            not self.primary_config_path_home.is_symlink()
            and self.primary_config_path_home.exists()
        ):
            warning = f"\n\n[bold yellow]警告:[/bold yellow] {self.primary_config_path_home} 不是一个符号链接。\n请运行 'init' 或 'switch' 来修复。"
        elif not tool_env and auth_type != "Unknown":
            warning = "\n\n[bold yellow]注意:[/bold yellow] 配置已存在，但链接已断开。"

        self.console.print(
            Panel(
                status_message + warning,
                title="Claude-Env 状态面板",
                border_style="blue",
                padding=(1, 2),
            )
        )

    def save(self):
        """
        强制保存当前激活环境的配置
        注意：在 symlink 架构下，配置会自动保存到激活的环境目录中，
        这个命令主要用于兼容性和提示用户当前状态
        """
        active_env = self._get_active_env()
        if not active_env:
            self.console.print("[bold red]错误[/bold red]: 没有激活的环境。")
            self.console.print("请先使用 'switch' 命令切换到一个环境。")
            return

        env_path = self.config.base_dir / active_env
        self.console.print(f"[bold]当前激活环境:[/bold] [cyan]{active_env}[/cyan]")
        self.console.print(f"[bold]配置存储位置:[/bold] {env_path}")
        self.console.print()
        self.console.print("[green]提示:[/green] 当前使用 symlink 架构，")
        self.console.print("所有配置修改会自动保存到激活环境的目录中。")
        self.console.print("无需手动保存。")

    def set_api_key(self, api_key: str, endpoint: str):
        """
        为当前激活环境配置 API Key 和 Endpoint
        """
        active_env = self._get_active_env()
        if not active_env:
            self.console.print("[bold red]错误[/bold red]: 没有激活的环境。")
            self.console.print("请先使用 'switch' 命令切换到一个环境。")
            return

        config_path = self.config.base_dir / active_env / self.primary_config_file

        # 读取现有配置或创建新配置
        try:
            if config_path.is_file():
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}

            # 设置 API Key 和 Endpoint
            data["apiKey"] = api_key
            data["apiEndpoint"] = endpoint

            # 确保有基本字段（兼容 Claude Code）
            if "installMethod" not in data:
                data["installMethod"] = "unknown"
            if "autoUpdates" not in data:
                data["autoUpdates"] = True

            # 保存回文件
            os.makedirs(config_path.parent, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.console.print(
                f"[green]✓ 成功配置 API Key 到环境 '[bold]{active_env}[/bold]'[/green]"
            )
            self.console.print()
            self.console.print(f"[bold]Endpoint:[/bold] [cyan]{endpoint}[/cyan]")
            self.console.print(
                f"[bold]API Key:[/bold] [dim]{api_key[:8]}...{api_key[-4:]}[/dim]"
            )
            self.console.print()
            self.console.print("[yellow]提示:[/yellow]")
            self.console.print("  • Claude Code 会自动从 ~/.claude.json 读取 API Key")
            self.console.print(
                '  • 也可以设置环境变量: export ANTHROPIC_API_KEY="your-key"'
            )
            self.console.print("  • 镜像站需要在 settings.json 中配置 apiUrl")
            self.console.print()
            self.console.print(
                "[dim]运行 'python claude_env.py status' 查看配置状态[/dim]"
            )

        except Exception as e:
            self.console.print(f"[bold red]配置失败[/bold red]: {e}")

    def remove(self, env_name: str):
        """
        删除指定的环境（交互式确认）
        """
        # 1. 检查环境是否存在
        if env_name not in self.state.environments:
            self.console.print(f"[bold red]错误[/bold red]: 环境 '{env_name}' 不存在。")
            return

        # 2. 检查是否是当前激活的环境
        active_env = self._get_active_env()
        if env_name == active_env:
            self.console.print(
                f"[bold red]错误[/bold red]: 不能删除当前激活的环境 '{env_name}'。"
            )
            self.console.print("请先切换到其他环境，然后再删除。")
            return

        # 3. 显示要删除的信息
        env_path = self.config.base_dir / env_name
        config_path = self.config.base_dir / env_name / self.primary_config_file

        self.console.print()
        self.console.print("[bold red]⚠ 警告: 即将删除环境[/bold red]")
        self.console.print()
        self.console.print(f"  [bold]环境名称:[/bold] {env_name}")
        self.console.print(f"  [bold]路径:[/bold] {env_path}")

        # 显示环境信息
        auth_type = get_auth_type(config_path)
        email = get_current_email(config_path)
        endpoint = get_api_endpoint(config_path)

        if auth_type == "OAuth" and email:
            self.console.print(f"  [bold]用户:[/bold] {email}")
        elif auth_type == "API Key" and endpoint:
            self.console.print(f"  [bold]Endpoint:[/bold] {endpoint}")

        self.console.print()
        self.console.print("[bold red]此操作不可恢复！[/bold red]")
        self.console.print()

        # 4. 交互式确认
        try:
            confirmation = input("确认删除? 请输入 yes 或 no: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            self.console.print("[yellow]操作已取消[/yellow]")
            return

        if confirmation != "yes":
            self.console.print()
            self.console.print("[yellow]操作已取消[/yellow]")
            return

        # 5. 执行删除
        self.console.print()
        try:
            import shutil

            # 删除环境目录
            if env_path.exists():
                shutil.rmtree(env_path)
                self.console.print(f"[green]✓ 已删除目录:[/green] {env_path}")

            # 从状态列表中移除
            self.state.environments.remove(env_name)
            save_env_state(self.state)
            self.console.print(f"[green]✓ 已从环境列表中移除:[/green] {env_name}")

            self.console.print()
            self.console.print(f"[green]成功删除环境 '[bold]{env_name}[/bold]'！[/green]")

        except Exception as e:
            self.console.print(f"[bold red]删除失败[/bold red]: {e}")

    def uninstall(self):
        """
        卸载 ClaudeCodeManager（交互式确认）
        """
        import subprocess
        import shutil
        from pathlib import Path

        self.console.print()
        self.console.print("[bold red]⚠ 警告: 即将卸载 ClaudeCodeManager[/bold red]")
        self.console.print()
        self.console.print("这将执行以下操作:")
        self.console.print("  1. 删除全局命令 [cyan]claude_env[/cyan]")
        self.console.print("  2. (可选) 删除所有环境数据 [cyan]~/.claude_env[/cyan]")
        self.console.print()

        # 第一次确认
        try:
            confirmation = input("确认卸载? 请输入 yes 或 no: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            self.console.print("[yellow]卸载已取消[/yellow]")
            return

        if confirmation != "yes":
            self.console.print()
            self.console.print("[yellow]卸载已取消[/yellow]")
            return

        self.console.print()

        # 1. 删除全局命令
        launcher_path = Path.home() / ".local" / "bin" / "claude_env"
        if launcher_path.exists():
            try:
                launcher_path.unlink()
                self.console.print(f"[green]✓ 已删除全局命令:[/green] {launcher_path}")
            except Exception as e:
                self.console.print(f"[red]✗ 删除全局命令失败:[/red] {e}")
        else:
            self.console.print("[yellow]全局命令不存在，跳过[/yellow]")

        # 2. 询问是否删除环境数据
        self.console.print()
        self.console.print("[bold]环境数据位于:[/bold] [cyan]~/.claude_env[/cyan]")
        self.console.print("这包含您所有保存的 Claude Code 环境配置")
        self.console.print()

        try:
            delete_data = input("是否删除所有环境数据? (y/N): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            delete_data = "n"

        if delete_data in ["y", "yes"]:
            env_dir = Path.home() / ".claude_env"
            if env_dir.exists():
                try:
                    shutil.rmtree(env_dir)
                    self.console.print(f"[green]✓ 已删除环境数据:[/green] {env_dir}")
                except Exception as e:
                    self.console.print(f"[red]✗ 删除环境数据失败:[/red] {e}")
            else:
                self.console.print("[yellow]环境数据不存在，跳过[/yellow]")
        else:
            self.console.print("[cyan]保留环境数据[/cyan]")

        # 完成
        self.console.print()
        self.console.print("[green]✓ 卸载完成![/green]")
        self.console.print()
        self.console.print("[dim]项目源代码仍保留在当前目录[/dim]")
        self.console.print("[dim]如需完全删除，请手动删除项目目录[/dim]")
