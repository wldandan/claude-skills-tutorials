# 知乎完全自动化回答系统

## 🎯 系统功能

这是一个**完全自动化**的知乎回答系统，可以：
1. ✅ 自动搜索知乎热门问题
2. ✅ 智能选择最有价值的问题
3. ✅ 使用AI生成4000+字高质量回答
4. ✅ 自动登录并发布到知乎
5. ✅ 保存完整记录和报告

## 📋 系统要求

- Python 3.8+
- macOS/Linux（Windows需调整部分路径）
- 稳定的网络连接
- （可选）Anthropic API Key（用于高质量AI回答）

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Python库
pip3 install playwright anthropic

# 安装浏览器驱动
python3 -m playwright install chromium
```

### 2. 配置API Key（可选但推荐）

```bash
# 设置环境变量
export ANTHROPIC_API_KEY='your-api-key-here'

# 或者添加到 ~/.zshrc 或 ~/.bashrc
echo 'export ANTHROPIC_API_KEY="your-api-key"' >> ~/.zshrc
source ~/.zshrc
```

**获取API Key**：访问 https://console.anthropic.com/

### 3. 运行测试

```bash
# 方法1：使用启动脚本（推荐）
/Users/leiw/Projects/claude-skills-tutorials/automation/run-auto-answer.sh

# 方法2：直接运行Python脚本
cd /Users/leiw/Projects/claude-skills-tutorials/automation
python3 full-auto-answer.py
```

### 4. 设置定时任务

#### 方法A：使用Cron

```bash
# 编辑crontab
crontab -e

# 添加以下行（每天晚上22:00执行）
0 22 * * * /Users/leiw/Projects/claude-skills-tutorials/automation/run-auto-answer.sh
```

#### 方法B：使用launchd（macOS推荐）

```bash
# 创建plist文件
cat > ~/Library/LaunchAgents/com.zhihu.full-auto-answer.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.zhihu.full-auto-answer</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/leiw/Projects/claude-skills-tutorials/automation/run-auto-answer.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>22</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/leiw/Projects/claude-skills-tutorials/automation/logs/launchd-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/leiw/Projects/claude-skills-tutorials/automation/logs/launchd-stderr.log</string>
</dict>
</plist>
EOF

# 加载任务
launchctl load ~/Library/LaunchAgents/com.zhihu.full-auto-answer.plist

# 立即测试
launchctl start com.zhihu.full-auto-answer
```

## 📊 查看结果

### 查看日志

```bash
# 查看今天的日志
tail -f /Users/leiw/Projects/claude-skills-tutorials/automation/logs/auto-answer-$(date +%Y-%m-%d).log

# 查看所有日志
ls -lh /Users/leiw/Projects/claude-skills-tutorials/automation/logs/
```

### 查看生成的回答

```bash
# 今天的回答
cat /Users/leiw/Projects/claude-skills-tutorials/zhihu-drafts/daily/$(date +%Y-%m-%d)/answer-draft.md

# 查看执行报告
cat /Users/leiw/Projects/claude-skills-tutorials/zhihu-drafts/daily/$(date +%Y-%m-%d)/execution-report.json
```

## ⚙️ 配置说明

配置文件：`automation/config.json`

### 关键配置项

```json
{
  "zhihu_account": {
    "username": "15389041528",
    "password": "wldandan19810119"
  },
  "content_config": {
    "topics": [
      "AI Agent",
      "Prompt Engineering",
      "大模型应用",
      "RAG技术",
      "Claude Code",
      "Agent软件工程",
      "软件工程"
    ],
    "question_filters": {
      "publish_days": 7,
      "min_views": 1000,
      "max_answers": 50
    }
  },
  "publish_mode": "auto"
}
```

### 修改配置

```bash
# 编辑配置文件
code /Users/leiw/Projects/claude-skills-tutorials/automation/config.json

# 或使用vim
vim /Users/leiw/Projects/claude-skills-tutorials/automation/config.json
```

## 🔧 工作流程

系统执行流程：

```
1. 启动浏览器
   ↓
2. 登录知乎账号
   ↓
3. 搜索热门问题（按配置的主题）
   ↓
4. 智能选择最佳问题
   ↓
