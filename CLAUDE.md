# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **astro-news-bot** project that automatically fetches daily news from multiple sources, deduplicates, filters, summarizes using LLM, and publishes to an Astro blog. The system runs on GitHub Actions with free tier limits and integrates with static site deployment (Netlify/Vercel/Astro Cloud).

## Architecture

The project follows a pipeline architecture with these core components:

### Core Pipeline (news_bot/ directory)
- **fetcher.py** - Multi-source news fetching (NewsAPI, Guardian API, RSS feeds)
- **dedup.py** - Title-based vector deduplication using SentenceTransformer
- **selector.py** - Topic-based filtering with LLM assistance
- **summarizer.py** - LLM-powered news summarization
- **writer.py** - Markdown generation with YAML front-matter
- **publisher.py** - Automated Git commit and push
- **job.py** - CLI orchestrator for the entire pipeline

### Content Structure
- **content/news/{YYYY-MM-DD}/index.md** - Generated daily news files
- **src/components/LatestNews.astro** - Homepage component for displaying latest news

### Automation
- **.github/workflows/daily_news.yml** - GitHub Actions workflow (cron: '5 0 * * *')
- Local cron job support as alternative

## Key Dependencies

```
requests - HTTP client for API calls
python-dotenv - Environment variable management
sentence-transformers - Vector similarity for deduplication (model: 'all-MiniLM-L6-v2')
openai or dashscope - LLM integration for summarization
PyYAML - YAML processing for front-matter
```

## Development Commands

### Pipeline Execution
```bash
# Full pipeline with date
python news_bot/job.py --date YYYY-MM-DD

# Dry run (skip git push)
python news_bot/job.py --date YYYY-MM-DD --dry-run

# Individual components
python -m news_bot.fetcher YYYY-MM-DD
python -m news_bot.dedup YYYY-MM-DD
python -m news_bot.selector YYYY-MM-DD
python -m news_bot.summarizer YYYY-MM-DD
```

### Environment Setup
```bash
pip install -r requirements.txt
```

## Configuration

### API Keys (.env file required)
- OpenAI API key or Dashscope credentials for LLM operations
- NewsAPI key for news fetching
- Guardian API key for news fetching

### Topic Weights (selector.py)
```python
{"AI": 2, "Tech": 2, "Economy": 2}  # Adjust based on content preferences
```

### Output Control
- 6 news items selected per day (configurable in selector.py)
- 2-3 sentence summaries per item
- Token budget: < 4,000 tokens/day for LLM calls

## Data Flow

```
Raw News Sources → fetcher.py → raw_{date}.json
↓ (deduplication)
dedup_{date}.json → selector.py → select_{date}.json  
↓ (LLM filtering)
summary_{date}.json → writer.py → content/news/{date}/index.md
↓ (markdown generation)
Git commit/push → Static site rebuild
```

## GitHub Actions Constraints

- **Free tier limit**: 2,000 minutes/month for private repos
- **Runner**: ubuntu-latest (1x billing multiplier)  
- **Target execution time**: < 3 minutes per run
- **Auto-commit**: Uses stefanzweifel/git-auto-commit-action@v5

## Error Handling

- 3 retry attempts with exponential backoff for API calls
- LLM fallback: Random selection when GPT calls fail
- Git safety: No-op when working directory has no changes

## Astro Integration

The **LatestNews.astro** component:
- Uses `Astro.glob()` to read `content/news/**/*.md`
- Displays latest news with description and date
- Supports custom styling via `className` prop
- Links to `/news/YYYY-MM-DD/` pages

## Implementation Steps (from BLUEPRINT.md)

The project follows a 7-step implementation plan:
1. **Step 0-1**: Code skeleton creation
2. **Step 1-1/1-2**: Fetching and deduplication
3. **Step 2-1/2-2**: Selection and summarization  
4. **Step 3-1**: Markdown rendering
5. **Step 4-1/4-2**: Publishing and CLI integration
6. **Step 5-1**: GitHub Actions workflow
7. **Step 6-1**: Astro frontend component

Refer to BLUEPRINT.md for detailed prompts and acceptance criteria for each step.