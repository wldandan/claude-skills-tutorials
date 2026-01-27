#!/bin/bash

# 知乎完全自动化回答 - 启动脚本

set -e

PROJECT_DIR="/Users/leiw/Projects/claude-skills-tutorials"
cd "$PROJECT_DIR/automation"

echo "=========================================="
echo "知乎完全自动化回答系统"
echo "=========================================="
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到python3"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
python3 -c "import playwright" 2>/dev/null || {
    echo "⚠️  缺少playwright库"
    echo "正在安装..."
    pip3 install playwright anthropic
    python3 -m playwright install chromium
}

echo "✅ 依赖检查完成"
echo ""

# 检查API Key（可选）
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  提示：未设置ANTHROPIC_API_KEY环境变量"
    echo "   将使用模板回答（质量较低）"
    echo "   建议设置API Key以获得高质量AI回答"
    echo ""
    echo "   设置方法："
    echo "   export ANTHROPIC_API_KEY='your-api-key'"
    echo ""
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo "=========================================="
echo "开始执行自动化任务..."
echo "=========================================="
echo ""

# 运行Python脚本
python3 full-auto-answer.py

echo ""
echo "=========================================="
echo "任务执行完成"
echo "=========================================="
