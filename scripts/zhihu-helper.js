const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

/**
 * 知乎助手 - 简化版
 *
 * 使用说明：
 * 1. 手动在浏览器中登录知乎
 * 2. 运行此脚本，会打开浏览器
 * 3. 在打开的浏览器中手动搜索问题
 * 4. 脚本会提取问题列表供选择
 * 5. 生成回答草稿框架
 */

const CONFIG = {
  outputDir: path.join(__dirname, '../zhihu-drafts'),
  headless: false
};

// 确保输出目录存在
async function ensureOutputDir() {
  try {
    await fs.mkdir(CONFIG.outputDir, { recursive: true });
  } catch (err) {
    console.error('创建输出目录失败:', err);
  }
}

async function main() {
  await ensureOutputDir();

  console.log('\n========================================');
  console.log('知乎助手 - 简化工作流');
  console.log('========================================\n');

  const browser = await chromium.launch({
    headless: CONFIG.headless,
    slowMo: 50
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });

  const page = await context.newPage();

  try {
    console.log('步骤1: 打开知乎首页');
    await page.goto('https://www.zhihu.com', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    console.log('\n请在打开的浏览器中：');
    console.log('1. 登录知乎账号（如未登录）');
    console.log('2. 搜索关键词 "Agent" 或 "Prompt" 或 "AI Agent"');
    console.log('3. 完成后回到终端，按Enter继续...\n');

    // 等待用户手动操作
    await waitForUserInput();

    console.log('\n步骤2: 提取当前页面的问题列表');
    const questions = await extractQuestions(page);

    if (questions.length === 0) {
      console.log('未找到问题，请确保您在搜索结果页面');
      return;
    }

    console.log(`\n找到 ${questions.length} 个问题:\n`);
    questions.forEach((q, i) => {
      console.log(`${i + 1}. ${q.title}`);
      console.log(`   关注: ${q.followers || '未知'} | 回答: ${q.answers || '未知'}`);
      console.log(`   ${q.url}\n`);
    });

    console.log('请输入要回答的问题编号（1-' + questions.length + '），按Enter确认:');
    const selectedIndex = await getUserChoice(questions.length);

    const selectedQuestion = questions[selectedIndex];

    console.log('\n已选择问题:');
    console.log(`标题: ${selectedQuestion.title}`);
    console.log(`链接: ${selectedQuestion.url}\n`);

    // 访问问题页面获取更多信息
    console.log('正在访问问题页面...');
    await page.goto(selectedQuestion.url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 获取问题详情
    const questionDetail = await getQuestionDetail(page, selectedQuestion);

    console.log('\n问题详情:');
    console.log(JSON.stringify(questionDetail, null, 2));

    // 生成回答草稿
    console.log('\n步骤3: 生成回答草稿框架');
    await generateAndSaveDraft(questionDetail);

    console.log('\n========================================');
    console.log('草稿已保存！');
    console.log('位置:', path.join(CONFIG.outputDir, 'answer-draft.md'));
    console.log('========================================\n');

    console.log('浏览器将保持打开，您可以查看问题详情。按Ctrl+C退出。');
    await new Promise(() => {}); // 保持运行

  } catch (error) {
    console.error('执行出错:', error);
  }
}

// 提取问题列表
async function extractQuestions(page) {
  return await page.evaluate(() => {
    const results = [];

    // 尝试多种选择器以适应不同页面结构
    const selectors = [
      '.List-item',
      '.SearchResult-Card',
      '[class*="SearchResult"]',
      'div[data-za-detail-view-path-module*="SearchResult"]'
    ];

    let items = [];
    for (const selector of selectors) {
      items = Array.from(document.querySelectorAll(selector));
      if (items.length > 0) break;
    }

    items.forEach(item => {
      // 查找标题和链接
      const titleElement = item.querySelector('h2 a, .ContentItem-title a, a[href*="/question/"]');

      if (titleElement && titleElement.href.includes('/question/')) {
        const title = titleElement.textContent.trim();
        const url = titleElement.href;
        const questionId = url.match(/question\/(\d+)/)?.[1];

        // 提取元数据
        const metaElement = item.querySelector('.ContentItem-meta, .SearchItem-meta, [class*="Meta"]');
        const metaText = metaElement ? metaElement.textContent : '';

        // 解析数字
        const followMatch = metaText.match(/(\d+)\s*人关注/);
        const answerMatch = metaText.match(/(\d+)\s*个回答/);

        results.push({
          title,
          url,
          questionId,
          followers: followMatch ? parseInt(followMatch[1]) : 0,
          answers: answerMatch ? parseInt(answerMatch[1]) : 0
        });
      }
    });

    return results;
  });
}

// 获取问题详情
async function getQuestionDetail(page, basicInfo) {
  const detail = await page.evaluate(() => {
    // 获取问题描述
    const descElement = document.querySelector('.QuestionRichText, .QuestionHeader-detail');
    const description = descElement ? descElement.textContent.trim() : '';

    // 获取话题标签
    const topicElements = document.querySelectorAll('.QuestionHeader-topics .Tag, .Tag-content');
    const topics = Array.from(topicElements).map(el => el.textContent.trim());

    // 获取关注和回答数（更精确）
    const statsElements = document.querySelectorAll('.QuestionHeader-stats .NumberBoard-itemValue');
    const stats = Array.from(statsElements).map(el => el.textContent.trim());

    return {
      description,
      topics,
      stats
    };
  });

  return {
    ...basicInfo,
    description: detail.description,
    topics: detail.topics,
    detailedStats: detail.stats
  };
}

// 生成并保存草稿
async function generateAndSaveDraft(question) {
  const timestamp = new Date().toISOString();

  // 保存问题信息
  await fs.writeFile(
    path.join(CONFIG.outputDir, 'question-info.json'),
    JSON.stringify(question, null, 2),
    'utf-8'
  );

  // 生成回答草稿框架
  const draftContent = `# 知乎回答草稿

## 问题信息
- **标题**: ${question.title}
- **链接**: ${question.url}
- **问题ID**: ${question.questionId}
- **关注人数**: ${question.followers}
- **回答数**: ${question.answers}
- **话题标签**: ${question.topics?.join(', ') || '无'}
- **生成时间**: ${new Date().toLocaleString('zh-CN')}

## 问题描述
${question.description || '（无详细描述）'}

---

## 回答大纲

### TL;DR（核心观点，2-3句话）
[待补充] 用最简洁的语言概括你的核心观点和建议

---

### 一、引言：为什么这个问题值得关注

[待补充]
- 阐述问题的重要性和实际价值
- 点出当前业界的痛点或挑战
- 引出你将要分享的解决方案/见解

**字数要求**: 200-300字

---

### 二、理论基础：核心概念解析

[待补充]
- Agent的定义和核心组成部分
- Prompt Engineering的基本原理
- 相关技术栈（RAG、Tool Calling等）

**要求**:
- 使用简洁的语言解释复杂概念
- 可以用类比或实例帮助理解
- 字数: 400-500字

---

### 三、技术实现：落地方案和最佳实践

[待补充]

#### 3.1 架构设计
- 系统架构图（文字描述）
- 核心模块说明
- 技术选型考虑

#### 3.2 代码示例
\`\`\`python
# 示例代码1: Agent基础实现
# [待补充实际代码]
\`\`\`

\`\`\`python
# 示例代码2: Prompt优化技巧
# [待补充实际代码]
\`\`\`

#### 3.3 关键技术点
- [待补充] 技术点1
- [待补充] 技术点2
- [待补充] 技术点3

**字数要求**: 600-800字

---

### 四、实战案例：真实项目经验分享

[待补充]

#### 案例1: [具体场景]
- **背景**:
- **挑战**:
- **解决方案**:
- **效果数据**:

#### 案例2: [具体场景]
- **背景**:
- **挑战**:
- **解决方案**:
- **效果数据**:

**要求**:
- 提供具体的业务场景
- 包含可量化的数据（性能提升、准确率等）
- 字数: 400-500字

---

### 五、进阶技巧和坑点

[待补充]

#### 5.1 性能优化建议
- [待补充] 建议1
- [待补充] 建议2

#### 5.2 常见问题和解决方案
- [待补充] 问题1及解决方案
- [待补充] 问题2及解决方案

#### 5.3 实践中的注意事项
- [待补充] 注意事项

**字数要求**: 300-400字

---

### 六、总结与展望

[待补充]
- 总结核心要点（3-5条）
- 给读者的行动建议
- 技术趋势展望

**字数要求**: 200-300字

---

## 参考资料和延伸阅读

- [待补充] 相关论文
- [待补充] 技术文档
- [待补充] 优质博客文章
- [待补充] 开源项目

---

## 写作检查清单

完成回答前请确认：

- [ ] 总字数达到 2000-3000字
- [ ] 包含至少2-3个代码示例
- [ ] 提供具体的案例或数据支撑
- [ ] 逻辑结构清晰，层次分明
- [ ] 语言通俗易懂，避免过度学术化
- [ ] 包含实用的行动建议
- [ ] 检查排版格式（标题、代码块、列表）
- [ ] 添加适当的强调和总结
- [ ] 引用的资料准确可靠

---

## 发布前最终审核

- [ ] 技术内容准确性验证
- [ ] 代码示例可运行性检查
- [ ] 语法和错别字检查
- [ ] 格式和排版优化
- [ ] 确保原创性，避免抄袭
- [ ] 设置合适的话题标签

---

**生成时间**: ${new Date().toLocaleString('zh-CN')}
**文件路径**: ${path.join(CONFIG.outputDir, 'answer-draft.md')}
`;

  await fs.writeFile(
    path.join(CONFIG.outputDir, 'answer-draft.md'),
    draftContent,
    'utf-8'
  );
}

// 等待用户输入
function waitForUserInput() {
  return new Promise(resolve => {
    process.stdin.once('data', () => {
      resolve();
    });
  });
}

// 获取用户选择
function getUserChoice(max) {
  return new Promise(resolve => {
    const readline = require('readline').createInterface({
      input: process.stdin,
      output: process.stdout
    });

    const askChoice = () => {
      readline.question('请输入编号: ', (answer) => {
        const num = parseInt(answer);
        if (num >= 1 && num <= max) {
          readline.close();
          resolve(num - 1);
        } else {
          console.log(`请输入1到${max}之间的数字`);
          askChoice();
        }
      });
    };

    askChoice();
  });
}

main().catch(console.error);
