# Astro News Bot

基于 AI 的自动化科技新闻聚合和博客发布系统。自动从多个新闻源获取科技资讯，进行去重、摘要和分类，生成适合 Astro 博客的 Markdown 文件。

## 功能特性

- 🔄 **多源新闻获取**：支持 NewsAPI、Guardian API 和 RSS 订阅
- 🎯 **智能内容过滤**：专注科技/IT/AI/科学进展相关信息
- 🔍 **向量去重**：使用 SentenceTransformer 进行语义相似度去重
- 🤖 **AI 摘要**：基于 OpenAI GPT-4o 生成中文摘要和标签
- 📂 **自动分类**：智能归类到 9 个科技领域
- 📝 **Markdown 生成**：输出符合 Astro 博客标准的文章格式
- ⚙️ **灵活配置**：支持自定义输出路径和参数

## 项目结构

```
astro-news-bot/
├── news_bot/
│   ├── fetcher.py      # 新闻获取
│   ├── dedup.py        # 向量去重
│   ├── summarizer.py   # AI 摘要
│   ├── writer.py       # Markdown 生成
│   ├── selector.py     # 新闻筛选
│   ├── publisher.py    # 发布管理
│   └── job.py          # 工作流调度
├── config.json         # 配置文件
├── requirements.txt    # 依赖包
└── .env.example       # 环境变量模板
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd astro-news-bot

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API 密钥

复制环境变量模板并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入以下 API 密钥：

```env
# 必需：OpenAI API（用于摘要生成）
OPENAI_API_KEY=your_openai_api_key_here

# 可选：新闻源 API
NEWSAPI_KEY=your_newsapi_key_here
GUARDIAN_API_KEY=your_guardian_api_key_here
```

### 3. 配置输出路径

编辑 `config.json` 中的博客目录：

```json
{
  "output_config": {
    "blog_content_dir": "/Users/geyuxu/repo/blog/geyuxu.com/src/content/news",
    "filename_format": "news_{date}.md",
    "use_blog_dir": true
  },
  "git_config": {
    "target_branch": "gh-pages",
    "auto_switch_branch": true,
    "push_to_remote": true
  }
}
```

### 4. 运行全链路测试

```bash
# 完整工作流测试（自动化脚本操作）
DATE=$(date +%Y-%m-%d)

echo "=== 步骤 1: 新闻获取 ==="
python -m news_bot.fetcher $DATE

echo "=== 步骤 2: 向量去重 ==="
python -m news_bot.dedup $DATE

echo "=== 步骤 3: AI 摘要生成 ==="
python -m news_bot.summarizer $DATE

echo "=== 步骤 4: Markdown 生成 ==="
python -m news_bot.writer $DATE

echo "=== 步骤 5: Git 发布 ==="
python -m news_bot.publisher "Add daily news for $DATE"
```

## 使用方法

### 手动执行单个步骤

```bash
# 步骤 1：获取新闻
python -m news_bot.fetcher 2025-07-25

# 步骤 2：去重处理
python -m news_bot.dedup 2025-07-25

# 步骤 3：生成摘要
python -m news_bot.summarizer 2025-07-25

# 步骤 4：生成 Markdown
python -m news_bot.writer 2025-07-25

# 步骤 5：Git 发布
python -m news_bot.publisher "Add daily news for 2025-07-25"
```

### 自动化工作流

#### 方式1：直接运行（推荐）

```bash
# 执行完整流程 - 推荐方式
python -m news_bot.job --date $(date +%Y-%m-%d)

# 或指定特定日期
python -m news_bot.job --date 2025-07-25

# 干跑模式（跳过发布步骤）
python -m news_bot.job --date 2025-07-25 --dry-run
```

#### 方式2：后台脚本执行

```bash
# 后台执行脚本（包含日志记录）
./run_daily_news.sh

# 干跑模式测试
./run_daily_news.sh --dry-run

# 指定日期执行
./run_daily_news.sh --date 2025-07-25
```

#### 方式3：调度管理器（阻塞式）

```bash
# 启动后台调度器（占用终端）
./scheduler_manager.sh start

