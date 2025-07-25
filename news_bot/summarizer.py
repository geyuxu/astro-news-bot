"""
LLM-powered news summarization using OpenAI GPT-4o.
Generates Chinese summaries and bullet point tags for news articles.
"""

import json
import sys
import os
import time
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class NewsSummarizer:
    def __init__(self, model_name: str = "gpt-4o"):
        """
        Initialize the summarizer with OpenAI client.
        
        Args:
            model_name: OpenAI model to use for summarization
        """
        self.model_name = model_name
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.total_tokens_used = 0
        print(f"Initialized summarizer with model: {model_name}")
    
    def create_summary_prompt(self, article: Dict) -> str:
        """
        Create a prompt for summarizing an article.
        
        Args:
            article: Article dictionary with title, description, etc.
            
        Returns:
            Formatted prompt string
        """
        title = article.get('title', '')
        description = article.get('description', '')
        url = article.get('url', '')
        source = article.get('source', '')
        
        prompt = f"""请为以下科技新闻撰写中文摘要和标签：

标题：{title}
描述：{description}
来源：{source}
链接：{url}

请按照以下格式回复：

摘要：[用2-3句话总结这条新闻的核心内容，使用简洁明了的中文]

标签：[提供3-5个相关的中文标签，用逗号分隔，例如：人工智能,苹果,新产品发布,移动技术]

要求：
1. 摘要要准确传达新闻的关键信息和影响
2. 使用通俗易懂的中文表达
3. 标签应该涵盖技术领域、公司名称、产品类型等关键词
4. 保持客观中性的语调"""

        return prompt
    
    def summarize_article(self, article: Dict, max_retries: int = 3) -> Dict:
        """
        Summarize a single article using OpenAI API.
        
        Args:
            article: Article dictionary
            max_retries: Maximum number of retry attempts
            
        Returns:
            Article dictionary with added summary and bullets fields
        """
        prompt = self.create_summary_prompt(article)
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system", 
                            "content": "你是一个专业的科技新闻编辑，擅长将英文科技新闻总结成简洁明了的中文摘要。"
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.3,
                    timeout=30
                )
                
                content = response.choices[0].message.content.strip()
                tokens_used = response.usage.total_tokens
                self.total_tokens_used += tokens_used
                
                # Parse the response to extract summary and bullets
                summary, bullets = self.parse_llm_response(content)
                
                # Add summary and bullets to article
                enhanced_article = article.copy()
                enhanced_article['summary'] = summary
                enhanced_article['bullets'] = bullets
                
                print(f"✅ Summarized: {article.get('title', '')[:50]}... (Tokens: {tokens_used})")
                return enhanced_article
                
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"❌ Failed to summarize after {max_retries} attempts: {e}")
                    # Return article with fallback summary
                    fallback_article = article.copy()
                    fallback_article['summary'] = f"无法生成摘要：{article.get('description', '')[:100]}..."
                    fallback_article['bullets'] = ["科技", "新闻"]
                    return fallback_article
                else:
                    wait_time = 2 ** attempt
                    print(f"⚠️  Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
    
    def parse_llm_response(self, content: str) -> tuple[str, List[str]]:
        """
        Parse LLM response to extract summary and bullets.
        
        Args:
            content: Raw LLM response content
            
        Returns:
            Tuple of (summary, bullets_list)
        """
        lines = content.strip().split('\n')
        summary = ""
        bullets = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('摘要：'):
                summary = line.replace('摘要：', '').strip()
                current_section = 'summary'
            elif line.startswith('标签：'):
                tags_text = line.replace('标签：', '').strip()
                # Handle both comma and Chinese comma separators
                if '，' in tags_text:
                    bullets = [tag.strip() for tag in tags_text.split('，') if tag.strip()]
                else:
                    bullets = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
                current_section = 'bullets'
            elif current_section == 'summary' and not summary:
                summary = line
            elif current_section == 'bullets' and not bullets:
                # Handle both comma and Chinese comma separators
                if '，' in line:
                    bullets = [tag.strip() for tag in line.split('，') if tag.strip()]
                else:
                    bullets = [tag.strip() for tag in line.split(',') if tag.strip()]
        
        # Fallback parsing if format is not followed
        if not summary:
            # Try to find any substantial text as summary
            for line in lines:
                if len(line.strip()) > 20 and '：' not in line:
                    summary = line.strip()
                    break
            if not summary:
                summary = "摘要解析失败"
        
        if not bullets:
            bullets = ["科技", "新闻"]
        
        return summary, bullets
    
    def summarize_articles(self, input_file: str, output_file: str) -> List[Dict]:
        """
        Summarize all articles from input file and save to output file.
        
        Args:
            input_file: Path to input JSON file with selected articles
            output_file: Path to output JSON file for summarized articles
            
        Returns:
            List of summarized articles
        """
        # Load articles from input file
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        if not articles:
            print("No articles found in input file.")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return []
        
        print(f"Summarizing {len(articles)} articles...")
        
        summarized_articles = []
        for i, article in enumerate(articles, 1):
            print(f"Processing article {i}/{len(articles)}...")
            summarized_article = self.summarize_article(article)
            summarized_articles.append(summarized_article)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        # Save summarized articles
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summarized_articles, f, ensure_ascii=False, indent=2)
        
        print(f"\nSummarization completed:")
        print(f"  Articles processed: {len(summarized_articles)}")
        print(f"  Total tokens used: {self.total_tokens_used}")
        print(f"  Results saved to: {output_file}")
        
        return summarized_articles


def main():
    """Command line interface."""
    if len(sys.argv) != 2:
        print("Usage: python -m news_bot.summarizer YYYY-MM-DD")
        sys.exit(1)
    
    date = sys.argv[1]
    
    # Validate date format
    try:
        import datetime
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        print("Error: Date must be in YYYY-MM-DD format")
        sys.exit(1)
    
    input_file = f"select_{date}.json"
    output_file = f"summary_{date}.json"
    
    try:
        summarizer = NewsSummarizer()
        summarized_articles = summarizer.summarize_articles(input_file, output_file)
        
        if len(summarized_articles) > 0:
            avg_tokens = summarizer.total_tokens_used / len(summarized_articles)
            print(f"✅ Success: Summarized {len(summarized_articles)} articles")
            print(f"📊 Average tokens per article: {avg_tokens:.1f}")
            
            if summarizer.total_tokens_used > 4000:
                print(f"⚠️  Warning: Used {summarizer.total_tokens_used} tokens (target: <4000/day)")
            else:
                print(f"✅ Token usage within target: {summarizer.total_tokens_used}/4000 tokens")
        else:
            print("⚠️  Warning: No articles to summarize")
            
    except Exception as e:
        print(f"❌ Error during summarization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()