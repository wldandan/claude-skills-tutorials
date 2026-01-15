#!/bin/bash

# Claude Skills & Agents 安装脚本
# 支持 macOS 和 Linux

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
REPO_OWNER="${REPO_OWNER:-gongxh13}"
REPO_NAME="${REPO_NAME:-claude-skills-tutorials}"
BRANCH="${BRANCH:-main}"
BASE_URL="https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${BRANCH}"
API_URL="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents"

# 打印函数
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 从 GitHub API 获取目录列表
get_directory_list() {
    local path="$1"
    local url="${API_URL}/${path}?ref=${BRANCH}"

    # 使用 GitHub API 获取目录内容
    local response=$(curl -fsSL -H "Accept: application/vnd.github.v3+json" "$url")

    if [ -z "$response" ]; then
        print_error "无法获取 $path 的目录列表"
        return 1
    fi

    # 提取文件/目录名
    echo "$response" | grep -o '"name":"[^"]*"' | sed 's/"name":"//g' | sed 's/"//g'
}

# 检查并安装
main() {
    print_info "开始安装 Claude Skills & Agents..."
    echo ""

    # 创建 .claude 目录
    print_info "创建 ~/.claude 目录结构..."
    mkdir -p ~/.claude/skills
    mkdir -p ~/.claude/agents

    # 获取并安装 Skills
    print_info "获取 Skills 列表..."
    skill_dirs=$(get_directory_list "skills")

    if [ -z "$skill_dirs" ]; then
        print_warn "未找到任何 Skills"
    else
        print_info "安装 Skills..."
        skill_count=0
        while IFS= read -r skill; do
            if [ -n "$skill" ]; then
                skill_dir=~/.claude/skills/$skill
                skill_file=$skill_dir/SKILL.md
                url="${BASE_URL}/skills/${skill}/SKILL.md"

                print_info "  安装 $skill..."

                # 创建 skill 目录
                mkdir -p "$skill_dir"

                # 下载文件
                if curl -fsSL -o "$skill_file" "$url"; then
                    print_info "    ✓ $skill 安装成功"
                    ((skill_count++))
                else
                    print_warn "    ✗ $skill 安装失败，跳过"
                fi
            fi
        done <<< "$skill_dirs"
    fi

    echo ""
    print_info "获取 Agents 列表..."
    agent_files=$(get_directory_list "agents")

    if [ -z "$agent_files" ]; then
        print_warn "未找到任何 Agents"
    else
        print_info "安装 Agents..."
        agent_count=0
        while IFS= read -r agent; do
            if [ -n "$agent" ] && [[ "$agent" == *.md ]]; then
                agent_name="${agent%.md}"
                agent_file=~/.claude/agents/${agent}
                url="${BASE_URL}/agents/${agent}"

                print_info "  安装 $agent_name..."

                # 下载文件
                if curl -fsSL -o "$agent_file" "$url"; then
                    print_info "    ✓ $agent_name 安装成功"
                    ((agent_count++))
                else
                    print_warn "    ✗ $agent_name 安装失败，跳过"
                fi
            fi
        done <<< "$agent_files"
    fi

    echo ""
    print_info "安装完成！"
    echo ""
    echo "已安装 $skill_count 个 Skills，$agent_count 个 Agents"
    echo ""
    print_info "现在可以在 Claude Code 中使用这些 Skills 和 Agents 了！"
}

# 检查依赖
check_dependencies() {
    if ! command -v curl &> /dev/null; then
        print_error "curl 未安装，请先安装 curl"
        exit 1
    fi
}

# 主流程
check_dependencies
main