# 查看调度器状态
./scheduler_manager.sh status

# 立即执行一次
./scheduler_manager.sh run-now

# 查看运行日志
./scheduler_manager.sh logs

# 停止调度器
./scheduler_manager.sh stop

# 重启调度器
./scheduler_manager.sh restart

# 显示配置信息
./scheduler_manager.sh config
```

#### 方式4：守护进程模式（推荐）

**真正的后台守护进程，不占用终端，支持完善的启停控制：**

```bash
# 启动守护进程（完全后台运行）
./start_daemon.sh start

# 查看运行状态
./start_daemon.sh status

# 查看运行日志
./start_daemon.sh logs

# 停止守护进程（优雅关闭 + 强制清理）
./start_daemon.sh stop
# 或者快速停止
./stop_daemon.sh

# 重启守护进程
./start_daemon.sh restart

# 显示帮助信息
./start_daemon.sh help
```

**特点：**
- ✅ 真正的后台运行，不占用终端
- ✅ 完善的PID管理和进程清理
- ✅ 优雅关闭 + 强制停止双重保障
- ✅ 自动清理残留进程
- ✅ 详细的启动和停止日志

**Python原生调度器命令：**

```bash
# 启动调度器（需要保持终端开启）
python -m news_bot.scheduler start

# 查看调度器状态
python -m news_bot.scheduler status

# 停止调度器
python -m news_bot.scheduler stop

# 立即执行一次任务
python -m news_bot.scheduler run-now
```

## 后台执行与定时任务

### 推荐方式：守护进程

**最佳实践是使用守护进程模式，完全后台运行，不占用终端：**

```bash
# 启动守护进程
./start_daemon.sh start

# 查看状态
./start_daemon.sh status

# 查看日志
./start_daemon.sh logs

# 停止守护进程
./stop_daemon.sh
```

### 传统方式：cron定时任务

如果不想使用守护进程，也可以使用cron设置每日自动执行：

```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天8:05执行）
5 8 * * * /Users/geyuxu/repo/astro-news-bot/run_daily_news.sh

# 查看已设置的定时任务
crontab -l
```

### 日志管理

**守护进程日志：**
- 守护进程日志：`logs/daemon.log`
- 调度器日志：`logs/scheduler.log`

**传统脚本日志：**
- 脚本执行日志：`~/logs/news_bot.log`

**查看日志：**
```bash
# 查看守护进程日志
./start_daemon.sh logs

# 实时监控日志
tail -f logs/daemon.log

# 查看调度器日志
tail -f logs/scheduler.log
```

```bash
# 查看最新日志
tail -f ~/logs/news_bot.log

# 查看今天的执行记录
grep "$(date +%Y-%m-%d)" ~/logs/news_bot.log

