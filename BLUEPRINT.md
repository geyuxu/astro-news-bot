自动「每日新闻」功能 - 项目蓝图

适用工具链：GitHub （Free 帐号）、Astro 博客、Claude Code（AI 编程助手）、Python 3.11
目标：每天自动抓取多源新闻 → 过滤去重 → LLM 摘要 → 生成 news/YYYY-MM-DD.md → Git 推送触发站点构建 → 首页组件展示当日新闻。

⸻

一、项目简介

要素	说明
名称	astro-news-bot
核心目录	news_bot/ (Python)、content/news/ (MD)、src/components/LatestNews.astro
部署流	本地 cron or GitHub Actions 定时 → 推送到主分支 → Netlify/Vercel/Astro Cloud 自动构建
关键依赖	requests, python-dotenv, sentence-transformers, openai or dashscope, PyYAML
免费额度	GitHub Free：私有仓 2 000 min/月；公仓无限。Linux runner ×1 计费系数。


⸻

二、分步实施路线

格式说明
	•	Step #-X：任务名称
	•	Prompt（给 Claude Code）：复制进 Claude Code 即可产出样板／脚本
	•	验收标准：本步完成后必须满足的可验证结果

⸻

Step 0-1：创建代码骨架

Prompt

生成一个 Cookiecutter 模板或直接输出以下目录结构，并在空文件中放入占位注释：

news_bot/
  ├── __init__.py
  ├── fetcher.py
  ├── dedup.py
  ├── selector.py
  ├── summarizer.py
  ├── writer.py
  ├── publisher.py
  └── job.py
.contentignore  # 可选
requirements.txt

验收标准
	•	news_bot 目录与 7 个 Python 文件全部生成；每个文件首行含 # TODO 注释
	•	requirements.txt 至少列出 requests、python-dotenv、sentence-transformers、openai／dashscope

⸻

Step 1-1：实现 fetcher.py（抓取多源新闻）

Prompt

在 fetcher.py 中实现：
1. 支持 NewsAPI、Guardian API、RSS 三种源
2. 输入：日期字符串 (YYYY-MM-DD)
3. 输出：列表[dict]，字段包含 title, url, published_at, source, description
4. 对每个 API 添加 3 次重试和指数回退
5. 将结果保存本地 json：raw_{date}.json
返回全部代码。

验收标准
	•	本地执行 python -m news_bot.fetcher 2025-07-25 可在工作目录生成 raw_2025-07-25.json
	•	JSON 数组长度 ≥ 20，且字段完整无空值

⸻

Step 1-2：实现 dedup.py（标题向量去重）

Prompt

在 dedup.py 中：
1. 加载 SentenceTransformer('all-MiniLM-L6-v2')
2. 读取 raw_{date}.json
3. 基于标题文本，计算余弦相似度，阈值 0.85 以上视为重复，移除保留第一条
4. 输出去重后列表并保存 dedup_{date}.json
提供命令行入口。

验收标准
	•	python -m news_bot.dedup 2025-07-25 生成 dedup_2025-07-25.json
	•	若手动复制两条同标题新闻，最终文件只保留一条

⸻

Step 2-1：实现 selector.py（主题筛选）

Prompt

在 selector.py 中：
1. 加载 dedup_{date}.json
2. 设计主题权重：{"AI":2,"Tech":2,"Economy":2}
3. 调用 OpenAI GPT-4o：输入为 JSON 列表，要求返回符合主题权重的 6 条最佳新闻的索引数组
4. 保存 select_{date}.json
5. 遇 LLM 调用失败自动回退到随机 6 条
返回完整代码。

验收标准
	•	输出 JSON 长度 = 6
	•	若修改权重只留 "AI":1，再次运行会返回 1 条

⸻

Step 2-2：实现 summarizer.py（LLM 摘要）

Prompt

在 summarizer.py 中：
1. 读取 select_{date}.json
2. 对每条新闻调用 GPT-4o，prompt：请用 2-3 句话中文总结，并给出 bulletpoint 标签
3. 将摘要结果追加字段 summary, bullets
4. 保存 summary_{date}.json

