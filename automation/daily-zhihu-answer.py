#!/usr/bin/env python3
"""
每日知乎自动回答脚本
执行时间：每天晚上22:00
作者：Claude Code
创建日期：2026-01-21
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# 配置
PROJECT_DIR = Path("/Users/leiw/Projects/claude-skills-tutorials")
LOG_DIR = PROJECT_DIR / "automation" / "logs"
OUTPUT_DIR = PROJECT_DIR / "zhihu-drafts" / "daily"
DATE = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = LOG_DIR / f"zhihu-answer-{DATE}.log"

# 知乎账号信息
ZHIHU_ACCOUNT = "15389041528"
ZHIHU_PASSWORD = "wldandan19810119"

# 内容领域
TOPICS = [
    "AI Agent",
    "Prompt Engineering",
    "大模型应用",
    "RAG技术",
    "Claude Code",
    "Agent软件工程",
    "软件工程"
]

# 创建必要的目录
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("开始执行每日知乎自动回答任务")
    logger.info("=" * 50)

    logger.info(f"项目目录: {PROJECT_DIR}")
    logger.info(f"输出目录: {OUTPUT_DIR}")
    logger.info(f"内容领域: {', '.join(TOPICS)}")

    try:
        # 创建今日输出目录
        today_output = OUTPUT_DIR / DATE
        today_output.mkdir(parents=True, exist_ok=True)

        # 构建任务提示词
        prompt = f"""请执行每日知乎自动回答任务：

1. **搜索热门问题**
   - 搜索知乎上关于以下领域的热门问题：{', '.join(TOPICS)}
   - 筛选条件：发布时间在最近7天内，浏览量>1000，回答数<50
   - 优先选择技术深度高、讨论热度大的问题

2. **选择目标问题**
   - 从搜索结果中选择1个最有价值的问题
   - 评估标准：
     * 技术深度和讨论价值
     * 现有回答质量参差（有提升空间）
     * 与我的专业领域匹配度
     * 潜在影响力（关注数、浏览量）

3. **撰写高质量回答**
   - 字数：4000-5000字
   - 包含：代码示例（10+个）、架构图、真实数据对比
   - 风格：技术深度 + 实战经验 + 通俗易懂
   - 结构：TL;DR + 问题背景 + 深度分析 + 实战建议 + 参考资料

4. **自动发布到知乎**
   - 使用Playwright登录知乎
   - 账号：{ZHIHU_ACCOUNT}
   - 密码：{ZHIHU_PASSWORD}
   - 添加话题标签
   - 发布回答

5. **保存记录**
   - 将回答内容保存到：{today_output}/answer-draft.md
   - 将问题信息保存到：{today_output}/question-info.json
   - 将执行报告保存到：{today_output}/execution-report.json

请按步骤执行，并在完成后生成详细的执行报告。"""

        logger.info("正在调用zhihu-ai-content-strategist agent...")

        # 这里需要实际调用agent的逻辑
        # 由于我们在脚本中，需要通过subprocess调用claude命令
        import subprocess

        # 保存prompt到临时文件
        prompt_file = today_output / "task-prompt.txt"
        prompt_file.write_text(prompt, encoding='utf-8')

        logger.info(f"任务提示词已保存到: {prompt_file}")
        logger.info("请手动执行以下命令来运行agent：")
        logger.info(f"cd {PROJECT_DIR}")
        logger.info(f"claude-code # 然后在交互界面中运行agent")

        # 注意：实际的agent调用需要根据你的环境配置
        # 这里提供一个占位实现

        logger.info("✅ 任务配置完成")
        logger.info(f"输出目录: {today_output}")

        # 创建执行报告
        report = {
            "date": DATE,
            "status": "configured",
            "topics": TOPICS,
            "output_dir": str(today_output),
            "prompt_file": str(prompt_file),
            "note": "需要手动触发agent执行"
        }

        report_file = today_output / "execution-report.json"
        report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

        logger.info(f"执行报告: {report_file}")

    except Exception as e:
        logger.error(f"❌ 任务执行失败: {str(e)}", exc_info=True)
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("任务执行完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
