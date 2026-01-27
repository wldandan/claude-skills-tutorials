const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

// 配置
const CONFIG = {
  username: '15389041528',
  password: 'wldandan19810119',
  searchKeywords: ['Agent', 'Prompt', 'AI Agent', 'Prompt Engineering'],
  headless: false, // 设为false以便观察登录过程
  outputDir: path.join(__dirname, '../zhihu-drafts')
};

// 确保输出目录存在
async function ensureOutputDir() {
  try {
    await fs.mkdir(CONFIG.outputDir, { recursive: true });
  } catch (err) {
    console.error('创建输出目录失败:', err);
  }
}

// 主函数
async function main() {
  await ensureOutputDir();

  const browser = await chromium.launch({
    headless: CONFIG.headless,
    slowMo: 50 // 减慢操作速度，便于观察
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });

  const page = await context.newPage();

  try {
    console.log('\n========== 步骤1: 登录知乎 ==========');
    await loginZhihu(page);

    console.log('\n========== 步骤2: 搜索热门问题 ==========');
    const questions = await searchQuestions(page);

    console.log('\n========== 步骤3: 选择最佳问题 ==========');
    const selectedQuestion = selectBestQuestion(questions);

    console.log('\n========== 步骤4: 生成回答草稿 ==========');
    const answerDraft = await generateAnswerDraft(selectedQuestion);

    console.log('\n========== 步骤5: 保存草稿到本地 ==========');
    await saveDraft(selectedQuestion, answerDraft);

    console.log('\n\n========== 任务完成 ==========');
    console.log('回答草稿已保存到:', path.join(CONFIG.outputDir, 'answer-draft.md'));
    console.log('问题信息已保存到:', path.join(CONFIG.outputDir, 'question-info.json'));
    console.log('\n请审核后确认是否发布。');

    // 保持浏览器打开，等待用户审核
    console.log('\n浏览器将保持打开状态，按Ctrl+C退出...');
    await new Promise(() => {}); // 保持运行

  } catch (error) {
    console.error('执行过程中出错:', error);
    await page.screenshot({ path: path.join(CONFIG.outputDir, 'error-screenshot.png'), fullPage: true });
  }
}

// 登录知乎
async function loginZhihu(page) {
  console.log('访问知乎登录页...');
  await page.goto('https://www.zhihu.com/signin', { waitUntil: 'networkidle' });

  // 等待页面加载
  await page.waitForTimeout(2000);

  // 检查是否已经登录
  const isLoggedIn = await page.evaluate(() => {
    return document.querySelector('.Avatar') !== null;
  });

  if (isLoggedIn) {
    console.log('检测到已登录状态');
    return;
  }

  // 切换到密码登录
  console.log('切换到密码登录方式...');
  try {
    // 尝试多种可能的选择器
    await page.waitForTimeout(2000);

    // 查找"密码登录"按钮/标签
    const switched = await page.evaluate(() => {
      // 尝试查找包含"密码"文字的元素
      const buttons = Array.from(document.querySelectorAll('button, span, div, a'));
      const passwordButton = buttons.find(btn =>
        btn.textContent.includes('密码登录') ||
        btn.textContent.includes('账号密码')
      );

      if (passwordButton) {
        passwordButton.click();
        return true;
      }

      // 尝试查找 tab 切换
      const tabs = Array.from(document.querySelectorAll('[role="tab"], .SignFlow-tab'));
      const passwordTab = tabs.find(tab =>
        tab.textContent.includes('密码') ||
        tab.getAttribute('aria-label')?.includes('密码')
      );

      if (passwordTab) {
        passwordTab.click();
        return true;
      }

      return false;
    });

    if (switched) {
      console.log('成功切换到密码登录模式');
      await page.waitForTimeout(1500);
    } else {
      console.log('未找到密码登录切换按钮，尝试直接输入');
    }
  } catch (err) {
    console.log('切换密码登录时出错:', err.message);
  }

  // 截图以便调试
  await page.screenshot({ path: path.join(CONFIG.outputDir, 'before-login.png'), fullPage: true });

  // 输入账号 - 尝试多种选择器
  console.log('输入账号...');
  try {
    const usernameInput = await page.waitForSelector(
      'input[name="username"], input[type="text"], input[placeholder*="手机"], input[placeholder*="账号"]',
      { timeout: 5000 }
    );
    await usernameInput.click();
    await usernameInput.fill('');
    await usernameInput.type(CONFIG.username, { delay: 100 });
    await page.waitForTimeout(500);
    console.log('账号输入成功');
  } catch (err) {
    console.log('账号输入失败:', err.message);
  }

  // 输入密码 - 尝试多种选择器
  console.log('输入密码...');
  try {
    const passwordInput = await page.waitForSelector(
      'input[name="password"], input[type="password"], input[placeholder*="密码"]',
      { timeout: 5000 }
    );
    await passwordInput.click();
    await passwordInput.fill('');
    await passwordInput.type(CONFIG.password, { delay: 100 });
    await page.waitForTimeout(500);
    console.log('密码输入成功');
  } catch (err) {
    console.log('密码输入失败:', err.message);
  }

  // 截图查看输入状态
  await page.screenshot({ path: path.join(CONFIG.outputDir, 'after-input.png'), fullPage: true });

  // 点击登录按钮 - 尝试多种选择器
  console.log('点击登录按钮...');
  try {
    const loginButton = await page.waitForSelector(
      'button[type="submit"], button.SignFlow-submitButton, button:has-text("登录")',
      { timeout: 5000 }
    );
    await loginButton.click();
    console.log('登录按钮已点击');
  } catch (err) {
    console.log('点击登录按钮失败:', err.message);
  }

  // 等待登录成功 - 检查是否出现用户头像或跳转到首页
  console.log('等待登录成功...');
  try {
    await page.waitForSelector('.Avatar, .AppHeader-userInfo', { timeout: 15000 });
    console.log('登录成功！');
    await page.waitForTimeout(2000);
  } catch (err) {
    // 可能需要验证码，保存截图
    await page.screenshot({ path: path.join(CONFIG.outputDir, 'login-verification.png'), fullPage: true });
    console.log('可能需要人工验证，截图已保存');
    console.log('请手动完成验证后按Enter继续...');

    // 等待用户手动完成验证
    await new Promise(resolve => {
      process.stdin.once('data', resolve);
    });
  }
}

