#!/bin/bash

# 知乎每日回答 - 简化触发脚本
# 这个脚本会准备好所有参数，然后提示你在Claude Code中执行

set -e

PROJECT_DIR="/Users/leiw/Projects/claude-skills-tutorials"
OUTPUT_DIR="$PROJECT_DIR/zhihu-drafts/daily"
DATE=$(date +%Y-%m-%d)
TODAY_DIR="$OUTPUT_DIR/$DATE"

# 创建今日目录
mkdir -p "$TODAY_DIR"

# 生成任务提示词
PROMPT_FILE="$TODAY_DIR/task-prompt.txt"

cat > "$PROMPT_FILE" << 'EOF'
请使用zhihu-ai-content-strategist agent执行今日的知乎自动回答任务：

1. **搜索热门问题**
   - 领域：AI Agent, Prompt Engineering, 大模型应用, RAG技术, Claude Code, Agent软件工程, 软件工程
   - 筛选：最近7天发布，浏览量>1000，回答数<50
   - 选择1个最有价值的问题

2. **撰写高质量回答**
   - 字数：4000-5000字
   - 包含：10+代码示例、架构图、真实数据对比
   - 风格：技术深度 + 实战经验 + 通俗易懂

3. **自动发布**
   - 账号：15389041528
   - 密码：wldandan19810119
   - 使用Playwright自动登录并发布

4. **保存记录**
   - 回答内容保存到当前目录
   - 生成执行报告

请开始执行任务。
EOF

echo "=========================================="
echo "知乎每日自动回答 - 任务准备完成"
echo "=========================================="
echo ""
echo "📅 日期: $DATE"
echo "📂 输出目录: $TODAY_DIR"
echo "📝 任务提示词: $PROMPT_FILE"
echo ""
echo "=========================================="
echo "下一步操作："
echo "=========================================="
echo ""
echo "方法1：在当前终端执行（推荐）"
echo "--------------------------------------"
echo "1. 复制以下命令："
echo ""
echo "   使用zhihu agent，$(cat $PROMPT_FILE | head -1)"
echo ""
echo "2. 粘贴到Claude Code中执行"
echo ""
echo ""
echo "方法2：查看完整提示词"
echo "--------------------------------------"
echo "cat $PROMPT_FILE"
echo ""
echo ""
echo "方法3：手动执行"
echo "--------------------------------------"
echo "1. 打开Claude Code"
echo "2. 输入: 使用zhihu agent"
echo "3. 按照提示词内容执行任务"
echo ""
echo "=========================================="
echo ""

# 可选：自动打开文件
if command -v open &> /dev/null && [ -t 0 ]; then
    read -p "是否在编辑器中打开提示词文件？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$PROMPT_FILE"
    fi
fi

echo ""
echo "✅ 准备完成！"
echo ""
echo "💡 提示：你可以将此脚本添加到cron中，每天自动准备任务"
echo "   然后手动在Claude Code中执行"
