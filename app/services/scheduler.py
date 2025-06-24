"""
Background scheduler for automatic scraping
"""

import asyncio
import schedule
import time
from threading import Thread
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from app.scrapers.manager import ScraperManager
from app.utils.logger import logger

load_dotenv()

class BackgroundScheduler:
    """Background scheduler for periodic scraping tasks"""
    
    def __init__(self):
        self.scraper_manager = None
        self.running = False
        self.thread = None
    
    async def initialize(self):
        """Initialize the scheduler"""
        self.scraper_manager = ScraperManager()
        await self.scraper_manager.initialize()
        logger.info("Background scheduler initialized")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.scraper_manager:
            await self.scraper_manager.close()
        self.running = False
        logger.info("Background scheduler cleaned up")
    
    async def run_scheduled_scrape(self):
        """Run a scheduled scraping task"""
        try:
            logger.info("Starting scheduled scraping task")
            
            if not self.scraper_manager:
                await self.initialize()
            
            results = await self.scraper_manager.scrape_all_sources()
            
            total_scraped = 0
            total_saved = 0
            for source, result in results.items():
                if result.get("status") == "success":
                    scraped = result.get("items_scraped", 0)
                    saved = result.get("items_saved", 0)
                    total_scraped += scraped
                    total_saved += saved
                    logger.info(f"Scheduled scrape - {source}: {scraped} scraped, {saved} saved")
                else:
                    logger.error(f"Scheduled scrape error - {source}: {result.get('error')}")
            
            logger.info(f"Scheduled scraping completed: {total_scraped} total scraped, {total_saved} total saved")
            
        except Exception as e:
            logger.error(f"Error in scheduled scraping: {str(e)}")
    
    def setup_schedule(self):
        """Setup the scraping schedule"""
        # Schedule scraping every 4 hours
        schedule.every(4).hours.do(
            lambda: asyncio.create_task(self.run_scheduled_scrape())
        )
        
        # Schedule daily cleanup (optional - could remove old data, compress logs, etc.)
        schedule.every().day.at("02:00").do(self.daily_maintenance)
        
        logger.info("Scraping schedule configured: every 4 hours + daily maintenance at 2 AM")
    
    def daily_maintenance(self):
        """Daily maintenance tasks"""
        try:
            logger.info("Running daily maintenance tasks")
            
            # Could add tasks like:
            # - Clean up old log files
            # - Compress old data
            # - Update statistics
            # - Send daily reports
            
            logger.info("Daily maintenance completed")
            
        except Exception as e:
            logger.error(f"Error in daily maintenance: {str(e)}")
    
    def run_scheduler(self):
        """Run the scheduler in a loop"""
        logger.info("Starting background scheduler loop")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        
        logger.info("Background scheduler loop stopped")
    
    def start(self):
        """Start the background scheduler"""
        if not self.running:
            self.running = True
            self.setup_schedule()
            
            # Run initial scraping task
            asyncio.create_task(self.run_scheduled_scrape())
            
            # Start scheduler thread
            self.thread = Thread(target=self.run_scheduler, daemon=True)
            self.thread.start()
            
            logger.info("Background scheduler started")
    
    def stop(self):
        """Stop the background scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Background scheduler stopped")

# Global scheduler instance
background_scheduler = BackgroundScheduler()

async def start_background_tasks():
    """Start background tasks (called from main app)"""
    await background_scheduler.initialize()
    background_scheduler.start()

async def stop_background_tasks():
    """Stop background tasks (called from main app)"""
    background_scheduler.stop()
    await background_scheduler.cleanup()