// 搜索问题
async function searchQuestions(page) {
  const allQuestions = [];

  for (const keyword of CONFIG.searchKeywords) {
    console.log(`\n搜索关键词: ${keyword}`);

    // 访问搜索页
    const searchUrl = `https://www.zhihu.com/search?type=content&q=${encodeURIComponent(keyword)}`;
    await page.goto(searchUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // 提取问题信息
    const questions = await page.evaluate(() => {
      const results = [];
      const items = document.querySelectorAll('.List-item, .SearchResult-Card');

      items.forEach((item, index) => {
        if (index >= 10) return; // 只取前10个

        const titleElement = item.querySelector('h2 a, .ContentItem-title a');
        const linkElement = item.querySelector('a[href*="/question/"]');
        const metaElement = item.querySelector('.ContentItem-meta, .SearchItem-meta');

        if (titleElement && linkElement) {
          const title = titleElement.textContent.trim();
          const url = linkElement.href;
          const questionId = url.match(/question\/(\d+)/)?.[1];

          // 提取热度信息
          let heatScore = 0;
          const metaText = metaElement ? metaElement.textContent : '';

          // 解析关注者、回答数等
          const followMatch = metaText.match(/(\d+)\s*人关注/);
          const answerMatch = metaText.match(/(\d+)\s*个回答/);

          const followers = followMatch ? parseInt(followMatch[1]) : 0;
          const answers = answerMatch ? parseInt(answerMatch[1]) : 0;

          // 计算热度分数
          heatScore = followers * 2 + answers * 5;

          results.push({
            title,
            url,
            questionId,
            followers,
            answers,
            heatScore,
            keyword: null // 将在外部设置
          });
        }
      });

      return results;
    });

    // 设置关键词
    questions.forEach(q => q.keyword = keyword);

    console.log(`找到 ${questions.length} 个相关问题`);
    allQuestions.push(...questions);

    await page.waitForTimeout(1000);
  }

  // 按热度排序
  allQuestions.sort((a, b) => b.heatScore - a.heatScore);

  // 显示前10个
  console.log('\n热度最高的问题TOP 10:');
  allQuestions.slice(0, 10).forEach((q, i) => {
    console.log(`${i + 1}. [${q.keyword}] ${q.title}`);
    console.log(`   关注: ${q.followers} | 回答: ${q.answers} | 热度: ${q.heatScore}`);
    console.log(`   链接: ${q.url}\n`);
  });

  return allQuestions;
}

// 选择最佳问题
function selectBestQuestion(questions) {
  // 选择逻辑：
  // 1. 热度高（有一定关注和回答）
  // 2. 回答数不要太多（竞争不激烈）
  // 3. 关注数适中（有一定受众但不是超热门）

  const filtered = questions.filter(q => {
    return q.followers >= 100 && // 至少100人关注
           q.followers <= 10000 && // 不超过1万人关注（避免竞争太激烈）
           q.answers >= 5 && // 至少有5个回答（说明有价值）
           q.answers <= 200; // 不超过200个回答（避免埋没）
  });

  const selected = filtered.length > 0 ? filtered[0] : questions[0];

  console.log('\n已选择问题:');
  console.log(`标题: ${selected.title}`);
  console.log(`关键词: ${selected.keyword}`);
  console.log(`关注: ${selected.followers} | 回答: ${selected.answers}`);
  console.log(`链接: ${selected.url}`);

  return selected;
}

// 生成回答草稿（框架，实际内容需要AI生成）
async function generateAnswerDraft(question) {
  console.log('生成回答草稿框架...');

  // 这里返回一个结构化的草稿框架
  // 实际内容将由Claude AI生成
  return {
    question: question,
    metadata: {
      generatedAt: new Date().toISOString(),
      keyword: question.keyword,
      targetAudience: '技术人员、AI开发者、产品经理'
    },
    structure: {
      tldr: '待AI生成 - TL;DR 简短摘要（2-3句话概括核心观点）',
      introduction: '待AI生成 - 引言（吸引读者，阐述问题价值）',
      mainContent: [
        {
          section: '理论基础',
          content: '待AI生成 - Agent/Prompt的核心概念和原理'
        },
        {
          section: '技术实现',
          content: '待AI生成 - 具体的技术方案和代码示例'
        },
        {
          section: '最佳实践',
          content: '待AI生成 - 实际应用中的经验和建议'
        },
        {
          section: '案例分析',
          content: '待AI生成 - 真实案例或实验数据'
        }
      ],
      conclusion: '待AI生成 - 总结和行动建议',
      references: '待AI生成 - 参考资料和延伸阅读'
    },
    notes: [
      '字数要求: 1500-3000字',
      '包含至少2-3个代码示例',
      '使用Markdown格式',
      '技术深度与可读性平衡',
      '结合实际案例和数据支撑'
    ]
  };
}

// 保存草稿
async function saveDraft(question, draft) {
  // 保存问题信息
  await fs.writeFile(
    path.join(CONFIG.outputDir, 'question-info.json'),
    JSON.stringify(question, null, 2),
    'utf-8'
  );

  // 保存草稿框架
  const draftContent = `# 知乎回答草稿

## 问题信息
- **标题**: ${question.title}
- **链接**: ${question.url}
- **关键词**: ${question.keyword}
- **关注人数**: ${question.followers}
- **回答数**: ${question.answers}
- **生成时间**: ${new Date().toLocaleString('zh-CN')}

---

## 回答框架

### TL;DR
${draft.structure.tldr}

---

### 引言
${draft.structure.introduction}

---

### 主要内容

#### 1. 理论基础
${draft.structure.mainContent[0].content}

#### 2. 技术实现
${draft.structure.mainContent[1].content}

#### 3. 最佳实践
${draft.structure.mainContent[2].content}

#### 4. 案例分析
${draft.structure.mainContent[3].content}

---

### 总结
${draft.structure.conclusion}

---

### 参考资料
${draft.structure.references}

---

## 写作要求
${draft.notes.map(note => `- ${note}`).join('\n')}

---

## 待办事项
- [ ] 使用Claude AI生成具体内容
- [ ] 添加代码示例和技术细节
- [ ] 补充数据支撑和案例分析
- [ ] 优化语言表达和逻辑结构
- [ ] 审核并确认后发布
`;

  await fs.writeFile(
    path.join(CONFIG.outputDir, 'answer-draft.md'),
    draftContent,
    'utf-8'
  );

  console.log('草稿已保存');
}

// 执行主函数
main().catch(console.error);
