"""
CLI orchestrator for the entire news processing pipeline.
Executes the complete workflow: fetcher → dedup → summarizer → writer → publisher
"""

import argparse
import sys
import time
import os
from datetime import datetime, date
from pathlib import Path

# Import all pipeline modules
from .fetcher import NewsFetcher
from .dedup import NewsDeduplicator
from .summarizer import NewsSummarizer
from .writer import NewsWriter
from .publisher import NewsPublisher


class NewsJob:
    def __init__(self, target_date: str, dry_run: bool = False):
        """
        Initialize the news processing job.
        
        Args:
            target_date: Date string in YYYY-MM-DD format
            dry_run: If True, skip the publisher step
        """
        self.target_date = target_date
        self.dry_run = dry_run
        self.total_start_time = time.time()
        
        print(f"🚀 Starting news processing job for {target_date}")
        if dry_run:
            print("🔍 Running in DRY-RUN mode (publisher step will be skipped)")
        print()
    
    def log_step(self, step_name: str, start_time: float, success: bool = True):
        """Log step completion with timing information."""
        duration = time.time() - start_time
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status} {step_name} completed in {duration:.2f}s")
        print()
    
    def run_fetcher(self) -> bool:
        """Execute the fetcher step."""
        print("=== Step 1: News Fetching ===")
        start_time = time.time()
        
        try:
            fetcher = NewsFetcher()
            articles = fetcher.fetch_all_sources(self.target_date)
            
            # Save to file
            output_file = f"raw_{self.target_date}.json"
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            
            print(f"Fetched {len(articles)} articles")
            self.log_step("News Fetching", start_time)
            return True
            
        except Exception as e:
            print(f"Error in fetcher: {e}")
            self.log_step("News Fetching", start_time, success=False)
            return False
    
    def run_deduplicator(self) -> bool:
        """Execute the deduplicator step."""
        print("=== Step 2: Deduplication ===")
        start_time = time.time()
        
        try:
            input_file = f"raw_{self.target_date}.json"
            output_file = f"dedup_{self.target_date}.json"
            
            deduplicator = NewsDeduplicator()
            unique_articles = deduplicator.deduplicate_articles(input_file, output_file)
            
            print(f"Deduplicated to {len(unique_articles)} unique articles")
            self.log_step("Deduplication", start_time)
            return True
            
        except Exception as e:
            print(f"Error in deduplicator: {e}")
            self.log_step("Deduplication", start_time, success=False)
            return False
    
    def run_summarizer(self) -> bool:
        """Execute the summarizer step."""
        print("=== Step 3: AI Summarization ===")
        start_time = time.time()
        
        try:
            # Use dedup file if selector not implemented
            input_file = f"select_{self.target_date}.json"
            if not os.path.exists(input_file):
                input_file = f"dedup_{self.target_date}.json"
                print(f"Using {input_file} (selector not implemented)")
            
            output_file = f"summary_{self.target_date}.json"
            
            summarizer = NewsSummarizer()
            summarized_articles = summarizer.summarize_articles(input_file, output_file)
            
            print(f"Summarized {len(summarized_articles)} articles")
            print(f"Token usage: {summarizer.total_tokens_used}")
            self.log_step("AI Summarization", start_time)
            return True
            
        except Exception as e:
            print(f"Error in summarizer: {e}")
            self.log_step("AI Summarization", start_time, success=False)
            return False
    
    def run_writer(self) -> bool:
        """Execute the writer step."""
        print("=== Step 4: Markdown Generation ===")
        start_time = time.time()
        
        try:
            input_file = f"summary_{self.target_date}.json"
            
            writer = NewsWriter()
            output_file = writer.write_markdown_file(input_file, self.target_date)
            
            print(f"Generated markdown file: {output_file}")
            self.log_step("Markdown Generation", start_time)
            return True
            
        except Exception as e:
            print(f"Error in writer: {e}")
            self.log_step("Markdown Generation", start_time, success=False)
            return False
    
    def run_publisher(self) -> bool:
        """Execute the publisher step."""
        print("=== Step 5: Git Publishing ===")
        start_time = time.time()
        
        try:
            commit_msg = f"Add daily news for {self.target_date} - Auto-generated content"
            
            publisher = NewsPublisher()
            success = publisher.publish(commit_msg, auto_push=True)
            
            if success:
                print("Successfully published to blog repository")
                self.log_step("Git Publishing", start_time)
                return True
            else:
                print("Publisher reported failure")
                self.log_step("Git Publishing", start_time, success=False)
                return False
                
        except Exception as e:
            print(f"Error in publisher: {e}")
            self.log_step("Git Publishing", start_time, success=False)
            return False
    
    def run_pipeline(self) -> bool:
        """Execute the complete pipeline."""
        steps = [
            ("Fetcher", self.run_fetcher),
            ("Deduplicator", self.run_deduplicator),
            ("Summarizer", self.run_summarizer),
            ("Writer", self.run_writer)
        ]
        
        # Add publisher step if not dry run
        if not self.dry_run:
            steps.append(("Publisher", self.run_publisher))
        else:
            print("🔍 Skipping Publisher step (dry-run mode)")
            print()
        
        # Execute all steps
        for step_name, step_func in steps:
            if not step_func():
                print(f"❌ Pipeline failed at {step_name} step")
                return False
        
        # Calculate total time
        total_duration = time.time() - self.total_start_time
        print("=" * 50)
        print(f"🎉 Pipeline completed successfully in {total_duration:.2f}s")
        
        if self.dry_run:
            print("🔍 This was a dry-run. No changes were published.")
        else:
            print("📝 Changes have been committed and pushed to the blog repository.")
            
        return True


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description="Execute the complete news processing pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m news_bot.job --date 2025-07-25
  python -m news_bot.job --date 2025-07-25 --dry-run
  python -m news_bot.job  # Uses today's date
        """
    )
    
    parser.add_argument(
        "--date",
        default=date.today().strftime("%Y-%m-%d"),
        help="Target date in YYYY-MM-DD format (default: today)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip the publisher step (for testing)"
    )
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("❌ Error: Date must be in YYYY-MM-DD format")
        sys.exit(1)
    
    # Check if we're in the right directory
    if not Path("config.json").exists():
        print("❌ Error: config.json not found")
        print("Please run this command from the astro-news-bot root directory")
        sys.exit(1)
    
    try:
        job = NewsJob(args.date, args.dry_run)
        success = job.run_pipeline()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()