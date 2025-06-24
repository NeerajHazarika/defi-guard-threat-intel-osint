import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json
from urllib.parse import urljoin, urlparse

from app.scrapers.rekt_scraper import RektScraper
from app.scrapers.chainalysis_scraper import ChainanalysisScraper
from app.scrapers.base_scraper import BaseScraper
from app.models.threat_intel import ThreatIntelItem, RiskLevel
from app.database.database import SessionLocal, ThreatIntelDB
from app.services.protocol_classifier import protocol_classifier
from app.utils.logger import logger
from sqlalchemy.orm import Session
from sqlalchemy import and_

class ScraperManager:
    """Manages all threat intelligence scrapers"""
    
    def __init__(self):
        self.scrapers: Dict[str, BaseScraper] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self._initialize_scrapers()
    
    def _initialize_scrapers(self):
        """Initialize all available scrapers"""
        self.scrapers = {
            "rekt": RektScraper(),
            "chainalysis": ChainanalysisScraper(),
        }
        logger.info(f"Initialized {len(self.scrapers)} scrapers: {list(self.scrapers.keys())}")
    
    async def initialize(self):
        """Initialize the scraper manager"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "DeFiGuard-OSINT-Bot/1.0"}
        )
        
        # Initialize protocol classifier
        await protocol_classifier.initialize()
        
        # Initialize individual scrapers
        for scraper in self.scrapers.values():
            await scraper.initialize(self.session)
    
    async def close(self):
        """Close the scraper manager and cleanup resources"""
        if self.session:
            await self.session.close()
        
        for scraper in self.scrapers.values():
            await scraper.close()
    
    def get_available_sources(self) -> List[str]:
        """Get list of available scraper sources"""
        return list(self.scrapers.keys())
    
    async def scrape_all_sources(self) -> Dict[str, Any]:
        """Scrape all available sources"""
        results = {}
        
        for source_name, scraper in self.scrapers.items():
            try:
                logger.info(f"Starting scrape for source: {source_name}")
                items = await scraper.scrape()
                
                # Save items to database
                saved_count = await self._save_items_to_db(items, source_name)
                
                results[source_name] = {
                    "status": "success",
                    "items_scraped": len(items),
                    "items_saved": saved_count
                }
                
                logger.info(f"Completed scrape for {source_name}: {len(items)} items found, {saved_count} saved")
                
            except Exception as e:
                logger.error(f"Error scraping {source_name}: {str(e)}")
                results[source_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    async def scrape_sources(self, source_names: List[str]) -> Dict[str, Any]:
        """Scrape specific sources"""
        results = {}
        
        for source_name in source_names:
            if source_name not in self.scrapers:
                results[source_name] = {
                    "status": "error",
                    "error": f"Source '{source_name}' not available"
                }
                continue
            
            try:
                logger.info(f"Starting scrape for source: {source_name}")
                scraper = self.scrapers[source_name]
                items = await scraper.scrape()
                
                # Save items to database
                saved_count = await self._save_items_to_db(items, source_name)
                
                results[source_name] = {
                    "status": "success",
                    "items_scraped": len(items),
                    "items_saved": saved_count
                }
                
                logger.info(f"Completed scrape for {source_name}: {len(items)} items found, {saved_count} saved")
                
            except Exception as e:
                logger.error(f"Error scraping {source_name}: {str(e)}")
                results[source_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    async def _save_items_to_db(self, items: List[ThreatIntelItem], source_name: str) -> int:
        """Save scraped items to database"""
        db = SessionLocal()
        saved_count = 0
        
        try:
            for item in items:
                # Generate unique ID based on source URL
                item_id = hashlib.md5(str(item.source_url).encode()).hexdigest()
                
                # Check if item already exists
                existing = db.query(ThreatIntelDB).filter(
                    ThreatIntelDB.source_url == str(item.source_url)
                ).first()
                
                if existing:
                    # Update existing item if it's newer
                    if item.scraped_date > existing.scraped_date:
                        # Convert Pydantic model to dict and handle URL conversion
                        item_data = item.dict()
                        item_data['source_url'] = str(item.source_url)  # Convert URL to string
                        
                        for key, value in item_data.items():
                            if key != "id" and value is not None:
                                setattr(existing, key, value)
                        existing.scraped_date = datetime.utcnow()
                        saved_count += 1
                        logger.debug(f"Updated existing item: {item.title}")
                else:
                    # Create new item
                    db_item = ThreatIntelDB(
                        id=item_id,
                        title=item.title,
                        description=item.description,
                        protocol_name=item.protocol_name,
                        risk_level=item.risk_level.value,
                        source_url=str(item.source_url),
                        source_name=source_name,
                        published_date=item.published_date,
                        scraped_date=datetime.utcnow(),
                        tags=item.tags,
                        amount_lost=item.amount_lost,
                        attack_type=item.attack_type,
                        blockchain=item.blockchain,
                        severity_score=item.severity_score,
                        is_verified=item.is_verified,
                        additional_data=item.additional_data
                    )
                    db.add(db_item)
                    saved_count += 1
                    logger.debug(f"Created new item: {item.title}")
            
            db.commit()
            logger.info(f"Saved {saved_count} items to database for source: {source_name}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving items to database: {str(e)}")
            raise
        finally:
            db.close()
        
        return saved_count
