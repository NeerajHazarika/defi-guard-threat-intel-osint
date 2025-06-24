import re
from typing import List, Optional
from datetime import datetime
from urllib.parse import urljoin
import json

from app.scrapers.base_scraper import BaseScraper
from app.models.threat_intel import ThreatIntelItem, RiskLevel
from app.utils.logger import logger

class ChainanalysisScraper(BaseScraper):
    """Scraper for Chainalysis reports and blog posts"""
    
    def __init__(self):
        super().__init__(
            name="Chainalysis",
            base_url="https://blog.chainalysis.com"
        )
        self.blog_endpoint = "/blog"
        self.max_pages = 3
    
    async def scrape(self) -> List[ThreatIntelItem]:
        """Scrape threat intelligence from Chainalysis blog"""
        items = []
        
        try:
            # Get the blog page to find article links
            blog_url = f"{self.base_url}"
            content = await self.fetch_page(blog_url)
            
            if not content:
                logger.error("Failed to fetch Chainalysis blog page")
                return items
            
            soup = self.parse_html(content)
            
            # Find relevant article links (focus on DeFi, security, hacks)
            article_links = self._extract_relevant_article_links(soup)
            
            logger.info(f"Found {len(article_links)} relevant articles on Chainalysis blog")
            
            # Scrape each article
            for link in article_links[:15]:  # Limit to 15 most recent relevant articles
                try:
                    article_url = urljoin(self.base_url, link)
                    article_item = await self._scrape_article(article_url)
                    
                    if article_item:
                        items.append(article_item)
                        logger.debug(f"Scraped article: {article_item.title}")
                    
                except Exception as e:
                    logger.error(f"Error scraping article {link}: {str(e)}")
                    continue
            
            logger.info(f"Successfully scraped {len(items)} items from Chainalysis")
            
        except Exception as e:
            logger.error(f"Error scraping Chainalysis: {str(e)}")
        
        return items
    
    def _extract_relevant_article_links(self, soup) -> List[str]:
        """Extract links to DeFi/security relevant articles"""
        links = []
        
        # Keywords that indicate relevant content
        relevant_keywords = [
            'defi', 'hack', 'exploit', 'vulnerability', 'attack', 'security',
            'breach', 'theft', 'scam', 'fraud', 'laundering', 'crime',
            'protocol', 'smart contract', 'dex', 'yield', 'flash loan'
        ]
        
        # Look for article links
        article_selectors = [
            'a[href*="/blog/"]',
            '.post-title a',
            '.article-title a',
            'h2 a',
            'h3 a',
            '.blog-post a'
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if not href:
                    continue
                
                # Get article title/text for relevance check
                title_text = element.get_text(strip=True).lower()
                
                # Check if article is relevant to DeFi/security
                if any(keyword in title_text for keyword in relevant_keywords):
                    if href not in links:
                        links.append(href)
        
        return links
    
    async def _scrape_article(self, url: str) -> Optional[ThreatIntelItem]:
        """Scrape a single article from Chainalysis blog"""
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
            
            # Filter out non-DeFi content
            if not self._is_defi_relevant(title, description):
                logger.debug(f"Article not DeFi relevant: {title}")
                return None
            
            # Assess risk level (Chainalysis articles are typically analytical)
            risk_level = self.assess_risk_level(
                amount_lost=amount_lost,
                title=title,
                description=description
            )
            
            # Extract tags
            tags = self.extract_tags(title, description)
            tags.extend(['analysis', 'research'])  # Chainalysis specific tags
            
            # Additional data specific to Chainalysis
            additional_data = {
                "analysis_type": self._extract_analysis_type(description),
                "data_source": "chainalysis",
                "report_type": self._extract_report_type(title, description),
                "geographical_focus": self._extract_geographical_focus(description)
            }
            
            return ThreatIntelItem(
                title=title,
                description=description,
                protocol_name=protocol_name,
                risk_level=risk_level,
                source_url=url,
                source_name="Chainalysis",
                published_date=published_date,
                tags=tags,
                amount_lost=amount_lost,
                attack_type=self._extract_attack_type(description),
                blockchain=self._extract_blockchain(description),
                severity_score=self._calculate_severity_score(amount_lost, risk_level),
                is_verified=True,  # Chainalysis is a reputable source
                additional_data=additional_data
            )
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {str(e)}")
            return None
    
    def _is_defi_relevant(self, title: str, description: str) -> bool:
        """Check if article is relevant to DeFi"""
        text = f"{title} {description}".lower()
        
        defi_keywords = [
            'defi', 'decentralized finance', 'dex', 'yield farming', 'liquidity',
            'smart contract', 'protocol', 'flash loan', 'governance token',
            'amm', 'automated market maker', 'lending protocol', 'borrowing',
            'staking', 'validator', 'consensus', 'bridge', 'cross-chain'
        ]
        
        # Must contain at least one DeFi keyword
        if not any(keyword in text for keyword in defi_keywords):
            return False
        
        # Exclude general crypto news
        excluded_keywords = [
            'bitcoin only', 'btc only', 'traditional finance', 'fiat',
            'regulation only', 'policy only', 'legal only'
        ]
        
        return not any(keyword in text for keyword in excluded_keywords)
    
    def _extract_title(self, soup) -> Optional[str]:
        """Extract article title"""
        title_selectors = [
            'h1.entry-title',
            'h1.post-title',
            'h1',
            '.blog-post-title',
            '.article-title',
            'title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 10:
                    return title
        
        return None
    
    def _extract_description(self, soup) -> Optional[str]:
        """Extract article description/content"""
        content_selectors = [
            '.entry-content',
            '.post-content',
            '.blog-post-content',
            '.article-content',
            'main .content',
            '.post-body'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Remove unwanted elements
                for unwanted in element(["script", "style", "nav", "aside", ".share-buttons"]):
                    unwanted.decompose()
                
                text = element.get_text(strip=True)
                if text and len(text) > 200:
                    return text[:1500]  # Limit to first 1500 characters
        
        return None
    
    def _extract_published_date(self, soup) -> Optional[datetime]:
        """Extract published date from article"""
        date_selectors = [
            'time[datetime]',
            '.published-date',
            '.post-date',
            '.entry-date',
            '[class*="date"]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                # Try datetime attribute
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
                            '%d %b %Y',
                            '%m/%d/%Y'
                        ]
                        
                        for fmt in formats:
                            try:
                                return datetime.strptime(date_text, fmt)
                            except:
                                continue
                    except:
                        pass
        
        return None
    
    def _extract_analysis_type(self, text: str) -> Optional[str]:
        """Extract type of analysis from text"""
        analysis_patterns = {
            'trend_analysis': ['trend', 'patterns', 'analysis over time'],
            'incident_analysis': ['incident', 'hack analysis', 'post-mortem'],
            'market_analysis': ['market', 'trading', 'volume'],
            'technical_analysis': ['technical', 'blockchain analysis', 'on-chain'],
            'regulatory_analysis': ['regulation', 'compliance', 'legal'],
            'threat_intelligence': ['threat', 'security', 'risk assessment']
        }
        
        text_lower = text.lower()
        for analysis_type, keywords in analysis_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return analysis_type
        
        return 'general_analysis'
    
    def _extract_report_type(self, title: str, description: str) -> Optional[str]:
        """Extract report type from title and description"""
        text = f"{title} {description}".lower()
        
        if 'report' in text:
            if any(keyword in text for keyword in ['annual', 'yearly', 'year']):
                return 'annual_report'
            elif any(keyword in text for keyword in ['monthly', 'month']):
                return 'monthly_report'
            elif any(keyword in text for keyword in ['quarterly', 'quarter']):
                return 'quarterly_report'
            else:
                return 'research_report'
        elif 'analysis' in text:
            return 'analysis'
        elif any(keyword in text for keyword in ['insight', 'findings']):
            return 'insights'
        else:
            return 'blog_post'
    
    def _extract_geographical_focus(self, text: str) -> Optional[str]:
        """Extract geographical focus from text"""
        geo_patterns = [
            'united states', 'usa', 'us', 'america', 'north america',
            'europe', 'european', 'eu', 'asia', 'china', 'japan',
            'south korea', 'india', 'russia', 'africa', 'global',
            'worldwide', 'international'
        ]
        
        text_lower = text.lower()
        for geo in geo_patterns:
            if geo in text_lower:
                return geo.title()
        
        return None
    
    def _extract_attack_type(self, text: str) -> Optional[str]:
        """Extract attack type from text"""
        attack_patterns = {
            'phishing': ['phishing', 'social engineering'],
            'smart_contract_exploit': ['smart contract', 'code exploit', 'vulnerability'],
            'flash_loan_attack': ['flash loan', 'flashloan'],
            'governance_attack': ['governance', 'voting manipulation'],
            'bridge_exploit': ['bridge', 'cross-chain attack'],
            'rug_pull': ['rug pull', 'exit scam'],
            'oracle_manipulation': ['oracle', 'price manipulation'],
            'exchange_hack': ['exchange hack', 'centralized exchange']
        }
        
        text_lower = text.lower()
        for attack_type, keywords in attack_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return attack_type
        
        return None
    
    def _extract_blockchain(self, text: str) -> Optional[str]:
        """Extract blockchain network from text"""
        blockchain_patterns = [
            'ethereum', 'bitcoin', 'polygon', 'binance smart chain', 'bsc',
            'avalanche', 'fantom', 'arbitrum', 'optimism', 'solana',
            'cardano', 'polkadot', 'cosmos', 'terra', 'harmony',
            'near', 'algorand', 'tezos'
        ]
        
        text_lower = text.lower()
        for blockchain in blockchain_patterns:
            if blockchain in text_lower:
                return blockchain.title()
        
        return None
    
    def _calculate_severity_score(self, amount_lost: Optional[float], risk_level: RiskLevel) -> float:
        """Calculate severity score (Chainalysis articles are typically analytical)"""
        base_score = {
            RiskLevel.LOW: 3.0,
            RiskLevel.MEDIUM: 5.0,
            RiskLevel.HIGH: 7.0,
            RiskLevel.CRITICAL: 8.5
        }.get(risk_level, 2.0)
        
        # Adjust based on amount lost
        if amount_lost:
            if amount_lost >= 50_000_000:  # $50M+
                base_score = min(10.0, base_score + 1.0)
            elif amount_lost >= 5_000_000:  # $5M+
                base_score = min(10.0, base_score + 0.5)
        
        return base_score
