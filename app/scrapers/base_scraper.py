import abc
import asyncio
import aiohttp
from typing import List, Optional, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
import re

from app.models.threat_intel import ThreatIntelItem, RiskLevel
from app.utils.logger import logger

class BaseScraper(abc.ABC):
    """Base class for all threat intelligence scrapers"""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 1.0  # Default 1 second between requests
    
    async def initialize(self, session: aiohttp.ClientSession):
        """Initialize the scraper with an aiohttp session"""
        self.session = session
        logger.info(f"Initialized {self.name} scraper")
    
    async def close(self):
        """Cleanup scraper resources"""
        logger.info(f"Closing {self.name} scraper")
    
    @abc.abstractmethod
    async def scrape(self) -> List[ThreatIntelItem]:
        """Scrape threat intelligence data from the source"""
        pass
    
    async def fetch_page(self, url: str, **kwargs) -> Optional[str]:
        """Fetch a web page and return its content"""
        if not self.session:
            raise RuntimeError("Scraper not initialized")
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            async with self.session.get(url, **kwargs) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.debug(f"Successfully fetched {url}")
                    return content
                else:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def parse_html(self, content: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup"""
        return BeautifulSoup(content, 'html.parser')
    
    def extract_protocol_name(self, text: str) -> Optional[str]:
        """Extract DeFi protocol name from text using common patterns"""
        # Common DeFi protocol patterns
        defi_protocols = [
            'uniswap', 'compound', 'aave', 'makerdao', 'curve', 'yearn', 'synthetix',
            'balancer', 'sushiswap', 'pancakeswap', '1inch', 'kyber', 'bancor',
            'cream', 'alpha', 'harvest', 'pickle', 'badger', 'convex', 'frax',
            'olympus', 'wonderland', 'tomb', 'spell', 'rari', 'fuse', 'iron',
            'mirror', 'anchor', 'terra', 'polygon', 'arbitrum', 'optimism',
            'avalanche', 'fantom', 'bsc', 'harmony'
        ]
        
        text_lower = text.lower()
        for protocol in defi_protocols:
            if protocol in text_lower:
                return protocol.title()
        
        # Try to extract from common patterns
        patterns = [
            r'(\w+)\s+(?:protocol|finance|swap|dao)',
            r'(?:protocol|finance|swap|dao)\s+(\w+)',
            r'(\w+)\s+(?:exploit|hack|attack)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                potential_protocol = match.group(1)
                if len(potential_protocol) > 2:  # Avoid very short matches
                    return potential_protocol.title()
        
        return None
    
    def assess_risk_level(self, amount_lost: Optional[float] = None, 
                         keywords: List[str] = None, 
                         title: str = "", 
                         description: str = "") -> RiskLevel:
        """Assess risk level based on various factors"""
        keywords = keywords or []
        text = f"{title} {description}".lower()
        
        # Critical indicators
        critical_keywords = ['critical', 'emergency', 'immediate', 'urgent', 'exploit']
        high_keywords = ['hack', 'attack', 'vulnerability', 'breach', 'stolen', 'drained']
        medium_keywords = ['warning', 'risk', 'issue', 'concern', 'potential']
        
        # Check amount lost
        if amount_lost:
            if amount_lost >= 10_000_000:  # $10M+
                return RiskLevel.CRITICAL
            elif amount_lost >= 1_000_000:  # $1M+
                return RiskLevel.HIGH
            elif amount_lost >= 100_000:  # $100K+
                return RiskLevel.MEDIUM
        
        # Check keywords
        if any(keyword in text for keyword in critical_keywords):
            return RiskLevel.CRITICAL
        elif any(keyword in text for keyword in high_keywords):
            return RiskLevel.HIGH
        elif any(keyword in text for keyword in medium_keywords):
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def extract_amount_lost(self, text: str) -> Optional[float]:
        """Extract monetary amount lost from text"""
        # Patterns for different currency formats
        patterns = [
            r'\$?([\d,]+(?:\.\d{2})?)\s*(?:million|m)',
            r'\$?([\d,]+(?:\.\d{2})?)\s*(?:billion|b)',
            r'\$?([\d,]+(?:\.\d{2})?)\s*(?:thousand|k)',
            r'\$?([\d,]+(?:\.\d{2})?)',
        ]
        
        text_lower = text.lower()
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    
                    # Apply multipliers
                    if 'billion' in match.group(0) or 'b' in match.group(0):
                        amount *= 1_000_000_000
                    elif 'million' in match.group(0) or 'm' in match.group(0):
                        amount *= 1_000_000
                    elif 'thousand' in match.group(0) or 'k' in match.group(0):
                        amount *= 1_000
                    
                    # Only return if it's a reasonable amount (> $1000)
                    if amount > 1000:
                        return amount
                        
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def extract_tags(self, title: str, description: str) -> List[str]:
        """Extract relevant tags from title and description"""
        text = f"{title} {description}".lower()
        
        tag_patterns = {
            'exploit': ['exploit', 'attack', 'hack'],
            'vulnerability': ['vulnerability', 'bug', 'flaw'],
            'defi': ['defi', 'decentralized finance'],
            'smart_contract': ['smart contract', 'contract'],
            'flash_loan': ['flash loan', 'flashloan'],
            'rug_pull': ['rug pull', 'rugpull', 'exit scam'],
            'governance': ['governance', 'voting', 'proposal'],
            'oracle': ['oracle', 'price feed'],
            'bridge': ['bridge', 'cross-chain'],
            'token': ['token', 'cryptocurrency', 'crypto'],
        }
        
        tags = []
        for tag, keywords in tag_patterns.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)
        
        return tags
