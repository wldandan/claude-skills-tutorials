const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

/**
 * 获取知乎专栏文章内容
 * 
 * 使用方法:
 * ZHIHU_USERNAME=your_username ZHIHU_PASSWORD=your_password node scripts/fetch-zhuanlan-article.js
 * 
 * 或者直接修改下面的 CONFIG 对象
 */

const CONFIG = {
  username: process.env.ZHIHU_USERNAME || '',
  password: process.env.ZHIHU_PASSWORD || '',
  articleUrl: 'https://zhuanlan.zhihu.com/p/694428893',
  outputDir: path.join(__dirname, '../zhihu-drafts'),
  headless: false, // 设为false以便观察和手动处理验证码
  waitForManualVerification: true // 如果需要手动验证，设为true
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
  if (!CONFIG.username || !CONFIG.password) {
    console.error('错误: 请设置用户名和密码');
    console.log('方法1: 设置环境变量');
    console.log('  export ZHIHU_USERNAME=your_username');
    console.log('  export ZHIHU_PASSWORD=your_password');
    console.log('  node scripts/fetch-zhuanlan-article.js');
    console.log('\n方法2: 直接修改脚本中的 CONFIG 对象');
    process.exit(1);
  }

  await ensureOutputDir();

  console.log('\n========== 开始获取专栏文章 ==========');
  console.log(`文章URL: ${CONFIG.articleUrl}`);
  console.log(`输出目录: ${CONFIG.outputDir}\n`);

  const browser = await chromium.launch({
    headless: CONFIG.headless,
    slowMo: 100 // 减慢操作速度
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });

  const page = await context.newPage();

  try {
    // 步骤1: 登录
    console.log('步骤1: 登录知乎...');
    await loginZhihu(page);

    // 步骤2: 访问专栏文章
    console.log('\n步骤2: 访问专栏文章...');
    await page.goto(CONFIG.articleUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // 步骤3: 提取文章内容
    console.log('步骤3: 提取文章内容...');
    const articleContent = await extractArticleContent(page);

    // 步骤4: 保存内容
    console.log('步骤4: 保存文章内容...');
    await saveArticleContent(articleContent);

    console.log('\n========== 任务完成 ==========');
    console.log(`文章已保存到: ${path.join(CONFIG.outputDir, 'zhuanlan-article-694428893.md')}`);
    console.log(`文章元数据已保存到: ${path.join(CONFIG.outputDir, 'zhuanlan-article-meta.json')}`);

    // 保持浏览器打开一段时间，让用户查看
    console.log('\n浏览器将保持打开10秒，您可以查看页面...');
    await page.waitForTimeout(10000);

  } catch (error) {
    console.error('执行过程中出错:', error);
    await page.screenshot({ 
      path: path.join(CONFIG.outputDir, 'error-screenshot.png'), 
      fullPage: true 
    });
    console.log('错误截图已保存');
  } finally {
    await browser.close();
  }
}

// 登录知乎
async function loginZhihu(page) {
  console.log('访问知乎登录页...');
  await page.goto('https://www.zhihu.com/signin', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // 检查是否已经登录
  const isLoggedIn = await page.evaluate(() => {
    return document.querySelector('.Avatar, .AppHeader-userInfo') !== null;
  });

  if (isLoggedIn) {
    console.log('检测到已登录状态');
    return;
  }

  // 切换到密码登录
  console.log('切换到密码登录方式...');
  try {
    await page.waitForTimeout(1000);
    
    const switched = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, span, div, a'));
      const passwordButton = buttons.find(btn =>
        btn.textContent.includes('密码登录') ||
        btn.textContent.includes('账号密码')
      );

      if (passwordButton) {
        passwordButton.click();
        return true;
      }

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
    }
  } catch (err) {
    console.log('切换密码登录时出错:', err.message);
  }

  // 输入账号
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
    throw err;
  }

  // 输入密码
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
    throw err;
  }

  // 点击登录按钮
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
    throw err;
  }

  // 等待登录成功
  console.log('等待登录成功...');
  try {
    await page.waitForSelector('.Avatar, .AppHeader-userInfo', { timeout: 15000 });
    console.log('登录成功！');
    await page.waitForTimeout(2000);
  } catch (err) {
    // 可能需要验证码
    await page.screenshot({ 
      path: path.join(CONFIG.outputDir, 'login-verification.png'), 
      fullPage: true 
    });
    console.log('可能需要人工验证，截图已保存到 login-verification.png');
    
    if (CONFIG.waitForManualVerification) {
      console.log('请手动完成验证后，在终端按Enter继续...');
      await new Promise(resolve => {
        process.stdin.once('data', resolve);
      });
      
      // 再次检查登录状态
      const loggedIn = await page.evaluate(() => {
        return document.querySelector('.Avatar, .AppHeader-userInfo') !== null;
      });
      
      if (!loggedIn) {
        throw new Error('登录失败，请检查用户名和密码');
      }
      console.log('登录验证完成！');
    } else {
      throw new Error('需要手动验证，但 waitForManualVerification 为 false');
    }
  }
}

