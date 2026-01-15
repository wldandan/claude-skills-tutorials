# claude-skills-tutorials

Claude Skills 和 Sub-agents 使用指南和教程

## 一键安装

### 本地安装（推荐）

如果你已经 clone 或 fork 了这个仓库，直接在项目根目录运行安装脚本，脚本会自动检测 Git 仓库信息：

**macOS / Linux**
```bash
bash scripts/install.sh
```

**Windows (PowerShell)**
```powershell
.\scripts\install.ps1
```

### 在线安装

从 GitHub 直接下载并运行（默认从原仓库安装）：

**macOS / Linux**
```bash
curl -fsSL https://raw.githubusercontent.com/wldandan/claude-skills-tutorials/main/scripts/install.sh | bash
```

**Windows (PowerShell)**
```powershell
iwr -useb https://raw.githubusercontent.com/wldandan/claude-skills-tutorials/main/scripts/install.ps1 | iex
```

### 安装到自己的 Fork 仓库

如果你 fork 了这个仓库，想从自己的仓库安装：

1. **方案一：本地运行（自动检测，最简单）**
   - clone 你的 fork 仓库后，直接在本地运行脚本即可
   - 脚本会自动检测 Git 仓库信息，无需任何配置

2. **方案二：在线安装（需修改 README）**
   ```bash
   # Fork 后，运行此脚本自动更新 README 中的链接
   bash scripts/update-readme.sh
   ```
   - `update-readme.sh` 会自动检测你的 Git 仓库并更新 README.md
   - 更新后可以直接运行 README 中的在线安装命令

3. **方案三：手动指定（环境变量）**
   ```bash
   # 设置环境变量覆盖
   REPO_OWNER=YOUR_USERNAME bash scripts/install.sh
   ```

### 安装内容说明

安装脚本会自动扫描 GitHub 仓库中的：
- `skills/` 目录下的所有子目录（每个目录代表一个 Skill）
- `agents/` 目录下的所有 `.md` 文件（每个文件代表一个 Agent）

然后将它们安装到本地的 `~/.claude/` 对应目录下。无需手动维护列表，添加新的 Skill 或 Agent 后会自动被安装。

## 文档

- [Skills vs Sub-agents: 使用场景指南](./skills-vs-subagents.md) - 详细说明何时使用 Skills，何时使用 Sub-agents
- [运维领域产品经理 Agent Prompt](./ops-pm-agent-prompt.md) - 智能运维命令行工具的产品经理 Agent 提示词

## 概述

本项目包含关于 Claude 代码中 Skills 和 Sub-agents 的使用指南，帮助开发者做出正确的架构决策。
