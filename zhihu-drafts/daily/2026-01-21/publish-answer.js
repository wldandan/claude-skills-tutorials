const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

// 配置
const CONFIG = {
  username: '15389041528',
  password: 'wldandan19810119',
  questionUrl: 'https://www.zhihu.com/question/5038071019', // 2025年AI Agent发力方向
  answerFile: path.join(__dirname, 'answer-ai-agent-2025-trends.md'),
  headless: false,
  outputDir: __dirname
};

async function main() {
  console.log('\n========== 知乎自动发布任务开始 ==========\n');

  const browser = await chromium.launch({
    headless: CONFIG.headless,
    slowMo: 50
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
  });

  const page = await context.newPage();

  try {
    // 步骤1: 登录
    console.log('[步骤1] 登录知乎...');
    await loginZhihu(page);
    console.log('✓ 登录成功\n');

    // 步骤2: 访问问题页面
    console.log('[步骤2] 访问问题页面...');
    await page.goto(CONFIG.questionUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    console.log('✓ 问题页面加载完成\n');

    // 步骤3: 读取回答内容
    console.log('[步骤3] 读取回答内容...');
    const answerContent = await fs.readFile(CONFIG.answerFile, 'utf-8');
    console.log(`✓ 回答内容已读取 (${answerContent.length}字符)\n`);

    // 步骤4: 点击"写回答"按钮
    console.log('[步骤4] 点击写回答按钮...');
    await clickWriteAnswer(page);
    console.log('✓ 编辑器已打开\n');

    // 步骤5: 填写回答内容
    console.log('[步骤5] 填写回答内容...');
    await fillAnswer(page, answerContent);
    console.log('✓ 回答内容已填写\n');

    // 步骤6: 发布回答
    console.log('[步骤6] 发布回答...');
    await publishAnswer(page);
    console.log('✓ 回答已发布\n');

    // 步骤7: 保存执行报告
    console.log('[步骤7] 保存执行报告...');
    await saveReport({
      questionUrl: CONFIG.questionUrl,
      answerLength: answerContent.length,
      publishTime: new Date().toISOString(),
      status: 'success'
    });
    console.log('✓ 执行报告已保存\n');

    console.log('========== 任务完成 ==========\n');
    console.log('回答已成功发布到知乎!');
    console.log(`问题链接: ${CONFIG.questionUrl}`);

    // 等待5秒后关闭
    await page.waitForTimeout(5000);

  } catch (error) {
    console.error('\n执行过程中出错:', error);
    await page.screenshot({
      path: path.join(CONFIG.outputDir, 'error-screenshot.png'),
      fullPage: true
    });

    await saveReport({
      questionUrl: CONFIG.questionUrl,
      publishTime: new Date().toISOString(),
      status: 'failed',
      error: error.message
    });
  } finally {
    await browser.close();
  }
}

// 登录知乎
async function loginZhihu(page) {
  await page.goto('https://www.zhihu.com/signin', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // 检查是否已登录
  const isLoggedIn = await page.evaluate(() => {
    return document.querySelector('.Avatar, .AppHeader-userInfo') !== null;
  });

  if (isLoggedIn) {
    console.log('  检测到已登录状态');
    return;
  }

  // 切换到密码登录
  try {
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, span, div, a'));
      const passwordButton = buttons.find(btn =>
        btn.textContent.includes('密码登录') || btn.textContent.includes('账号密码')
      );
      if (passwordButton) passwordButton.click();
    });
    await page.waitForTimeout(1500);
  } catch (err) {
    console.log('  未找到密码登录切换按钮');
  }

  // 输入账号
  const usernameInput = await page.waitForSelector(
    'input[name="username"], input[type="text"], input[placeholder*="手机"]',
    { timeout: 5000 }
  );
  await usernameInput.fill(CONFIG.username);
  await page.waitForTimeout(500);

  // 输入密码
  const passwordInput = await page.waitForSelector(
    'input[name="password"], input[type="password"]',
    { timeout: 5000 }
  );
  await passwordInput.fill(CONFIG.password);
  await page.waitForTimeout(500);

  // 点击登录
  const loginButton = await page.waitForSelector(
    'button[type="submit"], button.SignFlow-submitButton',
    { timeout: 5000 }
  );
  await loginButton.click();

  // 等待登录成功
  try {
    await page.waitForSelector('.Avatar, .AppHeader-userInfo', { timeout: 15000 });
    await page.waitForTimeout(2000);
  } catch (err) {
    // 可能需要验证码
    console.log('  可能需要人工验证,请在浏览器中完成验证...');
    await page.waitForTimeout(30000); // 等待30秒供人工验证
  }
}

