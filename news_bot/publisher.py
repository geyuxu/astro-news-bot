"""
Git publisher for automated commits and pushes.
Handles automatic Git operations for news content publishing.
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict


class NewsPublisher:
    def __init__(self, repo_path: Optional[str] = None, config_file: str = "config.json"):
        """
        Initialize the news publisher.
        
        Args:
            repo_path: Path to the git repository (if None, reads from config)
            config_file: Path to configuration file
        """
        self.config = self.load_config(config_file)
        
        if repo_path:
            self.repo_path = Path(repo_path)
        else:
            # Get blog directory from config and find git root
            blog_dir = self.get_blog_directory()
            self.repo_path = self.find_git_root(blog_dir)
            
        print(f"Publisher will operate in git repository: {self.repo_path}")
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Config file {config_file} not found, using defaults")
            return {
                "output_config": {
                    "blog_content_dir": "/Users/geyuxu/repo/blog/geyuxu.com/src/content/news",
                    "use_blog_dir": True
                }
            }
    
    def get_blog_directory(self) -> Path:
        """Get the blog directory from configuration."""
        output_config = self.config.get("output_config", {})
        
        if output_config.get("use_blog_dir", False):
            blog_dir = output_config.get("blog_content_dir", "content/news")
        else:
            blog_dir = output_config.get("local_content_dir", "content/news")
            
        return Path(blog_dir)
    
    def find_git_root(self, start_path: Path) -> Path:
        """
        Find the git repository root starting from the given path.
        
        Args:
            start_path: Starting directory path
            
        Returns:
            Path to git repository root
        """
        current_path = Path(start_path).resolve()
        
        # Walk up the directory tree to find .git
        while current_path != current_path.parent:
            if (current_path / ".git").exists():
                return current_path
            current_path = current_path.parent
        
        # If no .git found, try the parent of blog content directory
        # For example: /Users/geyuxu/repo/blog/geyuxu.com/src/content/news -> /Users/geyuxu/repo/blog/geyuxu.com
        blog_content_dir = self.get_blog_directory()
        possible_repo_root = blog_content_dir.parent.parent.parent  # ../../../ from news directory
        
        if (possible_repo_root / ".git").exists():
            return possible_repo_root
            
        raise FileNotFoundError(f"No git repository found from {start_path} upwards")
        
    def check_git_status(self) -> bool:
        """
        Check if there are any changes to commit.
        
        Returns:
            True if there are changes, False otherwise
        """
        try:
            # Check for both staged and unstaged changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # If output is empty, no changes
            has_changes = bool(result.stdout.strip())
            
            if has_changes:
                print("Git status shows changes to commit:")
                print(result.stdout)
            else:
                print("No changes detected in git working directory")
                
            return has_changes
            
        except subprocess.CalledProcessError as e:
            print(f"Error checking git status: {e}")
            return False
    
    def stage_changes(self) -> bool:
        """
        Stage all changes for commit.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "add", "."],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            print("Successfully staged all changes")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error staging changes: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")
            return False
    
    def commit_changes(self, commit_msg: str) -> bool:
        """
        Commit staged changes with the provided message.
        
        Args:
            commit_msg: Commit message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            print(f"Successfully committed changes: {commit_msg}")
            if result.stdout:
                print(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e:
            # If nothing to commit, this is not an error condition
            if "nothing to commit" in e.stdout or "nothing to commit" in e.stderr:
                print("Nothing to commit, working tree clean")
                return True
            
            print(f"Error committing changes: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")
            return False
    
    def push_changes(self) -> bool:
        """
        Push committed changes to remote repository.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "push"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            print("Successfully pushed changes to remote repository")
            if result.stdout:
                print(result.stdout)
            if result.stderr:  # Git push info often goes to stderr
                print(result.stderr)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error pushing changes: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")
            return False
    
    def publish(self, commit_msg: str, auto_push: bool = True) -> bool:
        """
        Execute the complete publish workflow: stage, commit, and optionally push.
        
        Args:
            commit_msg: Commit message
            auto_push: Whether to automatically push to remote (default: True)
            
        Returns:
            True if all operations successful, False otherwise
        """
        print(f"Starting publish workflow in: {self.repo_path}")
        print(f"Commit message: {commit_msg}")
        
        # Check if there are changes to commit
        if not self.check_git_status():
            print("✅ No changes to publish, exiting successfully")
            return True
        
        # Stage changes
        if not self.stage_changes():
            print("❌ Failed to stage changes")
            return False
        
        # Commit changes
        if not self.commit_changes(commit_msg):
            print("❌ Failed to commit changes")
            return False
        
        # Push changes if requested
        if auto_push:
            if not self.push_changes():
                print("❌ Failed to push changes")
                return False
        else:
            print("📝 Changes committed but not pushed (auto_push=False)")
        
        print("✅ Publish workflow completed successfully")
        return True


def main():
    """Command line interface."""
    if len(sys.argv) < 2:
        print("Usage: python -m news_bot.publisher 'commit message' [--no-push]")
        print("Examples:")
        print("  python -m news_bot.publisher 'Add daily news for 2025-07-25'")
        print("  python -m news_bot.publisher 'Update news content' --no-push")
        sys.exit(1)
    
    commit_msg = sys.argv[1]
    auto_push = "--no-push" not in sys.argv
    
    # Check if config file exists
    if not Path("config.json").exists():
        print("❌ Error: config.json not found")
        print("Please run this command from the astro-news-bot root directory")
        sys.exit(1)
    
    try:
        publisher = NewsPublisher()
        success = publisher.publish(commit_msg, auto_push=auto_push)
        
        if not success:
            print("❌ Publisher workflow failed")
            sys.exit(1)
        else:
            print("✅ Publisher workflow completed successfully")
            
    except Exception as e:
        print(f"❌ Unexpected error during publishing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()