// 提取文章内容
async function extractArticleContent(page) {
  const content = await page.evaluate(() => {
    // 提取标题
    const titleElement = document.querySelector('.Post-Title, h1.PostIndex-title, .ColumnPost-Title');
    const title = titleElement ? titleElement.textContent.trim() : '';

    // 提取作者信息
    const authorElement = document.querySelector('.AuthorInfo-name, .Post-Author .UserLink-link');
    const author = authorElement ? authorElement.textContent.trim() : '';

    // 提取发布时间
    const timeElement = document.querySelector('.Post-Time, time[datetime], .ContentItem-time');
    const publishTime = timeElement ? 
      (timeElement.getAttribute('datetime') || timeElement.textContent.trim()) : '';

    // 提取文章正文
    const contentElement = document.querySelector(
      '.Post-RichText, .PostContent, .RichContent-inner, article'
    );
    
    let articleBody = '';
    if (contentElement) {
      // 提取所有段落
      const paragraphs = contentElement.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, blockquote');
      articleBody = Array.from(paragraphs)
        .map(p => {
          const text = p.textContent.trim();
          const tagName = p.tagName.toLowerCase();
          
          // 处理标题
          if (tagName.startsWith('h')) {
            const level = parseInt(tagName[1]);
            const prefix = '#'.repeat(level) + ' ';
            return prefix + text;
          }
          
          // 处理列表
          if (tagName === 'li') {
            return '- ' + text;
          }
          
          // 处理引用
          if (tagName === 'blockquote') {
            return '> ' + text;
          }
          
          return text;
        })
        .filter(text => text.length > 0)
        .join('\n\n');
    }

    // 提取图片（如果有）
    const images = Array.from(document.querySelectorAll('.Post-RichText img, .RichContent-inner img'))
      .map(img => img.src || img.getAttribute('data-src'))
      .filter(src => src && !src.includes('data:image'));

    // 提取标签/话题
    const tags = Array.from(document.querySelectorAll('.Tag, .Topic'))
      .map(tag => tag.textContent.trim())
      .filter(tag => tag.length > 0);

    // 提取阅读数、点赞数等统计信息
    const stats = {};
    const statsElements = document.querySelectorAll('[class*="Count"], [class*="count"]');
    statsElements.forEach(el => {
      const text = el.textContent.trim();
      if (text.includes('赞')) {
        stats.likes = text;
      } else if (text.includes('评论')) {
        stats.comments = text;
      } else if (text.includes('收藏')) {
        stats.collections = text;
      }
    });

    return {
      title,
      author,
      publishTime,
      content: articleBody,
      images,
      tags,
      stats,
      url: window.location.href
    };
  });

  return content;
}

// 保存文章内容
async function saveArticleContent(article) {
  // 保存为Markdown格式
  const markdown = `# ${article.title}

**作者**: ${article.author}
**发布时间**: ${article.publishTime}
**原文链接**: ${article.url}

${article.stats.likes ? `**${article.stats.likes}** | ` : ''}${article.stats.comments ? `**${article.stats.comments}** | ` : ''}${article.stats.collections ? `**${article.stats.collections}**` : ''}

${article.tags.length > 0 ? `**标签**: ${article.tags.join(', ')}\n\n` : ''}

---

## 正文

${article.content}

${article.images.length > 0 ? `\n\n## 图片\n\n${article.images.map((img, i) => `![图片${i + 1}](${img})`).join('\n\n')}` : ''}

---

**提取时间**: ${new Date().toLocaleString('zh-CN')}
`;

  // 保存Markdown文件
  await fs.writeFile(
    path.join(CONFIG.outputDir, 'zhuanlan-article-694428893.md'),
    markdown,
    'utf-8'
  );

  // 保存元数据JSON
  await fs.writeFile(
    path.join(CONFIG.outputDir, 'zhuanlan-article-meta.json'),
    JSON.stringify(article, null, 2),
    'utf-8'
  );
}

// 执行主函数
main().catch(console.error);


