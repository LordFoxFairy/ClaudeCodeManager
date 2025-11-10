#!/usr/bin/env python3
# claude_env/cli.py
# 描述: 定义 Typer 命令行界面

import typer
from rich.console import Console
from typing_extensions import Annotated

from claude_env.manager import EnvironmentManager

# --- 初始化 Typer 应用和 Rich Console ---
app = typer.Typer(
    help="Claude 环境管理器 (claude_env)",
    add_completion=False,
    name="claude_env"  # 设置程序名称
)
console = Console()


# --- Typer 回调 ---
@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """
    在每个命令运行前被调用。
    1. 创建 EnvironmentManager 实例。
    2. 将 manager 实例存储在上下文中，供子命令使用。
    """
    try:
        manager = EnvironmentManager()
        # manager.init_manager()  # 运行初始化逻辑 <-- [删除] 不再自动初始化
        ctx.obj = manager  # 将 manager 传递给子命令
    except ImportError:
        # 这个错误在 config.py 中被捕获，但作为双重保险
        console.print("[bold red]错误: 依赖库未安装。[/bold red]")
        console.print("请运行: pip install -r requirements.txt")
        raise typer.Exit(code=1)

    # 如果没有调用子命令 (例如只运行了 'python claude_env.py')
    if ctx.invoked_subcommand is None:
        console.print("[bold]欢迎使用 Claude 环境管理器[/bold]")
        console.print("未提供任何命令。请使用 '--help' 查看可用命令。")
        console.print(
            "如果是首次使用，请先运行: [bold]python claude_env.py init[/bold]"
        )


# --- Typer 命令 ---


@app.command("init")
def init_app(ctx: typer.Context):
    """
    初始化管理器：自动检测当前配置并将其保存为第一个环境。
    """
    manager: EnvironmentManager = ctx.obj
    manager.init_manager()


@app.command("add")
def add_env(
    ctx: typer.Context,
    env_name: Annotated[
        str, typer.Argument(help="要创建的新环境的名称 (例如: 'personal' 或 'work')")
    ],
):
    """
    添加一个新环境并切换到该空白环境。
    """
    manager: EnvironmentManager = ctx.obj
    manager.add(env_name)


@app.command("switch")
def switch_env(
    ctx: typer.Context,
    env_name: Annotated[str, typer.Argument(help="要切换到的环境名称")],
):
    """
    切换到指定的已保存环境。
    """
    manager: EnvironmentManager = ctx.obj
    manager.switch(env_name)


@app.command("rename")
def rename_env(
    ctx: typer.Context,
    new_name: Annotated[str, typer.Argument(help="当前环境的新名称 (例如: 'my-work')")],
):
    """
    重命名当前激活的环境。
    """
    manager: EnvironmentManager = ctx.obj
    manager.rename(new_name)


@app.command("list")
def list_envs(ctx: typer.Context):
    """
    列出所有已保存的环境。
    """
    manager: EnvironmentManager = ctx.obj
    manager.list_envs()


@app.command("save")
def save_current(ctx: typer.Context):
    """
    强制保存当前激活环境的配置。
    """
    manager: EnvironmentManager = ctx.obj
    manager.save()


@app.command("status")
def status(ctx: typer.Context):
    """
    显示当前激活环境和实际登录用户的状态。
    """
    manager: EnvironmentManager = ctx.obj
    manager.status()


@app.command("set-api")
def set_api_key(
    ctx: typer.Context,
    api_key: Annotated[str, typer.Argument(help="API Key")],
    endpoint: Annotated[str, typer.Argument(help="镜像站 Endpoint URL")],
):
    """
    为当前激活环境配置 API Key 和 Endpoint（用于镜像站）。
    """
    manager: EnvironmentManager = ctx.obj
    manager.set_api_key(api_key, endpoint)


@app.command("remove")
def remove_env(
    ctx: typer.Context,
    env_name: Annotated[str, typer.Argument(help="要删除的环境名称")],
):
    """
    删除指定的环境（交互式确认）。
    """
    manager: EnvironmentManager = ctx.obj
    manager.remove(env_name)


@app.command("uninstall")
def uninstall_app(
    ctx: typer.Context,
):
    """
    卸载 ClaudeCodeManager（交互式确认）。
    """
    manager: EnvironmentManager = ctx.obj
    manager.uninstall()
