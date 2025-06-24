"""
Data validation and cleanup utilities for threat intelligence
"""

import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from urllib.parse import urlparse

from app.models.threat_intel import RiskLevel
from app.utils.logger import logger

class DataValidator:
    """Validates and cleans threat intelligence data"""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate if URL is properly formatted"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def clean_title(title: str) -> str:
        """Clean and normalize title text"""
        if not title:
            return ""
        
        # Remove extra whitespace
        title = ' '.join(title.split())
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ['BREAKING:', 'UPDATE:', 'ALERT:']
        for prefix in prefixes_to_remove:
            if title.upper().startswith(prefix):
                title = title[len(prefix):].strip()
        
        # Limit length
        if len(title) > 200:
            title = title[:197] + "..."
        
        return title
    
    @staticmethod
    def clean_description(description: str) -> str:
        """Clean and normalize description text"""
        if not description:
            return ""
        
        # Remove extra whitespace and newlines
        description = ' '.join(description.split())
        
        # Remove HTML tags if any
        description = re.sub(r'<[^>]+>', '', description)
        
        # Remove URLs from description to avoid duplication
        description = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', description)
        
        # Limit length
        if len(description) > 2000:
            description = description[:1997] + "..."
        
        return description.strip()
    
    @staticmethod
    def normalize_protocol_name(protocol_name: Optional[str]) -> Optional[str]:
        """Normalize protocol name for consistency"""
        if not protocol_name:
            return None
        
        # Common protocol name mappings
        protocol_mappings = {
            'uni': 'Uniswap',
            'uniswap v2': 'Uniswap',
            'uniswap v3': 'Uniswap',
            'sushi': 'SushiSwap',
            'pancake': 'PancakeSwap',
            'compound': 'Compound',
            'aave': 'Aave',
            'maker': 'MakerDAO',
            'makerdao': 'MakerDAO',
            'yearn': 'Yearn Finance',
            'curve': 'Curve Finance',
            'balancer': 'Balancer',
            '1inch': '1inch',
            'kyber': 'Kyber Network',
            'bancor': 'Bancor',
            'cream': 'Cream Finance',
            'alpha': 'Alpha Finance',
            'harvest': 'Harvest Finance',
            'pickle': 'Pickle Finance',
            'badger': 'Badger DAO',
            'convex': 'Convex Finance',
            'frax': 'Frax Finance',
            'olympus': 'Olympus DAO',
            'wonderland': 'Wonderland',
            'tomb': 'Tomb Finance',
            'spell': 'Spell Token',
            'rari': 'Rari Capital',
            'fuse': 'Fuse',
            'iron': 'Iron Finance',
            'mirror': 'Mirror Protocol',
            'anchor': 'Anchor Protocol',
            'terra': 'Terra',
            'polygon': 'Polygon',
            'arbitrum': 'Arbitrum',
            'optimism': 'Optimism'
        }
        
        protocol_lower = protocol_name.lower().strip()
        
        # Check for exact mappings
        if protocol_lower in protocol_mappings:
            return protocol_mappings[protocol_lower]
        
        # Capitalize first letter of each word
        return ' '.join(word.capitalize() for word in protocol_lower.split())
    
    @staticmethod
    def validate_amount(amount: Optional[float]) -> Optional[float]:
        """Validate and clean amount lost"""
        if amount is None:
            return None
        
        # Must be positive
        if amount <= 0:
            return None
        
        # Must be reasonable (less than $1 trillion)
        if amount > 1_000_000_000_000:
            return None
        
        # Round to 2 decimal places
        return round(amount, 2)
    
    @staticmethod
    def validate_risk_level(risk_level: str) -> RiskLevel:
        """Validate and normalize risk level"""
        if not risk_level:
            return RiskLevel.LOW
        
        risk_lower = risk_level.lower().strip()
        
        risk_mappings = {
            'low': RiskLevel.LOW,
            'medium': RiskLevel.MEDIUM,
            'med': RiskLevel.MEDIUM,
            'moderate': RiskLevel.MEDIUM,
            'high': RiskLevel.HIGH,
            'critical': RiskLevel.CRITICAL,
            'severe': RiskLevel.CRITICAL,
            'urgent': RiskLevel.CRITICAL
        }
        
        return risk_mappings.get(risk_lower, RiskLevel.LOW)
    
    @staticmethod
    def clean_tags(tags: List[str]) -> List[str]:
        """Clean and normalize tags"""
        if not tags:
            return []
        
        cleaned_tags = []
        for tag in tags:
            if isinstance(tag, str) and tag.strip():
                # Normalize tag
                clean_tag = tag.lower().strip().replace(' ', '_')
                
                # Remove special characters except underscore
                clean_tag = re.sub(r'[^a-z0-9_]', '', clean_tag)
                
                if clean_tag and len(clean_tag) > 1:
                    cleaned_tags.append(clean_tag)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(cleaned_tags))
    
    @staticmethod
    def normalize_blockchain(blockchain: Optional[str]) -> Optional[str]:
        """Normalize blockchain name"""
        if not blockchain:
            return None
        
        blockchain_mappings = {
            'eth': 'Ethereum',
            'ethereum': 'Ethereum',
            'btc': 'Bitcoin',
            'bitcoin': 'Bitcoin',
            'bnb': 'Binance Smart Chain',
            'bsc': 'Binance Smart Chain',
            'binance smart chain': 'Binance Smart Chain',
            'polygon': 'Polygon',
            'matic': 'Polygon',
            'avax': 'Avalanche',
            'avalanche': 'Avalanche',
            'ftm': 'Fantom',
            'fantom': 'Fantom',
            'arbitrum': 'Arbitrum',
            'optimism': 'Optimism',
            'sol': 'Solana',
            'solana': 'Solana',
            'ada': 'Cardano',
            'cardano': 'Cardano',
            'dot': 'Polkadot',
            'polkadot': 'Polkadot',
            'atom': 'Cosmos',
            'cosmos': 'Cosmos',
            'luna': 'Terra',
            'terra': 'Terra',
            'near': 'Near',
            'algo': 'Algorand',
            'algorand': 'Algorand',
            'xtz': 'Tezos',
            'tezos': 'Tezos',
            'harmony': 'Harmony',
            'one': 'Harmony'
        }
        
        blockchain_lower = blockchain.lower().strip()
        return blockchain_mappings.get(blockchain_lower, blockchain.title())
    
    @staticmethod
    def extract_severity_keywords(text: str) -> List[str]:
        """Extract severity-related keywords from text"""
        text_lower = text.lower()
        
        severity_keywords = {
            'critical': ['critical', 'emergency', 'immediate', 'urgent'],
            'high': ['major', 'significant', 'substantial', 'severe'],
            'exploit': ['exploit', 'attack', 'hack', 'breach'],
            'financial': ['million', 'billion', 'lost', 'stolen', 'drained'],
            'technical': ['vulnerability', 'bug', 'flaw', 'code']
        }
        
        found_keywords = []
        for category, keywords in severity_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords.append(category)
                    break
        
        return found_keywords
    
    @staticmethod
    def calculate_confidence_score(title: str, description: str, source_name: str) -> float:
        """Calculate confidence score for the threat intelligence item"""
        score = 0.0
        
        # Base score by source reliability
        source_scores = {
            'Rekt News': 9.0,
            'Chainalysis': 9.5,
            'CoinDesk': 8.0,
            'The Block': 8.0,
            'Unknown': 5.0
        }
        score += source_scores.get(source_name, 5.0)
        
        # Add points for detailed content
        if len(description) > 500:
            score += 0.5
        if len(description) > 1000:
            score += 0.5
        
        # Add points for specific details
        if any(keyword in description.lower() for keyword in ['$', 'million', 'billion']):
            score += 0.5
        
        if any(keyword in description.lower() for keyword in ['exploit', 'vulnerability', 'attack']):
            score += 0.5
        
        # Normalize to 0-10 scale
        return min(10.0, score)