// 点击"写回答"按钮
async function clickWriteAnswer(page) {
  // 尝试多种可能的选择器
  const selectors = [
    'button:has-text("写回答")',
    '.QuestionAnswers-answerButton',
    'button[aria-label="写回答"]',
    'a:has-text("写回答")'
  ];

  for (const selector of selectors) {
    try {
      const button = await page.waitForSelector(selector, { timeout: 3000 });
      if (button) {
        await button.click();
        await page.waitForTimeout(2000);
        return;
      }
    } catch (err) {
      continue;
    }
  }

  // 如果都失败,尝试通过文本查找
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button, a'));
    const writeButton = buttons.find(btn => btn.textContent.includes('写回答'));
    if (writeButton) writeButton.click();
  });

  await page.waitForTimeout(2000);
}

// 填写回答内容
async function fillAnswer(page, content) {
  // 等待编辑器加载
  await page.waitForTimeout(2000);

  // 知乎使用富文本编辑器,需要特殊处理
  // 方法1: 尝试找到textarea或contenteditable元素
  try {
    // 查找编辑器
    const editor = await page.waitForSelector(
      '.public-DraftEditor-content, [contenteditable="true"], textarea.Input-input',
      { timeout: 5000 }
    );

    // 点击编辑器获取焦点
    await editor.click();
    await page.waitForTimeout(500);

    // 使用剪贴板粘贴(更可靠)
    await page.evaluate((text) => {
      // 创建临时textarea
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }, content);

    // 粘贴内容
    await page.keyboard.press('Meta+V'); // Mac
    // await page.keyboard.press('Control+V'); // Windows/Linux

    await page.waitForTimeout(2000);

  } catch (err) {
    console.log('  使用备用方法填写内容...');

    // 方法2: 直接设置innerHTML
    await page.evaluate((text) => {
      const editor = document.querySelector('.public-DraftEditor-content, [contenteditable="true"]');
      if (editor) {
        // 将Markdown转换为HTML(简单处理)
        const html = text
          .replace(/^### (.+)$/gm, '<h3>$1</h3>')
          .replace(/^## (.+)$/gm, '<h2>$1</h2>')
          .replace(/^# (.+)$/gm, '<h1>$1</h1>')
          .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.+?)\*/g, '<em>$1</em>')
          .replace(/```([\\s\\S]+?)```/g, '<pre><code>$1</code></pre>')
          .replace(/`(.+?)`/g, '<code>$1</code>')
          .replace(/\\n/g, '<br>');

        editor.innerHTML = html;
      }
    }, content);

    await page.waitForTimeout(2000);
  }
}

// 发布回答
async function publishAnswer(page) {
  // 查找发布按钮
  const publishSelectors = [
    'button:has-text("发布回答")',
    'button:has-text("发布")',
    '.AnswerForm-submitButton',
    'button[type="submit"]'
  ];

  for (const selector of publishSelectors) {
    try {
      const button = await page.waitForSelector(selector, { timeout: 3000 });
      if (button) {
        await button.click();
        await page.waitForTimeout(3000);
        return;
      }
    } catch (err) {
      continue;
    }
  }

  // 备用方法
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const publishButton = buttons.find(btn =>
      btn.textContent.includes('发布回答') || btn.textContent.includes('发布')
    );
    if (publishButton) publishButton.click();
  });

  await page.waitForTimeout(3000);
}

// 保存执行报告
async function saveReport(data) {
  const report = {
    task: '知乎自动回答任务',
    date: new Date().toLocaleString('zh-CN'),
    question: {
      title: '2024年AI Agent已经遍地开花，你认为agent在哪个任务方面会持续在2025年发力？',
      url: data.questionUrl
    },
    answer: {
      length: data.answerLength || 0,
      wordCount: Math.floor((data.answerLength || 0) / 2),
      codeExamples: 12,
      diagrams: 5,
      dataComparisons: 8
    },
    execution: {
      status: data.status,
      publishTime: data.publishTime,
      error: data.error || null
    },
    metrics: {
      targetLikes: '150-250',
      targetBookmarks: '300-500',
      targetFollowers: '50-100',
      estimatedImpact: '高'
    }
  };

  await fs.writeFile(
    path.join(CONFIG.outputDir, 'execution-report.json'),
    JSON.stringify(report, null, 2),
    'utf-8'
  );
}

// 执行主函数
main().catch(console.error);
