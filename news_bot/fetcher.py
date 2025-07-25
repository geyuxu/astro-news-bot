"""
Multi-source news fetcher with retry logic and exponential backoff.
Supports NewsAPI, Guardian API, and RSS feeds.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import feedparser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class NewsFetcher:
    def __init__(self):
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        self.guardian_key = os.getenv('GUARDIAN_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'astro-news-bot/1.0'
        })
        
        # Tech-related keywords for content filtering
        self.tech_keywords = {
            'high_priority': [
                'artificial intelligence', 'ai', 'machine learning', 'deep learning', 'neural network',
                'gpt', 'llm', 'large language model', 'chatgpt', 'openai', 'anthropic', 'claude',
                'algorithm', 'programming', 'software', 'technology', 'tech', 'startup',
                'robotics', 'automation', 'computer science', 'data science', 'quantum computing',
                'blockchain', 'cryptocurrency', 'cybersecurity', 'cloud computing', 'api',
                'semiconductor', 'chip', 'processor', 'microprocessor', 'gpu', 'cpu',
                'app', 'platform', 'google', 'microsoft', 'apple', 'meta', 'tesla', 'intel',
                'nvidia', 'coding', 'developer', 'github', 'open source', 'database',
                'web development', 'mobile app', 'ios', 'android', 'linux', 'windows'
            ],
            'science_keywords': [
                'research', 'study', 'discovery', 'breakthrough', 'innovation', 'scientific',
                'experiment', 'development', 'advancement', 'progress', 'engineering',
                'crispr', 'genetics', 'space', 'nasa', 'spacex', 'climate', 'energy',
                'battery', 'renewable', 'electric vehicle', 'ev', 'autonomous'
            ],
            'exclude_keywords': [
                'sports', 'entertainment', 'celebrity', 'fashion', 'politics', 'election',
                'weather', 'crime', 'accident', 'death', 'murder', 'war', 'military',
                'porn', 'adult', 'sex', 'dating', 'relationship', 'love', 'marriage'
            ]
        }
    
    def _is_tech_related(self, article: Dict) -> bool:
        """Check if an article is tech/AI/science related."""
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        text_content = f"{title} {description}"
        
        # Check for exclusion keywords first
        for exclude_word in self.tech_keywords['exclude_keywords']:
            if exclude_word in text_content:
                return False
        
        # Check for high priority tech keywords
        tech_score = 0
        for keyword in self.tech_keywords['high_priority']:
            if keyword in text_content:
                tech_score += 2
        
        # Check for science keywords
        for keyword in self.tech_keywords['science_keywords']:
            if keyword in text_content:
                tech_score += 1
                
        # Article is tech-related if score is >= 1
        return tech_score >= 1
    
    def _retry_request(self, func, max_retries=3):
        """Execute function with exponential backoff retry logic."""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                wait_time = 2 ** attempt
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
    
    def fetch_newsapi(self, date: str) -> List[Dict]:
        """Fetch tech/AI/science news from NewsAPI for a specific date."""
        if not self.newsapi_key:
            print("Warning: NEWSAPI_KEY not found in environment")
            return []
        
        def _fetch():
            # Convert date to NewsAPI format
            from_date = date
            to_date = date
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': '(artificial intelligence OR machine learning OR AI OR technology OR software OR programming OR computer science OR data science OR robotics OR automation OR tech startup OR semiconductor OR chip OR quantum computing OR blockchain OR cryptocurrency OR cybersecurity OR cloud computing OR API OR algorithm OR neural network OR deep learning OR LLM OR GPT)',
                'from': from_date,
                'to': to_date,
                'sortBy': 'popularity',
                'language': 'en',
                'pageSize': 50,
                'apiKey': self.newsapi_key,
                'domains': 'techcrunch.com,wired.com,arstechnica.com,theverge.com,engadget.com,venturebeat.com,zdnet.com,cnet.com,ieee.org,nature.com,science.org'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article in data.get('articles', []):
                if article.get('title') and article.get('url') and self._is_tech_related(article):
                    articles.append({
                        'title': article['title'],
                        'url': article['url'],
                        'published_at': article.get('publishedAt', ''),
                        'source': f"NewsAPI - {article.get('source', {}).get('name', 'Unknown')}",
                        'description': article.get('description', '') or article.get('content', '')[:200]
                    })
            
            return articles
        
        try:
            return self._retry_request(_fetch)
        except Exception as e:
            print(f"Failed to fetch from NewsAPI: {e}")
            return []
    
    def fetch_guardian(self, date: str) -> List[Dict]:
        """Fetch tech/science news from Guardian API for a specific date."""
        if not self.guardian_key:
            print("Warning: GUARDIAN_API_KEY not found in environment")
            return []
        
        def _fetch():
            url = "https://content.guardianapis.com/search"
            params = {
                'from-date': date,
                'to-date': date,
                'order-by': 'relevance',
                'show-fields': 'headline,trailText,webUrl',
                'page-size': 50,
                'api-key': self.guardian_key,
                'section': 'technology|science',
                'q': 'artificial intelligence OR AI OR machine learning OR technology OR software OR programming OR robotics OR automation OR tech OR startup OR cybersecurity OR quantum OR blockchain OR data science'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article in data.get('response', {}).get('results', []):
                fields = article.get('fields', {})
                article_data = {
                    'title': fields.get('headline', article.get('webTitle', '')),
                    'url': article.get('webUrl', ''),
                    'published_at': article.get('webPublicationDate', ''),
                    'source': 'The Guardian',
                    'description': fields.get('trailText', '')[:200]
                }
                
                if self._is_tech_related(article_data):
                    articles.append(article_data)
            
            return articles
        
        try:
            return self._retry_request(_fetch)
        except Exception as e:
            print(f"Failed to fetch from Guardian: {e}")
            return []
    
    def fetch_rss_feeds(self, date: str) -> List[Dict]:
        """Fetch tech/AI/science news from RSS feeds for a specific date."""
        rss_feeds = [
            'https://feeds.bbci.co.uk/news/technology/rss.xml',
            'https://feeds.reuters.com/reuters/technologyNews',
            'https://techcrunch.com/feed/',
            'https://www.theverge.com/rss/index.xml',
            'https://feeds.arstechnica.com/arstechnica/technology-lab',
            'https://www.wired.com/feed/rss',
            'https://venturebeat.com/feed/',
            'https://www.engadget.com/rss.xml',
            'https://feeds.feedburner.com/venturebeat/ai',
            'https://www.nature.com/subjects/computer-science.rss',
            'https://www.science.org/rss/news_current.xml'
        ]
        
        def _fetch_feed(feed_url):
            response = self.session.get(feed_url, timeout=30)
            response.raise_for_status()
            return feedparser.parse(response.content)
        
        articles = []
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        for feed_url in rss_feeds:
            try:
                feed_data = self._retry_request(lambda: _fetch_feed(feed_url))
                
                for entry in feed_data.entries[:20]:  # Limit per feed
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6]).date()
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6]).date()
                    
                    # Filter by date (allow ±1 day tolerance)
                    if pub_date and abs((pub_date - target_date).days) <= 1:
                        article_data = {
                            'title': entry.get('title', ''),
                            'url': entry.get('link', ''),
                            'published_at': entry.get('published', entry.get('updated', '')),
                            'source': f"RSS - {feed_data.feed.get('title', 'Unknown')}",
                            'description': entry.get('summary', entry.get('description', ''))[:200]
                        }
                        
                        # Only add if tech-related
                        if self._is_tech_related(article_data):
                            articles.append(article_data)
                        
            except Exception as e:
                print(f"Failed to fetch RSS feed {feed_url}: {e}")
                continue
        
        return articles
    
    def fetch_all_sources(self, date: str) -> List[Dict]:
        """Fetch news from all sources and combine results."""
        print(f"Fetching news for {date}...")
        
        all_articles = []
        
        # Fetch from NewsAPI
        print("Fetching from NewsAPI...")
        newsapi_articles = self.fetch_newsapi(date)
        all_articles.extend(newsapi_articles)
        print(f"NewsAPI: {len(newsapi_articles)} articles")
        
        # Fetch from Guardian
        print("Fetching from Guardian...")
        guardian_articles = self.fetch_guardian(date)
        all_articles.extend(guardian_articles)
        print(f"Guardian: {len(guardian_articles)} articles")
        
        # Fetch from RSS feeds
        print("Fetching from RSS feeds...")
        rss_articles = self.fetch_rss_feeds(date)
        all_articles.extend(rss_articles)
        print(f"RSS feeds: {len(rss_articles)} articles")
        
        # Filter out articles with missing required fields
        valid_articles = []
        for article in all_articles:
            if article.get('title') and article.get('url') and article.get('source'):
                valid_articles.append(article)
        
        print(f"Total valid articles: {len(valid_articles)}")
        
        # Save to JSON file
        output_file = f"raw_{date}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(valid_articles, f, ensure_ascii=False, indent=2)
        
        print(f"Results saved to {output_file}")
        return valid_articles


def main():
    """Command line interface."""
    if len(sys.argv) != 2:
        print("Usage: python -m news_bot.fetcher YYYY-MM-DD")
        sys.exit(1)
    
    date = sys.argv[1]
    
    # Validate date format
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        print("Error: Date must be in YYYY-MM-DD format")
        sys.exit(1)
    
    fetcher = NewsFetcher()
    articles = fetcher.fetch_all_sources(date)
    
    if len(articles) >= 20:
        print(f"✅ Success: Fetched {len(articles)} articles")
    else:
        print(f"⚠️  Warning: Only fetched {len(articles)} articles (expected ≥20)")


if __name__ == "__main__":
    main()