# 查看最近10行日志
tail -10 ~/logs/news_bot.log
```

## 更新日志

### v1.2.0 (2025-07-26)
- 🎉 **新增真正的守护进程模式**：完全后台运行，不占用终端
- 🔧 **修复进程管理问题**：优化PID管理和进程清理机制
- ✅ **改进停止机制**：支持优雅关闭和强制停止双重保障
- 🧹 **自动清理功能**：防止进程残留，确保干净停止
- 📊 **增强日志管理**：详细的启动、运行和停止日志
- 📝 **完善文档**：新增守护进程使用说明和故障排除指南

### v1.1.0 (2025-07-25)
- 🚀 **完成全链路实现**：fetcher → dedup → selector → summarizer → writer → publisher
- ⏰ **后台调度系统**：支持定时任务和手动执行
- 🛠️ **多种执行方式**：直接运行、脚本执行、调度管理、守护进程
- 📋 **shell脚本工具**：run_daily_news.sh 和 scheduler_manager.sh
- 🔄 **cron集成**：支持传统cron定时任务
- 📄 **完整文档**：README包含所有使用方法和配置说明

### 调度器配置

修改 `config.json` 中的调度器设置：

```json
{
  "scheduler_config": {
    "enabled": true,
    "timezone": "Asia/Shanghai",
    "cron_expression": "0 8 * * *",
    "dry_run": false,
    "max_retries": 3,
    "retry_interval_minutes": 30
  }
}
```

## 配置说明

### config.json 配置项

```json
{
  "output_config": {
    "blog_content_dir": "博客内容目录路径",
    "local_content_dir": "本地内容目录路径", 
    "filename_format": "文件命名格式，如 news_{date}.md",
    "use_blog_dir": "是否输出到博客目录"
  },
  "git_config": {
    "target_branch": "Git目标分支",
    "auto_switch_branch": "是否自动切换分支",
    "push_to_remote": "是否推送到远程"
  },
  "news_config": {
    "max_articles_per_day": "每日最大文章数",
    "token_budget_per_day": "每日 Token 预算",
    "similarity_threshold": "去重相似度阈值"
  },
  "llm_config": {
    "model": "使用的 LLM 模型",
    "max_tokens": "最大 Token 数",
    "temperature": "生成温度"
  },
  "scheduler_config": {
    "enabled": "是否启用调度器",
    "timezone": "时区设置",
    "cron_expression": "Cron表达式"
  }
}
```

## 技术架构

### 数据流程

1. **新闻获取** → 多源抓取 → `raw_{date}.json`
2. **向量去重** → 语义相似度过滤 → `dedup_{date}.json`
3. **AI 摘要** → GPT-4o 生成中文摘要 → `summary_{date}.json`
4. **Markdown 生成** → 按类别组织 → `news_{date}.md`

### 新闻分类

系统自动将新闻归类到以下 9 个科技领域：

- 🤖 人工智能
- 📱 移动技术  
- 🚗 自动驾驶
- ☁️ 云计算
- 💾 芯片技术
- 💰 创业投资
- 🔒 网络安全
- ⛓️ 区块链
- 🔬 科学研究

## 输出格式

生成的 Markdown 文件包含：

- **YAML Front-matter**：标题、日期、描述、标签等元数据
- **按类别分组**：新闻按技术领域自动分类
- **中文摘要**：AI 生成的新闻要点
- **标签系统**：自动提取的关键词标签
- **原文链接**：保留新闻源链接

## API 成本控制

- 每日处理约 6 篇文章
- 预计 Token 消耗：~4000 tokens/天
- OpenAI 成本：约 $0.01-0.05/天

## 开发状态

### 已完成模块

- ✅ 新闻获取（fetcher.py）
- ✅ 向量去重（dedup.py）
- ✅ AI 摘要（summarizer.py）
- ✅ Markdown 生成（writer.py）
- ✅ Git 发布（publisher.py）
- ✅ 工作流调度（job.py）
- ✅ 配置系统（config.json）
- ✅ 全链路测试验证

### 待开发模块

- ⏳ 新闻筛选（selector.py）
- ✅ 工作流调度（job.py）
- ⏳ GitHub Actions 自动化
- ⏳ Astro 前端组件

## 测试验证

### 全链路测试结果

最新测试日期：2025-07-26

**测试流程：**
1. **Fetcher** → 获取了 31 篇科技新闻（RSS 源）
2. **Deduplicator** → 向量去重处理，保留 31 篇唯一文章
3. **Summarizer** → AI 摘要生成，使用 10,681 tokens
4. **Writer** → 生成 188 行 Markdown，包含 7 个科技分类
5. **Publisher** → 成功提交并推送到博客仓库

**验证结果：**
- ✅ **纯脚本操作**：全程无需人工干预
- ✅ **配置正确**：文件生成在正确的博客目录
- ✅ **Git 流程**：成功推送到博客仓库
- ✅ **内容质量**：自动分类到 7 个科技领域
- ✅ **格式标准**：符合 Astro 博客系统要求

**性能指标：**
- 处理文章数：31 篇
- 生成文件大小：17.5KB，188 行
- Token 消耗：10,681（需优化以控制成本）
- 执行时间：约 2-3 分钟

**生成示例：**
- 输出文件：`news_2025-07-26.md`
- 技术分类：人工智能、移动技术、自动驾驶、芯片技术等
- Git 提交：自动提交到博客仓库并推送

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！