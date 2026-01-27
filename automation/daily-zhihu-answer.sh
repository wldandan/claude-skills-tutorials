#!/bin/bash

# 每日知乎自动回答脚本
# 执行时间：每天晚上22:00
# 作者：Claude Code
# 创建日期：2026-01-21

set -e  # 遇到错误立即退出

# 配置变量
PROJECT_DIR="/Users/leiw/Projects/claude-skills-tutorials"
LOG_DIR="$PROJECT_DIR/automation/logs"
OUTPUT_DIR="$PROJECT_DIR/zhihu-drafts/daily"
DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/zhihu-answer-$DATE.log"

# 知乎账号信息
ZHIHU_ACCOUNT="15389041528"
ZHIHU_PASSWORD="wldandan19810119"

# 内容领域配置
TOPICS="AI Agent, Prompt Engineering, 大模型应用, RAG技术, Claude Code, Agent软件工程, 软件工程"

# 创建必要的目录
mkdir -p "$LOG_DIR"
mkdir -p "$OUTPUT_DIR"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "开始执行每日知乎自动回答任务"
log "=========================================="

# 切换到项目目录
cd "$PROJECT_DIR"

log "项目目录: $PROJECT_DIR"
log "输出目录: $OUTPUT_DIR"
log "内容领域: $TOPICS"

# 调用Claude Code执行任务
log "正在调用zhihu-ai-content-strategist agent..."

# 使用claude命令行工具执行任务
# 注意：这里需要确保claude命令可用
claude task run \
    --agent zhihu-ai-content-strategist \
    --prompt "请执行每日知乎自动回答任务：

1. 搜索知乎上关于以下领域的热门问题（发布时间在最近7天内，浏览量>1000）：
   - AI Agent
   - Prompt Engineering
   - 大模型应用
   - RAG技术
   - Claude Code
   - Agent软件工程
   - 软件工程

2. 从搜索结果中选择1个最有价值的问题（标准：技术深度、讨论热度、回答质量参差）

3. 为该问题撰写高质量回答（4000+字，包含代码示例、架构图、真实数据）

4. 使用以下账号登录并自动发布：
   - 账号：$ZHIHU_ACCOUNT
   - 密码：$ZHIHU_PASSWORD

5. 发布后记录以下信息：
   - 问题标题和链接
   - 回答字数
   - 发布时间
   - 预期效果

6. 将回答内容和元数据保存到：$OUTPUT_DIR/$DATE/

请按步骤执行，并在完成后生成执行报告。" \
    --output "$OUTPUT_DIR/$DATE/execution-report.json" \
    2>&1 | tee -a "$LOG_FILE"

# 检查执行结果
if [ $? -eq 0 ]; then
    log "✅ 任务执行成功！"
    log "回答已发布到知乎"
    log "详细报告：$OUTPUT_DIR/$DATE/execution-report.json"

    # 发送成功通知（可选）
    # 这里可以添加邮件或其他通知方式

else
    log "❌ 任务执行失败！"
    log "请查看日志文件：$LOG_FILE"

    # 发送失败通知
    exit 1
fi

log "=========================================="
log "任务执行完成"
log "=========================================="
