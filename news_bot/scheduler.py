"""
News Bot Scheduler - A long-running process for scheduled news processing.
Similar to Spring Boot's @Scheduled functionality in Java.
"""

import os
import sys
import signal
import time
import json
import logging
import argparse
import atexit
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from .job import NewsJob


class NewsScheduler:
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the news scheduler.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = self.load_config()
        self.scheduler = None
        self.pid_file = "news_scheduler.pid"
        self.running = False
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        # Note: atexit.register will be set only when scheduler is actually started
        
        self.logger.info("News Scheduler initialized")
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_file} not found, using defaults")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default scheduler configuration."""
        return {
            "scheduler_config": {
                "enabled": True,
                "timezone": "Asia/Shanghai",
                "cron_expression": "0 8 * * *",  # Every day at 08:00
                "dry_run": False,
                "max_retries": 3,
                "retry_interval_minutes": 30
            },
            "logging_config": {
                "level": "INFO",
                "log_dir": "logs",
                "log_file": "scheduler.log",
                "max_bytes": 10485760,  # 10MB
                "backup_count": 5
            }
        }
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get("logging_config", {})
        
        # Create logs directory
        log_dir = log_config.get("log_dir", "logs")
        Path(log_dir).mkdir(exist_ok=True)
        
        # Configure logging
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = Path(log_dir) / log_config.get("log_file", "scheduler.log")
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")
        self.shutdown()
    
    def create_pid_file(self):
        """Create PID file for process management."""
        pid = os.getpid()
        with open(self.pid_file, 'w') as f:
            f.write(str(pid))
        self.logger.info(f"Created PID file: {self.pid_file} (PID: {pid})")
    
    def remove_pid_file(self):
        """Remove PID file."""
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
                self.logger.info(f"Removed PID file: {self.pid_file}")
        except Exception as e:
            self.logger.error(f"Error removing PID file: {e}")
    
    def is_running(self) -> bool:
        """Check if scheduler is already running by checking PID file."""
        if not os.path.exists(self.pid_file):
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is still running
            os.kill(pid, 0)  # This will raise OSError if process doesn't exist
            return True
        except (OSError, ValueError, FileNotFoundError):
            # Process is not running or PID file is corrupted
            self.remove_pid_file()
            return False
    
    def execute_news_job(self):
        """Execute the news processing job."""
        try:
            self.logger.info("Starting scheduled news processing job...")
            start_time = time.time()
            
            scheduler_config = self.config.get("scheduler_config", {})
            dry_run = scheduler_config.get("dry_run", False)
            
            # Get current date
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Execute the job
            job = NewsJob(current_date, dry_run=dry_run)
            success = job.run_pipeline()
            
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"News processing job completed successfully in {duration:.2f}s")
            else:
                self.logger.error(f"News processing job failed after {duration:.2f}s")
                
        except Exception as e:
            self.logger.error(f"Error executing news job: {e}", exc_info=True)
    
    def job_listener(self, event):
        """Listen to job execution events."""
        if event.exception:
            self.logger.error(f"Job {event.job_id} crashed: {event.exception}")
        else:
            self.logger.info(f"Job {event.job_id} executed successfully")
    
    def start(self):
        """Start the scheduler."""
        if self.is_running():
            self.logger.error("Scheduler is already running")
            return False
        
        scheduler_config = self.config.get("scheduler_config", {})
        
        if not scheduler_config.get("enabled", True):
            self.logger.info("Scheduler is disabled in configuration")
            return False
        
        # Create PID file and register cleanup
        self.create_pid_file()
        atexit.register(self.shutdown)  # Only register when actually starting
        
        try:
            # Initialize scheduler
            timezone = scheduler_config.get("timezone", "Asia/Shanghai")
            self.scheduler = BackgroundScheduler(timezone=timezone)
            
            # Add job listener
            self.scheduler.add_listener(self.job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
            
            # Parse cron expression and add job
            cron_expr = scheduler_config.get("cron_expression", "0 8 * * *")
            cron_parts = cron_expr.split()
            
            if len(cron_parts) == 5:
                minute, hour, day, month, day_of_week = cron_parts
                
                self.scheduler.add_job(
                    func=self.execute_news_job,
                    trigger=CronTrigger(
                        minute=minute,
                        hour=hour,
                        day=day,
                        month=month,
                        day_of_week=day_of_week,
                        timezone=timezone
                    ),
                    id='news_processing_job',
                    name='Daily News Processing',
                    max_instances=1,
                    replace_existing=True
                )
                
                self.logger.info(f"Scheduled job with cron expression: {cron_expr}")
                self.logger.info(f"Timezone: {timezone}")
                self.logger.info(f"Dry run mode: {scheduler_config.get('dry_run', False)}")
                
                # Start the scheduler (non-blocking)
                self.scheduler.start()
                self.running = True
                self.logger.info("News Scheduler started successfully (daemon mode)")
                
                # Print next execution times after scheduler starts
                jobs = self.scheduler.get_jobs()
                if jobs:
                    try:
                        next_run = jobs[0].next_run_time
                        self.logger.info(f"Next execution scheduled for: {next_run}")
                    except AttributeError:
                        self.logger.info("Scheduler started, next execution time will be determined automatically")
                
                # Keep the process alive in daemon mode
                print(f"✅ Scheduler started in daemon mode")
                print(f"📅 Next execution: {jobs[0].next_run_time if jobs else 'TBD'}")
                print(f"📋 Use 'python -m news_bot.scheduler stop' to stop the scheduler")
                
                # Keep process alive
                try:
                    while self.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.logger.info("Received keyboard interrupt, shutting down...")
                    self.shutdown()
                
            else:
                self.logger.error(f"Invalid cron expression: {cron_expr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting scheduler: {e}", exc_info=True)
            self.remove_pid_file()
            return False
        
        return True
    
    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        if self.running:
            self.logger.info("Shutting down scheduler...")
            self.running = False
            
            if self.scheduler:
                try:
                    self.scheduler.shutdown(wait=True)
                    self.logger.info("Scheduler stopped successfully")
                except Exception as e:
                    self.logger.error(f"Error stopping scheduler: {e}")
        
        self.remove_pid_file()
        self.logger.info("News Scheduler shutdown complete")
    
    def stop(self):
        """Stop the scheduler (external command)."""
        if not self.is_running():
            print("Scheduler is not running")
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            print(f"Stopping scheduler process (PID: {pid})...")
            os.kill(pid, signal.SIGTERM)
            
            # Wait for process to shutdown
            for _ in range(10):  # Wait up to 10 seconds
                if not self.is_running():
                    print("Scheduler stopped successfully")
                    return True
                time.sleep(1)
            
            # Force kill if still running
            print("Force stopping scheduler...")
            os.kill(pid, signal.SIGKILL)
            self.remove_pid_file()
            return True
            
        except Exception as e:
            print(f"Error stopping scheduler: {e}")
            return False
    
    def status(self):
        """Check scheduler status."""
        if self.is_running():
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            print(f"Scheduler is running (PID: {pid})")
            return True
        else:
            print("Scheduler is not running")
            return False
    
    def run_now(self):
        """Execute news job immediately (for testing)."""
        print("Executing news processing job immediately...")
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.execute_news_job()


def main():
    """Command line interface for scheduler management."""
    parser = argparse.ArgumentParser(
        description="News Bot Scheduler - Process management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  start     Start the scheduler process
  stop      Stop the scheduler process  
  restart   Restart the scheduler process
  status    Check scheduler status
  run-now   Execute news job immediately (for testing)

Examples:
  python -m news_bot.scheduler start
  python -m news_bot.scheduler stop
  python -m news_bot.scheduler status
  python -m news_bot.scheduler run-now
        """
    )
    
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'restart', 'status', 'run-now'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--config',
        default='config.json',
        help='Configuration file path (default: config.json)'
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path(args.config).exists():
        print(f"❌ Error: {args.config} not found")
        print("Please run this command from the astro-news-bot root directory")
        sys.exit(1)
    
    scheduler = NewsScheduler(args.config)
    
    try:
        if args.command == 'start':
            if scheduler.start():
                sys.exit(0)
            else:
                sys.exit(1)
                
        elif args.command == 'stop':
            if scheduler.stop():
                sys.exit(0)
            else:
                sys.exit(1)
                
        elif args.command == 'restart':
            print("Restarting scheduler...")
            scheduler.stop()
            time.sleep(2)
            if scheduler.start():
                sys.exit(0)
            else:
                sys.exit(1)
                
        elif args.command == 'status':
            if scheduler.status():
                sys.exit(0)
            else:
                sys.exit(1)
                
        elif args.command == 'run-now':
            scheduler.run_now()
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⏹️  Command interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()