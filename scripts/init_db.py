#!/usr/bin/env python3
"""
Database initialization script for DeFi Guard OSINT API
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import create_tables, SessionLocal, ThreatIntelDB
from app.scrapers.manager import ScraperManager
from app.utils.logger import logger

async def initialize_database():
    """Initialize the database with tables"""
    try:
        logger.info("Creating database tables...")
        create_tables()
        logger.info("Database tables created successfully")
        
        # Check if we have any existing data
        db = SessionLocal()
        count = db.query(ThreatIntelDB).count()
        logger.info(f"Current database contains {count} threat intelligence items")
        db.close()
        
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

async def run_initial_scrape():
    """Run initial scraping to populate the database"""
    try:
        logger.info("Starting initial threat intelligence scraping...")
        
        scraper_manager = ScraperManager()
        await scraper_manager.initialize()
        
        # Run scraping for all sources
        results = await scraper_manager.scrape_all_sources()
        
        await scraper_manager.close()
        
        # Log results
        total_scraped = 0
        for source, result in results.items():
            if result.get("status") == "success":
                scraped = result.get("items_scraped", 0)
                saved = result.get("items_saved", 0)
                total_scraped += saved
                logger.info(f"{source}: {scraped} items scraped, {saved} items saved")
            else:
                logger.error(f"{source}: {result.get('error', 'Unknown error')}")
        
        logger.info(f"Initial scraping completed. Total items saved: {total_scraped}")
        return True
        
    except Exception as e:
        logger.error(f"Error during initial scraping: {str(e)}")
        return False

async def main():
    """Main initialization function"""
    logger.info("=== DeFi Guard OSINT API Initialization ===")
    
    # Initialize database
    db_success = await initialize_database()
    if not db_success:
        logger.error("Database initialization failed")
        sys.exit(1)
    
    # Ask user if they want to run initial scrape
    print("\nWould you like to run initial scraping to populate the database? (y/n): ", end="")
    choice = input().lower().strip()
    
    if choice in ['y', 'yes']:
        scrape_success = await run_initial_scrape()
        if not scrape_success:
            logger.warning("Initial scraping failed, but database is ready")
    else:
        logger.info("Skipping initial scraping")
    
    logger.info("=== Initialization Complete ===")
    logger.info("You can now start the API server with:")
    logger.info("  uvicorn app.main:app --host 0.0.0.0 --port 8000")
    logger.info("Or use Docker:")
    logger.info("  docker-compose up")

if __name__ == "__main__":
    asyncio.run(main())
