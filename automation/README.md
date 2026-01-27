# 知乎每日自动回答系统

## 📋 系统概述

这是一个自动化系统，每天晚上22:00自动搜索知乎热门问题并生成高质量回答。

## 🎯 功能特性

- ✅ 自动搜索热门问题（AI Agent、Prompt Engineering等领域）
- ✅ 智能选择最有价值的问题
- ✅ 生成4000+字的专业技术回答
- ✅ 自动登录并发布到知乎
- ✅ 完整的日志和报告记录

## 📂 文件结构

```
automation/
├── config.json                 # 配置文件
├── daily-zhihu-answer.sh      # Bash执行脚本
├── daily-zhihu-answer.py      # Python执行脚本
├── README.md                  # 本文件
├── logs/                      # 日志目录
│   └── zhihu-answer-YYYY-MM-DD.log
└── setup-cron.sh              # Cron任务安装脚本
```

## ⚙️ 配置说明

### config.json 配置项

```json
{
  "schedule": {
    "time": "22:00",           # 执行时间
    "frequency": "daily"       # 执行频率
  },
  "content_config": {
    "topics": [...],           # 关注的内容领域
    "question_filters": {
      "publish_days": 7,       # 问题发布天数范围
      "min_views": 1000,       # 最小浏览量
      "max_answers": 50        # 最大回答数
    }
  },
  "publish_mode": "auto"       # auto: 自动发布, draft: 仅生成草稿
}
```

## 🚀 安装步骤

### 方法1：使用Cron（推荐）

1. **赋予脚本执行权限**
   ```bash
   chmod +x /Users/leiw/Projects/claude-skills-tutorials/automation/daily-zhihu-answer.sh
   ```

2. **编辑crontab**
   ```bash
   crontab -e
   ```

3. **添加定时任务**
   ```cron
   # 每天晚上22:00执行知乎自动回答任务
   0 22 * * * /Users/leiw/Projects/claude-skills-tutorials/automation/daily-zhihu-answer.sh
   ```

4. **保存并退出**
   - Vim: 按 `ESC`, 输入 `:wq`, 回车
   - Nano: 按 `Ctrl+X`, 输入 `Y`, 回车

5. **验证cron任务**
   ```bash
   crontab -l
   ```

### 方法2：使用launchd（macOS推荐）

1. **创建plist文件**
   ```bash
   cp automation/com.zhihu.daily-answer.plist ~/Library/LaunchAgents/
   ```

2. **加载任务**
   ```bash
   launchctl load ~/Library/LaunchAgents/com.zhihu.daily-answer.plist
   ```

3. **启动任务**
   ```bash
   launchctl start com.zhihu.daily-answer
   ```

## 🧪 测试运行

在设置定时任务前，建议先手动测试：

```bash
# 方法1：直接运行脚本
/Users/leiw/Projects/claude-skills-tutorials/automation/daily-zhihu-answer.sh

# 方法2：运行Python脚本
python3 /Users/leiw/Projects/claude-skills-tutorials/automation/daily-zhihu-answer.py
```

## 📊 查看日志

```bash
# 查看今天的日志
tail -f /Users/leiw/Projects/claude-skills-tutorials/automation/logs/zhihu-answer-$(date +%Y-%m-%d).log

# 查看所有日志
ls -lh /Users/leiw/Projects/claude-skills-tutorials/automation/logs/
```

## 📁 查看输出

每天的回答会保存在：
```
zhihu-drafts/daily/YYYY-MM-DD/
├── answer-draft.md           # 回答内容
├── question-info.json        # 问题信息
└── execution-report.json     # 执行报告
```

## ⚠️ 重要提醒

### 安全性
- ⚠️ 配置文件包含知乎账号密码，请确保文件权限安全
- 建议设置文件权限：`chmod 600 automation/config.json`
- 不要将配置文件提交到公开的Git仓库

### 自动发布风险
- ⚠️ 当前配置为"自动发布"模式，回答会直接发布到知乎
- 建议前几天监控发布质量
- 如需改为草稿模式，修改 `config.json` 中的 `publish_mode` 为 `"draft"`

### 账号安全
- 频繁自动登录可能触发知乎的安全检测
- 建议使用应用专用密码（如果知乎支持）
- 定期检查账号安全状态

## 🔧 故障排查

### 问题1：Cron任务没有执行
```bash
# 检查cron服务状态
sudo launchctl list | grep cron

# 查看系统日志
tail -f /var/log/system.log | grep cron
```

### 问题2：脚本执行失败
```bash
# 检查脚本权限
ls -l automation/daily-zhihu-answer.sh

# 手动运行查看错误
bash -x automation/daily-zhihu-answer.sh
```

### 问题3：Agent调用失败
- 确保Claude Code已正确安装
- 检查zhihu-ai-content-strategist agent是否存在
- 查看日志文件获取详细错误信息

## 📝 修改配置

### 更改执行时间
编辑 `config.json`:
```json
"schedule": {
  "time": "09:00"  # 改为早上9点
}
```

然后更新cron任务。

### 更改内容领域
编辑 `config.json`:
```json
"topics": [
  "AI Agent",
  "你的新领域"
]
```

### 切换到草稿模式
编辑 `config.json`:
```json
"publish_mode": "draft"  # 改为仅生成草稿
```

## 🛑 停止自动任务

### 停止Cron任务
```bash
# 编辑crontab
crontab -e

# 删除或注释掉对应行（在行首添加#）
# 0 22 * * * /path/to/script.sh

# 保存退出
```

### 停止launchd任务
```bash
launchctl unload ~/Library/LaunchAgents/com.zhihu.daily-answer.plist
```

## 📈 监控和优化

### 查看执行统计
```bash
# 统计成功次数
grep "✅ 任务执行成功" automation/logs/*.log | wc -l

# 统计失败次数
grep "❌ 任务执行失败" automation/logs/*.log | wc -l
```

### 性能优化建议
1. 定期清理旧日志（保留最近30天）
2. 监控回答质量和用户反馈
3. 根据数据调整问题筛选条件
4. 优化回答模板和风格

## 🆘 获取帮助

如果遇到问题：
1. 查看日志文件：`automation/logs/`
2. 检查执行报告：`zhihu-drafts/daily/*/execution-report.json`
3. 手动运行脚本查看详细错误
4. 联系技术支持

---

**创建日期**: 2026-01-21
**最后更新**: 2026-01-21
**维护者**: Claude Code
