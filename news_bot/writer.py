"""
Markdown generation with YAML front-matter for Astro blog.
Converts summarized news articles into properly formatted blog posts.
"""

import json
import sys
import os
from datetime import datetime
from typing import List, Dict
from pathlib import Path
import yaml


class NewsWriter:
    def __init__(self):
        """Initialize the news writer."""
        self.topic_keywords = {
            "人工智能": ["人工智能", "ai", "机器学习", "深度学习", "神经网络", "gpt", "llm", "chatgpt", "openai", "anthropic", "claude"],
            "移动技术": ["苹果", "iphone", "ios", "android", "移动应用", "app store", "智能手机", "平板", "ipad"],
            "自动驾驶": ["自动驾驶", "特斯拉", "robotaxi", "无人驾驶", "自动驾驶汽车", "lyft", "uber"],
            "云计算": ["云计算", "aws", "azure", "google cloud", "微软", "云服务", "数据中心"],
            "芯片技术": ["芯片", "处理器", "nvidia", "intel", "amd", "gpu", "cpu", "半导体", "quantum"],
            "创业投资": ["创业", "投资", "融资", "vc", "startup", "独角兽"],
            "网络安全": ["网络安全", "cybersecurity", "数据泄露", "隐私", "安全漏洞"],
            "区块链": ["区块链", "加密货币", "比特币", "以太坊", "crypto", "web3"],
            "科学研究": ["研究", "科学", "发现", "突破", "实验", "nature", "science"],
            "其他科技": []  # 默认分类
        }
    
    def categorize_article(self, article: Dict) -> str:
        """
        Categorize an article based on its content.
        
        Args:
            article: Article dictionary with title, summary, bullets
            
        Returns:
            Category name in Chinese
        """
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        bullets = [tag.lower() for tag in article.get('bullets', [])]
        
        content = f"{title} {summary} {' '.join(bullets)}"
        
        # Find the best matching category
        category_scores = {}
        for category, keywords in self.topic_keywords.items():
            if category == "其他科技":
                continue
            score = sum(1 for keyword in keywords if keyword.lower() in content)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        else:
            return "其他科技"
    
    def group_articles_by_topic(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group articles by topic categories.
        
        Args:
            articles: List of summarized articles
            
        Returns:
            Dictionary with categories as keys and article lists as values
        """
        grouped = {}
        for article in articles:
            category = self.categorize_article(article)
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(article)
        
        return grouped
    
    def generate_yaml_frontmatter(self, date: str, articles: List[Dict]) -> str:
        """
        Generate YAML front-matter for the markdown file.
        
        Args:
            date: Date string in YYYY-MM-DD format
            articles: List of all articles
            
        Returns:
            YAML front-matter string
        """
        # Get first article's summary for description
        first_summary = articles[0].get('summary', '') if articles else "今日科技新闻速览"
        
        # Collect all unique tags
        all_tags = set()
        for article in articles:
            all_tags.update(article.get('bullets', []))
        
        # Limit to most relevant tags
        sorted_tags = sorted(list(all_tags))[:10]
        
        frontmatter = {
            'title': f"每日新闻速览 · {date}",
            'pubDate': date,
            'description': first_summary[:100] + ("..." if len(first_summary) > 100 else ""),
            'tags': ["News", "Daily"] + sorted_tags,
            'layout': "news"
        }
        
        return yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
    
    def generate_markdown_content(self, grouped_articles: Dict[str, List[Dict]]) -> str:
        """
        Generate markdown content from grouped articles.
        
        Args:
            grouped_articles: Articles grouped by category
            
        Returns:
            Markdown content string
        """
        content_lines = []
        
        for category, articles in grouped_articles.items():
            if not articles:
                continue
                
            # Add category header
            content_lines.append(f"## {category}")
            content_lines.append("")
            
            # Add articles in this category
            for article in articles:
                title = article.get('title', '')
                summary = article.get('summary', '')
                url = article.get('url', '')
                bullets = article.get('bullets', [])
                source = article.get('source', '')
                
                # Format article entry
                content_lines.append(f"- **{title}**")
                content_lines.append(f"  {summary}")
                if bullets:
                    tags_str = " · ".join(bullets[:5])  # Limit to 5 tags
                    content_lines.append(f"  *标签：{tags_str}*")
                content_lines.append(f"  [阅读原文]({url}) | 来源：{source}")
                content_lines.append("")
        
        return "\n".join(content_lines)
    
    def create_output_directory(self, date: str) -> Path:
        """
        Create the output directory structure.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            Path to the created directory
        """
        output_dir = Path(f"content/news/{date}")
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def write_markdown_file(self, input_file: str, date: str) -> str:
        """
        Generate markdown file from summarized articles.
        
        Args:
            input_file: Path to summary JSON file
            date: Date string in YYYY-MM-DD format
            
        Returns:
            Path to generated markdown file
        """
        # Load articles from input file
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        if not articles:
            raise ValueError("No articles found in input file")
        
        print(f"Processing {len(articles)} articles for markdown generation...")
        
        # Group articles by topic
        grouped_articles = self.group_articles_by_topic(articles)
        print(f"Grouped into {len(grouped_articles)} categories:")
        for category, category_articles in grouped_articles.items():
            print(f"  - {category}: {len(category_articles)} articles")
        
        # Generate YAML front-matter
        frontmatter = self.generate_yaml_frontmatter(date, articles)
        
        # Generate markdown content
        content = self.generate_markdown_content(grouped_articles)
        
        # Create output directory
        output_dir = self.create_output_directory(date)
        output_file = output_dir / "index.md"
        
        # Write the complete markdown file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("---\n")
            f.write(frontmatter)
            f.write("---\n\n")
            f.write(content)
        
        print(f"Markdown file generated successfully:")
        print(f"  Output file: {output_file}")
        print(f"  Categories: {', '.join(grouped_articles.keys())}")
        print(f"  Total articles: {len(articles)}")
        
        return str(output_file)


def main():
    """Command line interface."""
    if len(sys.argv) != 2:
        print("Usage: python -m news_bot.writer YYYY-MM-DD")
        sys.exit(1)
    
    date = sys.argv[1]
    
    # Validate date format
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        print("Error: Date must be in YYYY-MM-DD format")
        sys.exit(1)
    
    input_file = f"summary_{date}.json"
    
    try:
        writer = NewsWriter()
        output_file = writer.write_markdown_file(input_file, date)
        
        # Verify the generated file
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                print(f"✅ Success: Generated {len(lines)} lines of markdown")
                print(f"📄 File location: {output_file}")
                
                # Check for required sections
                if '---' in content and '##' in content:
                    print("✅ File includes proper YAML front-matter and section headers")
                else:
                    print("⚠️  Warning: File may be missing required structure")
        else:
            print("❌ Error: Output file was not created")
            
    except Exception as e:
        print(f"❌ Error during markdown generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()