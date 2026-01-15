# Claude Skills & Agents 安装脚本
# 支持 Windows (PowerShell)

# 配置 - 自动检测 Git 仓库
$env:REPO_OWNER = $env:REPO_OWNER
$env:REPO_NAME = $env:REPO_NAME

# 如果当前目录是 Git 仓库，则从 remote URL 中提取
if (Test-Path .git) {
    try {
        $remoteUrl = git remote get-url origin 2>$null
        if (-not $remoteUrl) {
            $remoteUrl = git remote get-url (git remote | Select-Object -First 1) 2>$null
        }

        if ($remoteUrl) {
            # 从 URL 中提取 owner 和 repo 名称
            if ($remoteUrl -match 'github\.com[:/](?<owner>[^/]+)/(?<repo>[^/\.]+)') {
                if (-not $env:REPO_OWNER) {
                    $env:REPO_OWNER = $Matches.owner
                }
                if (-not $env:REPO_NAME) {
                    $env:REPO_NAME = $Matches.repo
                }
            }
        }
    }
    catch {
        # 忽略 Git 检测错误，使用默认值
    }
}

# 如果检测失败或未设置，使用默认值
$env:REPO_OWNER = if ($env:REPO_OWNER) { $env:REPO_OWNER } else { "wldandan" }
$env:REPO_NAME = if ($env:REPO_NAME) { $env:REPO_NAME } else { "claude-skills-tutorials" }
$env:BRANCH = if ($env:BRANCH) { $env:BRANCH } else { "main" }
$BASE_URL = "https://raw.githubusercontent.com/$($env:REPO_OWNER)/$($env:REPO_NAME)/$($env:BRANCH)"
$API_URL = "https://api.github.com/repos/$($env:REPO_OWNER)/$($env:REPO_NAME)/contents"

# 打印函数
function Write-Info {
    Write-Host "[INFO] $args" -ForegroundColor Green
}

function Write-Warn {
    Write-Host "[WARN] $args" -ForegroundColor Yellow
}

function Write-Error {
    Write-Host "[ERROR] $args" -ForegroundColor Red
}

# 从 GitHub API 获取目录列表
function Get-DirectoryList {
    param([string]$Path)

    $url = "${API_URL}/${Path}?ref=$($env:BRANCH)"

    try {
        $response = Invoke-RestMethod -Uri $url -Headers @{
            "Accept" = "application/vnd.github.v3+json"
        }
        return $response
    }
    catch {
        Write-Error "无法获取 $Path 的目录列表: $_"
        return $null
    }
}

# 主函数
function Main {
    Write-Info "开始安装 Claude Skills & Agents..."
    Write-Host ""

    # 创建 .claude 目录
    $claudeDir = Join-Path $env:USERPROFILE ".claude"
    $skillsDir = Join-Path $claudeDir "skills"
    $agentsDir = Join-Path $claudeDir "agents"

    Write-Info "创建 $claudeDir 目录结构..."
    New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
    New-Item -ItemType Directory -Force -Path $agentsDir | Out-Null

    # 获取并安装 Skills
    Write-Info "获取 Skills 列表..."
    $skillItems = Get-DirectoryList "skills"

    $skillCount = 0
    if ($skillItems) {
        Write-Info "安装 Skills..."
        foreach ($item in $skillItems) {
            if ($item.type -eq "dir") {
                $skill = $item.name
                $skillDir = Join-Path $skillsDir $skill
                $skillFile = Join-Path $skillDir "SKILL.md"
                $url = "$BASE_URL/skills/$skill/SKILL.md"

                Write-Info "  安装 $skill..."

                # 创建 skill 目录
                New-Item -ItemType Directory -Force -Path $skillDir | Out-Null

                # 下载文件
                try {
                    Invoke-WebRequest -Uri $url -OutFile $skillFile -UseBasicParsing
                    Write-Info "    $skill 安装成功"
                    $skillCount++
                }
                catch {
                    Write-Warn "    $skill 安装失败，跳过"
                }
            }
        }
    } else {
        Write-Warn "未找到任何 Skills"
    }

    Write-Host ""
    Write-Info "获取 Agents 列表..."
    $agentItems = Get-DirectoryList "agents"

    $agentCount = 0
    if ($agentItems) {
        Write-Info "安装 Agents..."
        foreach ($item in $agentItems) {
            if ($item.type -eq "file" -and $item.name -match "\.md$") {
                $agentFile = Join-Path $agentsDir $item.name
                $url = "$BASE_URL/agents/$($item.name)"

                $agentName = $item.name -replace "\.md$", ""

                Write-Info "  安装 $agentName..."

                # 下载文件
                try {
                    Invoke-WebRequest -Uri $url -OutFile $agentFile -UseBasicParsing
                    Write-Info "    $agentName 安装成功"
                    $agentCount++
                }
                catch {
                    Write-Warn "    $agentName 安装失败，跳过"
                }
            }
        }
    } else {
        Write-Warn "未找到任何 Agents"
    }

    Write-Host ""
    Write-Info "安装完成！"
    Write-Host ""
    Write-Host "已安装 $skillCount 个 Skills，$agentCount 个 Agents"
    Write-Host ""
    Write-Info "现在可以在 Claude Code 中使用这些 Skills 和 Agents 了！"
}

# 检查依赖
function Check-Dependencies {
    # PowerShell 通常自带 Invoke-WebRequest，无需额外检查
}

# 主流程
Check-Dependencies
Main
