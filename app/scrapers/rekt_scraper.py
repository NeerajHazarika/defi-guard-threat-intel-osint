import re
from typing import List, Optional
from datetime import datetime, date
from urllib.parse import urljoin
import json

from app.scrapers.base_scraper import BaseScraper
from app.models.threat_intel import ThreatIntelItem, RiskLevel
from app.services.protocol_classifier import protocol_classifier
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
            
            logger.info(f"Rekt News page content length: {len(content)}")
            soup = self.parse_html(content)
            
            # Find article links
            article_links = self._extract_article_links(soup)
            
            logger.info(f"Found {len(article_links)} articles on Rekt News")
            
            # If no articles found, log some debug info
            if len(article_links) == 0:
                # Check for any h5 elements
                h5_elements = soup.find_all('h5')
                logger.info(f"Found {len(h5_elements)} h5 elements total")
                
                # Check for any post-title elements
                post_title_elements = soup.find_all(class_='post-title')
                logger.info(f"Found {len(post_title_elements)} post-title elements")
                
                # Check for any links with href starting with /
                all_links = soup.find_all('a', href=True)
                relevant_links = [link for link in all_links if link.get('href', '').startswith('/') and len(link.get('href', '')) > 1]
                logger.info(f"Found {len(relevant_links)} links starting with '/'")
                
                if relevant_links:
                    logger.info(f"Sample links: {[link.get('href') for link in relevant_links[:5]]}")
            
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
        
        # Look for article links based on actual Rekt News structure
        article_selectors = [
            'h5.post-title a',  # Primary selector - h5 with post-title class
            '.post-title a',    # General post-title selector
            'article.post .post-title a',  # More specific article context
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            logger.info(f"Selector '{selector}' found {len(elements)} elements")
            for element in elements:
                href = element.get('href')
                if href and href not in links:
                    # Filter out navigation links - Rekt articles start with /
                    if (href.startswith('/') and 
                        not href.startswith('/?') and  # Exclude tag filters
                        href != '/' and  # Exclude home page
                        'tag=' not in href and  # Exclude tag pages
                        'page=' not in href):  # Exclude pagination
                        links.append(href)
                        logger.info(f"Added article link: {href}")
        
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
            
            if not title or not description:
                logger.warning(f"Missing title or description for {url}")
                return None
            
            # Use AI to classify protocol and check if it's relevant threat intelligence
            threat_intel_result = await protocol_classifier.is_threat_intel_relevant(title, description)
            
            if not threat_intel_result['is_relevant']:
                logger.info(f"Article filtered out - {threat_intel_result['reason']}: {title[:50]}...")
                return None
            
            # Get the AI-classified protocol name
            protocol_name = threat_intel_result['protocol']
            logger.info(f"Classified protocol: {protocol_name} for article: {title[:50]}...")
            
            published_date = self._extract_published_date(soup)
            amount_lost = self.extract_amount_lost(f"{title} {description}")
            
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
                "post_mortem": self._has_post_mortem(description),
                "ai_classification_confidence": threat_intel_result['confidence']
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
    
    def _extract_published_date(self, soup) -> Optional[date]:
        """Extract published date from article"""
        import re
        from dateutil.parser import parse as date_parse
        
        # More comprehensive selectors for Rekt News
        date_selectors = [
            'time[datetime]',
            'time',
            '.published-date',
            '.post-date',
            '.entry-date',
            '.article-date',
            '.date',
            '[class*="date"]',
            '[class*="time"]',
            '.post-meta time',
            '.meta-date',
            '.byline time'
        ]
        
        for selector in date_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Try datetime attribute first
                datetime_attr = element.get('datetime')
                if datetime_attr:
                    try:
                        # Handle various ISO formats
                        clean_datetime = datetime_attr.replace('Z', '+00:00')
                        parsed_date = datetime.fromisoformat(clean_datetime)
                        return parsed_date.date()  # Return only date component
                    except Exception as e:
                        logger.debug(f"Failed to parse datetime attribute '{datetime_attr}': {e}")
                        # Try with dateutil parser as fallback
                        try:
                            parsed_date = date_parse(datetime_attr)
                            return parsed_date.date()  # Return only date component
                        except:
                            pass
                
                # Try text content
                date_text = element.get_text(strip=True)
                if date_text and len(date_text) > 4:  # Minimum reasonable date length
                    try:
                        # Clean the text
                        date_text = re.sub(r'(Posted|Published|on|at|by|•|·)', '', date_text, flags=re.IGNORECASE).strip()
                        date_text = re.sub(r'\s+', ' ', date_text)  # Remove extra whitespace
                        
                        # Try dateutil parser first (most flexible)
                        try:
                            parsed_date = date_parse(date_text)
                            return parsed_date.date()  # Return only date component
                        except:
                            pass
                        
                        # Common date formats
                        formats = [
                            '%Y-%m-%d',
                            '%Y-%m-%dT%H:%M:%S',
                            '%Y-%m-%d %H:%M:%S',
                            '%B %d, %Y',
                            '%b %d, %Y',
                            '%d %B %Y',
                            '%d %b %Y',
                            '%m/%d/%Y',
                            '%d/%m/%Y',
                            '%Y/%m/%d',
                            '%b %d %Y',
                            '%B %d %Y'
                        ]
                        
                        for fmt in formats:
                            try:
                                parsed_date = datetime.strptime(date_text, fmt)
                                return parsed_date.date()  # Return only date component
                            except:
                                continue
                    except Exception as e:
                        logger.debug(f"Failed to parse date text '{date_text}': {e}")
        
        # Look for dates in meta tags
        meta_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publishdate"]',
            'meta[name="date"]',
            'meta[property="og:updated_time"]'
        ]
        
        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get('content')
                if content:
                    try:
                        parsed_date = date_parse(content)
                        return parsed_date.date()  # Return only date component
                    except:
                        pass
        
        # Fallback: look for date patterns in the entire page
        page_text = soup.get_text()
        date_patterns = [
            r'\b(\d{4})-(\d{2})-(\d{2})\b',
            r'\b(\w+)\s+(\d{1,2}),?\s+(\d{4})\b',
            r'\b(\d{1,2})\s+(\w+)\s+(\d{4})\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, page_text)
            for match in matches:
                try:
                    if len(match) == 3:
                        date_str = ' '.join(match)
                        parsed_date = date_parse(date_str)
                        return parsed_date.date()  # Return only date component
                except:
                    continue
        
        logger.debug("No published date found")
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
