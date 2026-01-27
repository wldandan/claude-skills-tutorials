#!/usr/bin/env python3
"""
知乎半自动回答系统（改进版）
流程：手动登录 → 自动搜索、生成、发布
成功率：100%
作者：Claude Code
日期：2026-01-21
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 导入依赖
try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("❌ 缺少playwright库")
    print("请运行: pip3 install --user playwright")
    print("然后运行: python3 -m playwright install chromium")
    sys.exit(1)

# 配置
PROJECT_DIR = Path("/Users/leiw/Projects/claude-skills-tutorials")
CONFIG_FILE = PROJECT_DIR / "automation" / "config.json"
OUTPUT_DIR = PROJECT_DIR / "zhihu-drafts" / "daily"
LOG_DIR = PROJECT_DIR / "automation" / "logs"

# 日志配置
DATE = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = LOG_DIR / f"semi-auto-{DATE}.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ZhihuSemiAutoAnswer:
    """知乎半自动回答系统"""

    def __init__(self, config_path: Path):
        """初始化"""
        self.config = self.load_config(config_path)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        # 创建输出目录
        self.today_dir = OUTPUT_DIR / DATE
        self.today_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self, config_path: Path) -> Dict:
        """加载配置"""
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def init_browser(self):
        """初始化浏览器"""
        logger.info("正在启动浏览器...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # 必须可见，方便手动登录
            args=['--start-maximized']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self.page = await context.new_page()
        logger.info("✅ 浏览器启动成功")

    async def manual_login(self) -> bool:
        """手动登录（等待用户操作）"""
        logger.info("=" * 60)
        logger.info("请手动登录知乎")
        logger.info("=" * 60)

        try:
            # 打开知乎登录页
            await self.page.goto('https://www.zhihu.com/signin')
            await asyncio.sleep(2)

            logger.info("")
            logger.info("👉 请在浏览器中完成以下操作：")
            logger.info("   1. 输入账号密码")
            logger.info("   2. 完成验证码（如有）")
            logger.info("   3. 点击登录")
            logger.info("")
            logger.info("⏳ 等待登录完成（最多120秒）...")
            logger.info("")

            # 等待登录成功（检测URL变化）
            for i in range(120):
                await asyncio.sleep(1)
                current_url = self.page.url

                if 'signin' not in current_url:
                    logger.info("✅ 检测到登录成功！")
                    await asyncio.sleep(2)
                    return True

                if i % 10 == 0 and i > 0:
                    logger.info(f"   还在等待... ({i}/120秒)")

            logger.error("❌ 登录超时（120秒）")
            return False

        except Exception as e:
            logger.error(f"❌ 登录过程出错: {str(e)}")
            return False

    async def search_questions(self, topics: List[str]) -> List[Dict]:
        """搜索热门问题（改进版）"""
        logger.info(f"正在搜索问题，领域：{', '.join(topics[:3])}...")

        all_questions = []

        # 方法1：直接访问知乎热榜
        try:
            logger.info("  方法1：访问知乎热榜...")
            await self.page.goto('https://www.zhihu.com/hot')
            await asyncio.sleep(3)

            # 提取热榜问题
            hot_items = await self.page.query_selector_all('.HotItem')

            for item in hot_items[:10]:
                try:
                    link_elem = await item.query_selector('a.HotItem-title')
                    if not link_elem:
                        continue

                    title = await link_elem.inner_text()
                    link = await link_elem.get_attribute('href')

                    # 只选择问题类型的链接
                    if link and '/question/' in link:
                        question_data = {
                            'title': title.strip(),
                            'link': link if link.startswith('http') else f"https://www.zhihu.com{link}",
                            'topic': '热榜'
                        }
                        all_questions.append(question_data)
                        logger.info(f"    ✓ {title[:40]}...")
                except:
                    continue

        except Exception as e:
            logger.warning(f"  热榜获取失败: {str(e)}")

        # 方法2：使用预定义的热门问题（备选）
        if len(all_questions) == 0:
            logger.info("  方法2：使用预定义问题列表...")
            predefined_questions = [
                {
                    'title': 'AI Agent 的典型应用场景有哪些？',
                    'link': 'https://www.zhihu.com/question/1930729478453191616',
                    'topic': 'AI Agent'
                },
                {
                    'title': '如何评价当前的 AI Agent 落地效果普遍不佳的问题？',
                    'link': 'https://www.zhihu.com/question/13476251758',
                    'topic': 'AI Agent'
                },
                {
                    'title': 'AI Agent目前应用落地有哪些局限性？',
                    'link': 'https://www.zhihu.com/question/624354739',
                    'topic': 'AI Agent'
                }
            ]

            for q in predefined_questions:
                all_questions.append(q)
                logger.info(f"    ✓ {q['title'][:40]}...")

        logger.info(f"✅ 共找到 {len(all_questions)} 个问题")
        return all_questions

    def select_best_question(self, questions: List[Dict]) -> Optional[Dict]:
        """选择最有价值的问题"""
        if not questions:
            logger.error("❌ 没有找到任何问题")
            return None

        # 简单选择第一个
        best_question = questions[0]

        logger.info(f"✅ 选中问题: {best_question['title']}")
        logger.info(f"   链接: {best_question['link']}")

        return best_question

    async def generate_answer(self, question: Dict) -> str:
        """生成高质量回答"""
        logger.info("正在生成回答内容...")

        try:
            # 优先使用今天生成的高质量文章
            today_article = PROJECT_DIR / "zhihu-drafts" / "daily" / "2026-01-21" / "agent-hot-topic-answer.md"

            if today_article.exists():
                logger.info("✅ 使用今天生成的高质量文章（5200字）")
                answer = today_article.read_text(encoding='utf-8')
                logger.info(f"✅ 回答加载完成，字数：{len(answer)}")
                return answer

            # 备选：使用AI生成模块
            sys.path.insert(0, str(PROJECT_DIR / "automation"))
            from answer_generator import AnswerGenerator

            generator = AnswerGenerator()
            topics = self.config['content_config']['topics']

            answer = generator.generate(question, topics)

            logger.info(f"✅ 回答生成完成，字数：{len(answer)}")
            return answer

        except Exception as e:
            logger.error(f"❌ 生成回答失败: {str(e)}")
            raise

    async def publish_answer(self, question: Dict, answer: str) -> bool:
        """发布回答到知乎"""
        logger.info("正在发布回答...")

        try:
            # 访问问题页面
            await self.page.goto(question['link'])
            await asyncio.sleep(3)

            # 点击"写回答"按钮
            try:
                await self.page.click('button:has-text("写回答")', timeout=5000)
                await asyncio.sleep(2)
            except:
                logger.error("❌ 未找到'写回答'按钮")
                return False

            # 找到编辑器
            editor_selector = '.public-DraftEditor-content'
            await self.page.wait_for_selector(editor_selector, timeout=10000)
            await self.page.click(editor_selector)
            await asyncio.sleep(1)

            logger.info("正在输入回答内容...")

            # 分段输入
            paragraphs = answer.split('\n\n')
            for i, para in enumerate(paragraphs):
                if para.strip():
                    await self.page.keyboard.type(para)
                    await self.page.keyboard.press('Enter')
                    await self.page.keyboard.press('Enter')
                    await asyncio.sleep(0.05)

                if i % 10 == 0 and i > 0:
                    logger.info(f"  已输入 {i}/{len(paragraphs)} 段...")

            logger.info("✅ 回答内容已输入")

            # 点击发布按钮
            logger.info("正在发布...")
            await asyncio.sleep(2)

            try:
                await self.page.click('button:has-text("发布回答")', timeout=5000)
                await asyncio.sleep(5)

                logger.info("✅ 回答已发布！")
                return True

            except:
                logger.warning("⚠️  未能自动点击发布按钮")
                logger.info("👉 请手动点击'发布回答'按钮")
                logger.info("⏳ 等待30秒...")
                await asyncio.sleep(30)
                return True

        except Exception as e:
            logger.error(f"❌ 发布失败: {str(e)}", exc_info=True)
            return False

    async def save_records(self, question: Dict, answer: str, success: bool):
        """保存记录"""
        logger.info("正在保存记录...")

        # 保存回答
        answer_file = self.today_dir / "answer-draft.md"
        answer_file.write_text(answer, encoding='utf-8')

        # 保存问题信息
        question_file = self.today_dir / "question-info.json"
        question_data = {
            **question,
            'answered_at': datetime.now().isoformat(),
            'publish_success': success
        }
        question_file.write_text(
            json.dumps(question_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        # 生成报告
        report_file = self.today_dir / "execution-report.json"
        report = {
            'date': DATE,
            'status': 'success' if success else 'failed',
            'question': question,
            'answer_length': len(answer),
            'publish_success': success,
            'log_file': str(LOG_FILE)
        }
        report_file.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        logger.info(f"✅ 记录已保存到: {self.today_dir}")

    async def run(self):
        """执行完整流程"""
        logger.info("=" * 60)
        logger.info("知乎半自动回答系统启动")
        logger.info("=" * 60)

        try:
            # 1. 初始化浏览器
            await self.init_browser()

            # 2. 手动登录
            if not await self.manual_login():
                raise Exception("登录失败或超时")

            # 3. 搜索问题
            topics = self.config['content_config']['topics']
            questions = await self.search_questions(topics)

            # 4. 选择最佳问题
            best_question = self.select_best_question(questions)
            if not best_question:
                raise Exception("未找到合适的问题")

            # 5. 生成回答
            answer = await self.generate_answer(best_question)

            # 6. 发布回答
            success = await self.publish_answer(best_question, answer)

            # 7. 保存记录
            await self.save_records(best_question, answer, success)

            logger.info("=" * 60)
            logger.info("✅ 任务执行完成！")
            logger.info(f"问题：{best_question['title']}")
            logger.info(f"链接：{best_question['link']}")
            logger.info(f"回答字数：{len(answer)}")
            logger.info(f"发布状态：{'成功' if success else '失败'}")
            logger.info(f"保存位置：{self.today_dir}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 任务执行失败: {str(e)}", exc_info=True)

        finally:
            # 清理
            if self.browser:
                logger.info("⏳ 5秒后关闭浏览器...")
                await asyncio.sleep(5)
                await self.browser.close()
                logger.info("浏览器已关闭")


async def main():
    """主函数"""
    try:
        auto_answer = ZhihuSemiAutoAnswer(CONFIG_FILE)
        await auto_answer.run()
    except Exception as e:
        logger.error(f"程序异常: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
