# claude-skills-tutorials

Claude Skills 和 Sub-agents 使用指南和教程

## 一键安装

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/gongxh13/claude-skills-tutorials/main/scripts/install.sh | bash
```

### Windows (PowerShell)

```powershell
iwr -useb https://raw.githubusercontent.com/gongxh13/claude-skills-tutorials/main/scripts/install.ps1 | iex
```

### 自定义安装

如果想安装到不同的分支或仓库，可以设置环境变量：

```bash
# 自定义仓库所有者
REPO_OWNER=your-username curl -fsSL https://raw.githubusercontent.com/your-username/claude-skills-tutorials/main/scripts/install.sh | bash

# 自定义分支
BRANCH=dev curl -fsSL https://raw.githubusercontent.com/gongxh13/claude-skills-tutorials/main/scripts/install.sh | bash
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
