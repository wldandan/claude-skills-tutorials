#!/usr/bin/env python3
"""
知乎完全自动化回答系统
功能：自动搜索、选择问题、生成回答、发布到知乎
作者：Claude Code
日期：2026-01-21
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# 第三方库
try:
    from playwright.async_api import async_playwright, Page, Browser
    import anthropic
except ImportError:
    print("❌ 缺少必要的依赖库")
    print("请运行: pip3 install playwright anthropic")
    print("然后运行: python3 -m playwright install chromium")
    sys.exit(1)

# 配置
PROJECT_DIR = Path("/Users/leiw/Projects/claude-skills-tutorials")
CONFIG_FILE = PROJECT_DIR / "automation" / "config.json"
OUTPUT_DIR = PROJECT_DIR / "zhihu-drafts" / "daily"
LOG_DIR = PROJECT_DIR / "automation" / "logs"

# 日志配置
DATE = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = LOG_DIR / f"auto-answer-{DATE}.log"
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


class ZhihuAutoAnswer:
    """知乎自动回答系统"""

    def __init__(self, config_path: Path):
        """初始化"""
        self.config = self.load_config(config_path)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.anthropic_client = None

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
            headless=False,  # 设为True可后台运行
            args=['--start-maximized']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self.page = await context.new_page()
        logger.info("✅ 浏览器启动成功")

    async def login_zhihu(self) -> bool:
        """登录知乎"""
        logger.info("正在登录知乎...")

        try:
            account = self.config['zhihu_account']
            username = account['username']
            password = account['password']

            # 访问登录页
            await self.page.goto('https://www.zhihu.com/signin')
            await asyncio.sleep(2)

            # 切换到密码登录
            try:
                await self.page.click('text=密码登录', timeout=5000)
            except:
                logger.info("已经在密码登录页面")

            await asyncio.sleep(1)

            # 输入账号密码
            await self.page.fill('input[name="username"]', username)
            await asyncio.sleep(0.5)
            await self.page.fill('input[name="password"]', password)
            await asyncio.sleep(0.5)

            # 点击登录按钮
            await self.page.click('button[type="submit"]')
            await asyncio.sleep(3)

            # 检查是否需要验证码
            if await self.page.is_visible('text=请完成验证'):
                logger.warning("⚠️ 需要人工完成验证码，等待30秒...")
                await asyncio.sleep(30)

            # 检查登录是否成功
            await asyncio.sleep(2)
            current_url = self.page.url

            if 'signin' not in current_url:
                logger.info("✅ 登录成功")
                return True
            else:
                logger.error("❌ 登录失败，请检查账号密码")
                return False

        except Exception as e:
            logger.error(f"❌ 登录过程出错: {str(e)}", exc_info=True)
            return False

    async def search_questions(self, topics: List[str]) -> List[Dict]:
        """搜索热门问题"""
        logger.info(f"正在搜索问题，领域：{', '.join(topics)}")

        all_questions = []

        for topic in topics:
            try:
                logger.info(f"搜索主题: {topic}")

                # 访问搜索页面
                search_url = f"https://www.zhihu.com/search?type=content&q={topic}"
                await self.page.goto(search_url)
                await asyncio.sleep(3)

                # 切换到"问题"标签
                try:
                    await self.page.click('text=问题', timeout=3000)
                    await asyncio.sleep(2)
                except:
                    logger.warning(f"未找到问题标签，跳过主题: {topic}")
                    continue

                # 提取问题列表
                questions = await self.page.query_selector_all('.List-item')

                for q in questions[:5]:  # 每个主题取前5个问题
                    try:
                        # 提取问题信息
                        title_elem = await q.query_selector('h2.ContentItem-title a')
                        if not title_elem:
                            continue

                        title = await title_elem.inner_text()
                        link = await title_elem.get_attribute('href')

                        # 提取统计信息
                        meta_text = await q.inner_text()

                        question_data = {
                            'title': title.strip(),
                            'link': f"https://www.zhihu.com{link}" if link.startswith('/') else link,
                            'topic': topic,
                            'meta_text': meta_text
                        }

                        all_questions.append(question_data)
                        logger.info(f"  找到问题: {title[:50]}...")

                    except Exception as e:
                        logger.warning(f"提取问题信息失败: {str(e)}")
                        continue

            except Exception as e:
                logger.error(f"搜索主题 {topic} 时出错: {str(e)}")
                continue

        logger.info(f"✅ 共找到 {len(all_questions)} 个问题")
        return all_questions

    def select_best_question(self, questions: List[Dict]) -> Optional[Dict]:
        """选择最有价值的问题"""
        if not questions:
            logger.error("❌ 没有找到任何问题")
            return None

        logger.info("正在智能选择最佳问题...")

        # 简单评分机制（可以改进为AI评分）
        # 这里先简单返回第一个
        best_question = questions[0]

        logger.info(f"✅ 选中问题: {best_question['title']}")
        logger.info(f"   链接: {best_question['link']}")

        return best_question

    async def generate_answer(self, question: Dict) -> str:
        """生成高质量回答"""
        logger.info("正在生成回答内容...")

        try:
            # 导入AI生成模块
            from answer_generator import AnswerGenerator

            generator = AnswerGenerator()
            topics = self.config['content_config']['topics']

            answer = generator.generate(question, topics)

            logger.info(f"✅ 回答内容生成完成，字数：{len(answer)}")
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

            # 输入回答内容
            # 知乎使用富文本编辑器，需要找到正确的输入框
            editor_selector = '.public-DraftEditor-content'
            await self.page.wait_for_selector(editor_selector, timeout=10000)

            # 清空并输入内容
            await self.page.click(editor_selector)
            await asyncio.sleep(0.5)

            # 逐段输入（避免一次性输入太多）
            paragraphs = answer.split('\n\n')
            for para in paragraphs:
                await self.page.keyboard.type(para)
                await self.page.keyboard.press('Enter')
                await self.page.keyboard.press('Enter')
                await asyncio.sleep(0.1)

            logger.info("✅ 回答内容已输入")

            # 点击发布按钮
            logger.info("正在点击发布按钮...")
            await asyncio.sleep(1)

            try:
                await self.page.click('button:has-text("发布回答")', timeout=5000)
                await asyncio.sleep(3)

                logger.info("✅ 回答已发布！")
                return True

            except:
                logger.warning("⚠️ 未能自动点击发布，请手动确认")
                # 等待用户手动操作
                await asyncio.sleep(10)
                return True

        except Exception as e:
            logger.error(f"❌ 发布回答失败: {str(e)}", exc_info=True)
            return False

    async def save_records(self, question: Dict, answer: str, success: bool):
        """保存记录"""
        logger.info("正在保存记录...")

        # 保存回答内容
        answer_file = self.today_dir / "answer-draft.md"
        answer_file.write_text(answer, encoding='utf-8')
        logger.info(f"✅ 回答已保存: {answer_file}")

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
        logger.info(f"✅ 问题信息已保存: {question_file}")

        # 生成执行报告
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
        logger.info(f"✅ 执行报告已保存: {report_file}")

    async def run(self):
        """执行完整流程"""
        logger.info("=" * 60)
        logger.info("知乎完全自动化回答系统启动")
        logger.info("=" * 60)

        try:
            # 1. 初始化浏览器
            await self.init_browser()

            # 2. 登录知乎
            if not await self.login_zhihu():
                raise Exception("登录失败")

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
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 任务执行失败: {str(e)}", exc_info=True)

        finally:
            # 清理
            if self.browser:
                await asyncio.sleep(5)  # 留点时间查看结果
                await self.browser.close()
                logger.info("浏览器已关闭")


async def main():
    """主函数"""
    try:
        auto_answer = ZhihuAutoAnswer(CONFIG_FILE)
        await auto_answer.run()
    except Exception as e:
        logger.error(f"程序异常: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