class DataCleaner:
    """Cleans and standardizes threat intelligence data"""
    
    def __init__(self):
        self.validator = DataValidator()
    
    def clean_threat_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a complete threat intelligence item"""
        try:
            cleaned = {}
            
            # Clean required fields
            cleaned['title'] = self.validator.clean_title(item_data.get('title', ''))
            cleaned['description'] = self.validator.clean_description(item_data.get('description', ''))
            cleaned['source_url'] = item_data.get('source_url', '')
            cleaned['source_name'] = item_data.get('source_name', 'Unknown')
            
            # Validate URL
            if not self.validator.validate_url(cleaned['source_url']):
                logger.warning(f"Invalid URL: {cleaned['source_url']}")
                return None
            
            # Clean optional fields
            cleaned['protocol_name'] = self.validator.normalize_protocol_name(
                item_data.get('protocol_name')
            )
            
            cleaned['risk_level'] = self.validator.validate_risk_level(
                item_data.get('risk_level', 'low')
            )
            
            cleaned['amount_lost'] = self.validator.validate_amount(
                item_data.get('amount_lost')
            )
            
            cleaned['blockchain'] = self.validator.normalize_blockchain(
                item_data.get('blockchain')
            )
            
            cleaned['tags'] = self.validator.clean_tags(
                item_data.get('tags', [])
            )
            
            # Add computed fields
            cleaned['confidence_score'] = self.validator.calculate_confidence_score(
                cleaned['title'],
                cleaned['description'],
                cleaned['source_name']
            )
            
            cleaned['severity_keywords'] = self.validator.extract_severity_keywords(
                f"{cleaned['title']} {cleaned['description']}"
            )
            
            # Preserve other fields
            for field in ['published_date', 'attack_type', 'severity_score', 'is_verified', 'additional_data']:
                if field in item_data:
                    cleaned[field] = item_data[field]
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning threat item: {str(e)}")
            return None
