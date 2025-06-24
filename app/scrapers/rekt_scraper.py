import re
from typing import List, Optional
from datetime import datetime
from urllib.parse import urljoin
import json

from app.scrapers.base_scraper import BaseScraper
from app.models.threat_intel import ThreatIntelItem, RiskLevel
from app.utils.logger import logger

class RektScraper(BaseScraper):
    """Scraper for Rekt News - DeFi security incidents"""
    
    def __init__(self):
        super().__init__(
            name="Rekt News",
            base_url="https://rekt.news"
        )
        self.articles_endpoint = "/posts"
        self.max_pages = 5
    
    async def scrape(self) -> List[ThreatIntelItem]:
        """Scrape threat intelligence from Rekt News"""
        items = []
        
        try:
            # Get the main page to find article links
            main_page_url = f"{self.base_url}"
            content = await self.fetch_page(main_page_url)
            
            if not content:
                logger.error("Failed to fetch Rekt News main page")
                return items
            
            soup = self.parse_html(content)
            
            # Find article links
            article_links = self._extract_article_links(soup)
            
            logger.info(f"Found {len(article_links)} articles on Rekt News")
            
            # Scrape each article
            for link in article_links[:20]:  # Limit to 20 most recent articles
                try:
                    article_url = urljoin(self.base_url, link)
                    article_item = await self._scrape_article(article_url)
                    
                    if article_item:
                        items.append(article_item)
                        logger.debug(f"Scraped article: {article_item.title}")
                    
                except Exception as e:
                    logger.error(f"Error scraping article {link}: {str(e)}")
                    continue
            
            logger.info(f"Successfully scraped {len(items)} items from Rekt News")
            
        except Exception as e:
            logger.error(f"Error scraping Rekt News: {str(e)}")
        
        return items
    
    def _extract_article_links(self, soup) -> List[str]:
        """Extract article links from the main page"""
        links = []
        
        # Look for article links (adjust selectors based on actual site structure)
        article_selectors = [
            'a[href*="/posts/"]',
            'a[href*="/articles/"]',
            '.post-title a',
            '.article-title a',
            'h2 a',
            'h3 a'
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and href not in links:
                    # Ensure it's not a navigation or other non-article link
                    if any(keyword in href.lower() for keyword in ['post', 'article', '/20']):
                        links.append(href)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        return unique_links
    
    async def _scrape_article(self, url: str) -> Optional[ThreatIntelItem]:
        """Scrape a single article from Rekt News"""
        try:
            content = await self.fetch_page(url)
            if not content:
                return None
            
            soup = self.parse_html(content)
            
            # Extract article data
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            published_date = self._extract_published_date(soup)
            protocol_name = self.extract_protocol_name(f"{title} {description}")
            amount_lost = self.extract_amount_lost(f"{title} {description}")
            
            if not title or not description:
                logger.warning(f"Missing title or description for {url}")
                return None
            
            # Assess risk level
            risk_level = self.assess_risk_level(
                amount_lost=amount_lost,
                title=title,
                description=description
            )
            
            # Extract tags
            tags = self.extract_tags(title, description)
            
            # Additional data specific to Rekt
            additional_data = {
                "attack_vector": self._extract_attack_vector(description),
                "blockchain_network": self._extract_blockchain(description),
                "post_mortem": self._has_post_mortem(description)
            }
            
            return ThreatIntelItem(
                title=title,
                description=description,
                protocol_name=protocol_name,
                risk_level=risk_level,
                source_url=url,
                source_name="Rekt News",
                published_date=published_date,
                tags=tags,
                amount_lost=amount_lost,
                attack_type=additional_data.get("attack_vector"),
                blockchain=additional_data.get("blockchain_network"),
                severity_score=self._calculate_severity_score(amount_lost, risk_level),
                is_verified=True,  # Rekt News generally publishes verified incidents
                additional_data=additional_data
            )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {str(e)}")
            return None
    
    def _extract_title(self, soup) -> Optional[str]:
        """Extract article title"""
        title_selectors = [
            'h1',
            '.post-title',
            '.article-title',
            'title',
            '[class*="title"]'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 10:  # Reasonable title length
                    return title
        
        return None
    
    def _extract_description(self, soup) -> Optional[str]:
        """Extract article description/content"""
        content_selectors = [
            '.post-content',
            '.article-content',
            '.content',
            'main',
            '[class*="content"]'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Remove script and style elements
                for script in element(["script", "style"]):
                    script.decompose()
                
                text = element.get_text(strip=True)
                if text and len(text) > 100:  # Reasonable content length
                    return text[:1000]  # Limit to first 1000 characters
        
        # Fallback to body text
        body = soup.find('body')
        if body:
            text = body.get_text(strip=True)
            return text[:1000] if text else None
        
        return None
    
    def _extract_published_date(self, soup) -> Optional[datetime]:
        """Extract published date from article"""
        date_selectors = [
            'time[datetime]',
            '.published-date',
            '.post-date',
            '[class*="date"]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                # Try datetime attribute first
                datetime_attr = element.get('datetime')
                if datetime_attr:
                    try:
                        return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    except:
                        pass
                
                # Try text content
                date_text = element.get_text(strip=True)
                if date_text:
                    try:
                        # Common date formats
                        formats = [
                            '%Y-%m-%d',
                            '%B %d, %Y',
                            '%b %d, %Y',
                            '%d %B %Y',
                            '%d %b %Y'
                        ]
                        
                        for fmt in formats:
                            try:
                                return datetime.strptime(date_text, fmt)
                            except:
                                continue
                    except:
                        pass
        
        return None
    
    def _extract_attack_vector(self, text: str) -> Optional[str]:
        """Extract attack vector from text"""
        attack_patterns = {
            'flash_loan': ['flash loan', 'flashloan'],
            'reentrancy': ['reentrancy', 're-entrancy'],
            'oracle_manipulation': ['oracle', 'price manipulation'],
            'governance_attack': ['governance', 'voting'],
            'smart_contract_bug': ['bug', 'vulnerability', 'exploit'],
            'rug_pull': ['rug pull', 'exit scam'],
            'bridge_exploit': ['bridge', 'cross-chain'],
            'front_running': ['front running', 'mev'],
        }
        
        text_lower = text.lower()
        for attack_type, keywords in attack_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return attack_type
        
        return None
    
    def _extract_blockchain(self, text: str) -> Optional[str]:
        """Extract blockchain network from text"""
        blockchain_patterns = [
            'ethereum', 'eth', 'polygon', 'matic', 'bsc', 'binance smart chain',
            'avalanche', 'avax', 'fantom', 'ftm', 'arbitrum', 'optimism',
            'solana', 'sol', 'terra', 'luna', 'harmony', 'one'
        ]
        
        text_lower = text.lower()
        for blockchain in blockchain_patterns:
            if blockchain in text_lower:
                return blockchain.title()
        
        return None
    
    def _has_post_mortem(self, text: str) -> bool:
        """Check if article contains post-mortem analysis"""
        post_mortem_keywords = [
            'post-mortem', 'postmortem', 'analysis', 'detailed breakdown',
            'technical analysis', 'how it happened'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in post_mortem_keywords)
    
    def _calculate_severity_score(self, amount_lost: Optional[float], risk_level: RiskLevel) -> float:
        """Calculate severity score based on amount lost and risk level"""
        base_score = {
            RiskLevel.LOW: 2.0,
            RiskLevel.MEDIUM: 5.0,
            RiskLevel.HIGH: 7.5,
            RiskLevel.CRITICAL: 9.0
        }.get(risk_level, 1.0)
        
        # Adjust based on amount lost
        if amount_lost:
            if amount_lost >= 100_000_000:  # $100M+
                base_score = min(10.0, base_score + 1.0)
            elif amount_lost >= 10_000_000:  # $10M+
                base_score = min(10.0, base_score + 0.5)
        
        return base_score