验收标准
	•	每条对象含 summary 和 bullets(list)
	•	运行时 tokens 消耗记录 < 4 000 tokens/天

⸻

Step 3-1：实现 writer.py（渲染 Markdown）

Prompt

在 writer.py：
1. 读取 summary_{date}.json
2. 使用 YAML front-matter 生成 Markdown：
---
title: "每日新闻速览 · {date}"
pubDate: "{date}"
description: "{第一条 summary}"
tags: ["News","Daily"]
layout: "news"
---
## {主题中文}
- **{title}**  
  {summary}  
  <{url}>

3. 保存到 content/news/{date}/index.md（路径自动创建）

验收标准
	•	指定日期运行后相应 Markdown 文件存在，排版符合 Astro 解析规范
	•	文件包含至少三段不同主题 ## 小节

⸻

Step 4-1：实现 publisher.py（自动 Git 提交并推送）

Prompt

在 publisher.py：
- 参数：commit_msg
- 执行 subprocess git add . && git commit -m commit_msg && git push
- 捕获错误：若工作区无变更则退出 0

验收标准
	•	本地修改任何新闻后运行，Git 日志出现对应 commit
	•	无改动时不会抛异常

⸻

Step 4-2：串联 job.py（CLI 总入口）

Prompt

在 job.py:
1. 支持 --date, --dry-run
2. 顺序调用 fetcher → dedup → selector → summarizer → writer → publisher
3. 加 --dry-run 时跳过 publisher
4. 记录步骤耗时到 stdout

验收标准
	•	python news_bot/job.py --date 2025-07-25 --dry-run 全流程执行无报错
	•	非 dry-run 时会自动 git push

⸻

Step 5-1：GitHub Actions 定时工作流

Prompt

生成 .github/workflows/daily_news.yml：
- 触发：schedule cron '5 0 * * *'
- runner: ubuntu-latest
- 步骤：checkout → setup-python 3.11 → pip install -r requirements.txt → python news_bot/job.py
- 使用 stefanzweifel/git-auto-commit-action@v5 推送

验收标准
	•	在 GitHub Actions 面板能看到定时任务，每次成功生成并 commit news YYYY-MM-DD
	•	任务完成时间 < 3 分钟

⸻

Step 6-1：首页组件 LatestNews.astro

Prompt

创建 src/components/LatestNews.astro：
1. 使用 Astro.glob 读取 content/news/**/*.md
2. 取最新一篇排序
3. 卡片显示 description + 日期
4. props: className，可自定义样式
5. 导出默认组件

验收标准
	•	在首页模板插入 <LatestNews /> 后，构建站点能渲染今日新闻卡片
	•	点击卡片跳转到对应 /news/YYYY-MM-DD/

⸻

Step 7-1：本地定时任务（可选）

Prompt

生成 macOS+Linux cron 示例：
5 8 * * * /usr/bin/python3 /path/to/news_bot/job.py >> /var/log/news_bot.log 2>&1

验收标准
	•	crontab -l 能看到记录
	•	第二天早晨 08:05 本地日志出现成功行

⸻

三、里程碑与交付

里程碑	完成标志
M1	Step 0-1~1-2，本地可抓取+去重
M2	Step 2-2，LLM 摘要成功产出
M3	Step 3-1，新闻 MD 文件渲染无语法错误
M4	Step 4-2，job.py 全流程 dry-run OK
M5	Step 5-1，GitHub Actions 连续两天自动推送
M6	Step 6-1，首页组件展示最新新闻


⸻

使用提示
	•	Claude Code 可一次输入完整 Prompt；若超长，把功能拆成多个 Prompt 分步生成。
	•	生成代码后，记得在本地运行单元测试或手动验收，以免 CI 失败。
	•	若 LLM 费用需要控制，提前在 .env 设置 model=gpt-4o-mini 或 Dashscope 4k 版本。

完成以上蓝图，你的静态博客将实现低成本、自动化的每日新闻发布。祝编码顺利!