5. 调用AI生成回答
   ├─ 有API Key：使用Claude生成高质量回答
   └─ 无API Key：使用模板生成基础回答
   ↓
6. 自动发布到知乎
   ↓
7. 保存记录和报告
   ↓
8. 关闭浏览器
```

## ⚠️ 重要提醒

### 安全性

1. **保护配置文件**
   ```bash
   chmod 600 /Users/leiw/Projects/claude-skills-tutorials/automation/config.json
   ```

2. **不要提交到Git**
   ```bash
   # 确保config.json在.gitignore中
   echo "automation/config.json" >> .gitignore
   ```

3. **定期更换密码**
   - 建议每月更换一次知乎密码
   - 及时更新config.json中的密码

### 风险提示

1. **账号安全**
   - 频繁自动登录可能触发知乎安全检测
   - 建议设置合理的执行频率（每天1次）
   - 如遇验证码，脚本会等待30秒供人工处理

2. **内容质量**
   - 没有API Key时，回答质量较低
   - 强烈建议配置Anthropic API Key
   - 前几天建议手动审核发布内容

3. **发布频率**
   - 不要过于频繁发布（建议每天1篇）
   - 避免在短时间内发布多篇
   - 保持内容质量和多样性

## 🐛 故障排查

### 问题1：登录失败

**可能原因**：
- 账号密码错误
- 需要验证码
- IP被限制

**解决方案**：
```bash
# 1. 检查配置文件
cat automation/config.json | grep username

# 2. 手动登录测试
# 运行脚本，观察浏览器行为

# 3. 查看日志
tail -50 automation/logs/auto-answer-$(date +%Y-%m-%d).log
```

### 问题2：找不到问题

**可能原因**：
- 搜索关键词太窄
- 筛选条件太严格

**解决方案**：
```bash
# 修改配置，放宽筛选条件
# 编辑 config.json
{
  "question_filters": {
    "publish_days": 30,      # 增加到30天
    "min_views": 500,        # 降低浏览量要求
    "max_answers": 100       # 增加回答数上限
  }
}
```

### 问题3：AI回答质量差

**原因**：未设置API Key

**解决方案**：
```bash
# 设置API Key
export ANTHROPIC_API_KEY='your-api-key'

# 或修改脚本使用其他AI服务
```

### 问题4：发布失败

**可能原因**：
- 知乎页面结构变化
- 网络问题
- 内容被拦截

**解决方案**：
```bash
# 1. 查看日志详细错误
tail -100 automation/logs/auto-answer-$(date +%Y-%m-%d).log

# 2. 手动运行并观察
python3 automation/full-auto-answer.py

# 3. 检查生成的回答内容
cat zhihu-drafts/daily/$(date +%Y-%m-%d)/answer-draft.md
```

## 📈 性能优化

### 1. 提升回答质量

```bash
# 使用更强大的模型
# 修改 answer_generator.py 中的模型参数
model="claude-opus-4-5-20251101"  # 使用Opus模型
```

### 2. 加快执行速度

```python
# 修改 full-auto-answer.py
# 将 headless 设为 True
self.browser = await playwright.chromium.launch(
    headless=True,  # 后台运行，更快
)
```

### 3. 批量处理

```python
# 一次回答多个问题
# 修改主循环逻辑
for question in best_questions[:3]:  # 回答前3个问题
    await self.process_question(question)
```

## 📞 获取帮助

### 查看日志

```bash
# 最新日志
tail -f automation/logs/auto-answer-$(date +%Y-%m-%d).log

# 搜索错误
grep "ERROR" automation/logs/*.log
```

### 测试模式

```bash
# 修改配置为测试模式
# 在 config.json 中添加
{
  "test_mode": true,  # 不实际发布，只生成内容
}
```

## 🎉 成功案例

使用本系统后的预期效果：

- **时间节省**：从每天2小时 → 10分钟（自动化后）
- **内容质量**：4000+字专业回答
- **发布频率**：每天1篇稳定输出
- **账号成长**：持续积累专业影响力

## 📝 更新日志

- **2026-01-21**：初始版本发布
  - 完整的自动化流程
  - AI回答生成
  - 自动登录发布
  - 日志和报告系统

---

**维护者**：Claude Code
**最后更新**：2026-01-21
**版本**：1.0.0
