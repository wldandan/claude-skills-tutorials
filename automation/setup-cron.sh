#!/bin/bash

# Cron任务安装脚本
# 用于设置每日知乎自动回答任务

set -e

SCRIPT_DIR="/Users/leiw/Projects/claude-skills-tutorials/automation"
MAIN_SCRIPT="$SCRIPT_DIR/daily-zhihu-answer.sh"

echo "=========================================="
echo "知乎每日自动回答 - Cron任务安装"
echo "=========================================="

# 检查主脚本是否存在
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "❌ 错误：找不到主脚本 $MAIN_SCRIPT"
    exit 1
fi

# 赋予执行权限
echo "正在设置脚本执行权限..."
chmod +x "$MAIN_SCRIPT"
echo "✅ 权限设置完成"

# 显示当前的cron任务
echo ""
echo "当前的cron任务："
crontab -l 2>/dev/null || echo "(无)"

# 询问是否继续
echo ""
read -p "是否要添加新的cron任务？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消安装"
    exit 0
fi

# 创建临时cron文件
TEMP_CRON=$(mktemp)
crontab -l 2>/dev/null > "$TEMP_CRON" || true

# 检查是否已存在相同任务
if grep -q "daily-zhihu-answer.sh" "$TEMP_CRON"; then
    echo "⚠️  警告：已存在类似的cron任务"
    echo "请手动编辑crontab: crontab -e"
    rm "$TEMP_CRON"
    exit 1
fi

# 添加新任务
echo "" >> "$TEMP_CRON"
echo "# 知乎每日自动回答任务 - 每天晚上22:00执行" >> "$TEMP_CRON"
echo "0 22 * * * $MAIN_SCRIPT" >> "$TEMP_CRON"

# 安装新的crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo ""
echo "✅ Cron任务安装成功！"
echo ""
echo "新的cron任务："
crontab -l | tail -2

echo ""
echo "=========================================="
echo "安装完成"
echo "=========================================="
echo ""
echo "任务将在每天晚上22:00自动执行"
echo ""
echo "常用命令："
echo "  查看cron任务: crontab -l"
echo "  编辑cron任务: crontab -e"
echo "  删除cron任务: crontab -r"
echo "  查看日志: tail -f $SCRIPT_DIR/logs/zhihu-answer-\$(date +%Y-%m-%d).log"
echo ""
