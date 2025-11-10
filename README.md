# ClaudeCodeManager

Claude Code 环境管理器 - 支持多账号/API 快速切换的命令行工具

## 特性

- **多环境管理**: 轻松管理多个 Claude Code 配置环境
- **快速切换**: 一条命令即可切换账号,无需重复登录
- **双认证支持**: 同时支持 OAuth 订阅和 API Key 镜像站
- **自动保存**: 基于符号链接架构,配置自动同步保存
- **交互友好**: Rich 样式的终端界面,信息展示清晰
- **安全删除**: 删除环境前交互式确认,避免误操作

## 安装

### 前置要求

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) 包管理器

### 快速安装

```bash
# 克隆仓库
git clone https://github.com/LordFoxFairy/ClaudeCodeManager.git
cd ClaudeCodeManager

# 运行安装脚本
bash install.sh
```

安装完成后,`claude_env` 命令将全局可用。

如果提示 PATH 未配置,请在 shell 配置文件中添加:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## 快速开始

### 1. 初始化管理器

首次使用需要初始化,这会自动保存当前的 Claude Code 配置为第一个环境:

```bash
claude_env init
```

### 2. 添加新环境

创建一个新的空白环境:

```bash
claude_env add work
```

**OAuth 用户**: 运行 `claude` 命令并登录你的账号

**API Key 用户**: 使用 `set-api` 命令配置:

```bash
claude_env set-api "sk-ant-xxx..." "https://api.example.com/v1"
```

### 3. 切换环境

切换到已保存的环境:

```bash
claude_env switch default
```

### 4. 查看环境列表

列出所有环境及其状态:

```bash
claude_env list
```

输出示例:

```
┏━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃  状态  ┃ 环境名称 ┃ 认证    ┃ 用户信息      ┃ Endpoint      ┃
┡━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ ✓ 激活 │ default  │ OAuth   │ user@email.com│ 官方          │
│ ○ 就绪 │ work     │ OAuth   │ work@email.com│ 官方          │
│ ○ 就绪 │ mirror   │ API Key │ User: 44ba... │ https://api...│
└────────┴──────────┴─────────┴───────────────┴───────────────┘
```

### 5. 查看当前状态

显示当前激活环境和认证信息:

```bash
claude_env status
```

## 命令列表

| 命令 | 说明 |
|------|------|
| `claude_env init` | 初始化管理器,保存当前配置为第一个环境 |
| `claude_env add <name>` | 创建新环境并切换到该环境 |
| `claude_env switch <name>` | 切换到指定环境 |
| `claude_env list` | 列出所有环境及详细信息 |
| `claude_env status` | 显示当前环境状态 |
| `claude_env rename <new_name>` | 重命名当前激活的环境 |
| `claude_env save` | 强制保存当前环境配置 |
| `claude_env set-api <key> <endpoint>` | 配置 API Key 和镜像站地址 |
| `claude_env remove <name>` | 删除指定环境(交互式确认) |
| `claude_env --help` | 显示帮助信息 |

## 使用场景

### 场景 1: 个人账号 + 工作账号

```bash
# 保存当前个人账号为 default
claude_env init

# 创建工作环境
claude_env add work
# 运行 claude 并登录工作账号

# 快速切换
claude_env switch default  # 切换到个人账号
claude_env switch work     # 切换到工作账号
```

### 场景 2: 订阅账号 + API 镜像站

```bash
# 保存订阅账号
claude_env init

# 创建镜像站环境
claude_env add mirror
claude_env set-api "sk-ant-xxx..." "https://api.mirror.com/v1"

# 切换使用
claude_env switch default  # 使用官方订阅
claude_env switch mirror   # 使用镜像站
```

### 场景 3: 多个 API Key

```bash
# 项目 A
claude_env add project-a
claude_env set-api "sk-ant-aaa..." "https://api-a.com/v1"

# 项目 B
claude_env add project-b
claude_env set-api "sk-ant-bbb..." "https://api-b.com/v1"

# 快速切换项目
claude_env switch project-a
claude_env switch project-b
```

## 工作原理

ClaudeCodeManager 使用**符号链接 (Symlink)** 架构:

- 所有环境配置存储在 `~/.claude_env/<env_name>/`
- 激活环境时,创建 `~/.claude.json` → `~/.claude_env/<env_name>/.claude.json` 的符号链接
- Claude Code 读取 `~/.claude.json` 时自动使用激活环境的配置
- 配置修改会自动写入激活环境的目录,无需手动保存

**管理的文件**:
- `~/.claude.json` - 认证配置文件
- `~/.claude/` - Claude Code 配置目录

## 卸载

```bash
bash uninstall.sh
```

卸载脚本会:
1. 删除全局命令 `claude_env`
2. 询问是否删除环境数据 (`~/.claude_env`)

## 目录结构

```
ClaudeCodeManager/
├── claude_env/          # 核心包目录
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py          # Typer 命令行接口
│   ├── config.py       # 配置加载
│   ├── manager.py      # 核心业务逻辑
│   ├── models.py       # Pydantic 数据模型
│   └── utils.py        # 工具函数
├── install.sh          # 安装脚本
├── uninstall.sh        # 卸载脚本
├── pyproject.toml      # 项目配置
└── README.md           # 本文件
```

## 技术栈

- **Python 3.13**: 现代 Python 特性
- **Typer**: 优雅的 CLI 框架
- **Rich**: 漂亮的终端输出
- **Pydantic**: 类型安全的数据模型
- **uv**: 快速的 Python 包管理器

## 常见问题

### Q: 切换环境后 Claude Code 提示需要登录?

A: 这是正常的,因为新环境是空白的。请按提示登录或配置 API Key。

### Q: 环境数据存储在哪里?

A: 所有环境数据存储在 `~/.claude_env/` 目录下,每个环境一个子目录。

### Q: 如何备份我的环境?

A: 直接复制 `~/.claude_env/` 目录即可,所有配置都在里面。

### Q: 删除环境后能恢复吗?

A: 不能,删除是永久的。建议在删除前先备份重要环境。

### Q: 支持 Windows 吗?

A: 目前主要支持 macOS 和 Linux,Windows 需要 WSL 环境。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request!

## 作者

[LordFoxFairy](https://github.com/LordFoxFairy)

## 相关链接

- [Claude Code 官方文档](https://docs.anthropic.com/claude/docs)
- [uv 包管理器](https://github.com/astral-sh/uv)
- [Typer 文档](https://typer.tiangolo.com/)
