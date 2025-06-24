import os
import asyncio
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from app.utils.logger import logger

class ProtocolClassifier:
    """OpenAI-powered protocol classification service"""
    
    def __init__(self):
        self.client = None
        self.model = "gpt-3.5-turbo"
        self.max_retries = 3
        
        # List of known DeFi protocols for validation
        self.known_protocols = {
            'uniswap', 'compound', 'aave', 'makerdao', 'curve', 'yearn', 'synthetix',
            'balancer', 'sushiswap', 'pancakeswap', '1inch', 'kyber', 'bancor',
            'cream', 'alpha', 'harvest', 'pickle', 'badger', 'convex', 'frax',
            'olympus', 'wonderland', 'tomb', 'spell', 'rari', 'fuse', 'iron',
            'mirror', 'anchor', 'terra', 'polygon', 'arbitrum', 'optimism',
            'avalanche', 'fantom', 'bsc', 'harmony', 'chainlink', 'dydx',
            'gmx', 'benqi', 'trader joe', 'platypus', 'joe', 'vector',
            'euler', 'morpho', 'radiant', 'geist', 'hundred', 'fortress',
            'zunami', 'alexlab', 'force bridge', 'vesu', 'cork', 'marinade',
            'cetus', 'chainge', 'lndfi', 'brincfi', 'mobiusdao', 'celsius',
            'voyager', 'nomad', 'ronin', 'axie', 'poly network', 'thorchain',
            'multichain', 'anyswap', 'wormhole', 'beanstalk', 'rari capital',
            'qubit', 'nerve', 'cream finance', 'badgerdao', 'vesper', 'indexed',
            'alpha homora', 'value defi', 'dforce', 'belt finance', 'bunny',
            'autofarm', 'acryptos', 'viperswap', 'sphynx', 'dodo', 'mdex',
            'mooniswap', 'deversifi', 'loopring', 'immutable x', 'hermez',
            'polygon hermez', 'arbitrum one', 'optimism mainnet', 'metis',
            'moonbeam', 'moonriver', 'celo', 'fuse network', 'xdai', 'gnosis'
        }
    
    async def initialize(self):
        """Initialize the OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found. Protocol classification will use fallback method.")
            return
        
        self.client = AsyncOpenAI(api_key=api_key)
        logger.info("OpenAI client initialized for protocol classification")
    
    async def classify_protocol(self, title: str, description: str) -> Optional[str]:
        """Classify the DeFi protocol from article title and description"""
        if not self.client:
            logger.debug("OpenAI client not available, using fallback classification")
            return self._fallback_classification(title, description)
        
        try:
            # Prepare the prompt
            prompt = self._create_classification_prompt(title, description)
            
            # Make API call with retries
            for attempt in range(self.max_retries):
                try:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a DeFi protocol expert. Analyze the given text and identify the specific DeFi protocol mentioned. Return only the protocol name or 'NONE' if no specific protocol is identified."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        max_tokens=50,
                        temperature=0.1,
                        timeout=10.0
                    )
                    
                    protocol = response.choices[0].message.content.strip()
                    return self._validate_protocol(protocol)
                    
                except Exception as e:
                    logger.warning(f"OpenAI API attempt {attempt + 1} failed: {str(e)}")
                    if attempt == self.max_retries - 1:
                        logger.error("All OpenAI API attempts failed, using fallback")
                        return self._fallback_classification(title, description)
                    await asyncio.sleep(1)  # Wait before retry
                    
        except Exception as e:
            logger.error(f"Error in protocol classification: {str(e)}")
            return self._fallback_classification(title, description)
    
    def _create_classification_prompt(self, title: str, description: str) -> str:
        """Create a prompt for protocol classification"""
        text = f"Title: {title}\n\nDescription: {description[:800]}..."
        
        prompt = f"""
        Analyze this DeFi security incident article and identify the EXACT protocol name that was affected:

        {text}

        Instructions:
        - Return ONLY the exact name of the DeFi protocol that was hacked/exploited
        - Look for the protocol name in the title first, then the description
        - Common protocols: Uniswap, Aave, Compound, Curve, Yearn, SushiSwap, PancakeSwap, Balancer, etc.
        - Cross-chain bridges: Multichain, Wormhole, Ronin Bridge, Poly Network, Nomad, etc.
        - If the article mentions "Chainge", return "Chainge"
        - If the article mentions "Multichain", return "Multichain" 
        - Do NOT return blockchain names (Ethereum, BSC, Polygon) unless they are the protocol itself
        - Do NOT return generic terms like "DeFi", "bridge", "protocol"
        - If multiple protocols mentioned, return the PRIMARY one that was directly hacked
        - If no specific protocol is clearly identified, return "NONE"
        
        Examples:
        - "Uniswap V3 pools drained" → "Uniswap"
        - "Aave flash loan attack" → "Aave"
        - "Cross-chain bridge exploited" → "NONE" (unless specific bridge named)
        - "Chainge Finance users unable to withdraw" → "Chainge"

        Protocol name:
        """
        return prompt
    
    def _validate_protocol(self, protocol: str) -> Optional[str]:
        """Validate and clean the protocol name returned by OpenAI"""
        if not protocol or protocol.upper() == "NONE" or protocol.upper() == "NULL":
            return None
        
        # Clean the protocol name
        protocol_clean = protocol.strip().lower()
        protocol_clean = protocol_clean.replace("protocol", "").replace("finance", "").strip()
        protocol_clean = protocol_clean.replace("defi", "").replace("network", "").strip()
        
        # Direct match in known protocols
        if protocol_clean in self.known_protocols:
            return protocol_clean.title()
        
        # Check for partial matches with known protocols
        for known in self.known_protocols:
            # Exact substring match
            if protocol_clean == known or known == protocol_clean:
                return known.title()
            # Protocol name contains known protocol
            elif len(known) > 3 and known in protocol_clean and len(protocol_clean) <= len(known) + 5:
                return known.title()
            # Known protocol contains the classified name (for partial matches)
            elif len(protocol_clean) > 3 and protocol_clean in known and len(known) <= len(protocol_clean) + 5:
                return known.title()
        
        # Special cases for common misclassifications
        special_cases = {
            'uni': 'uniswap',
            'sushi': 'sushiswap', 
            'pancake': 'pancakeswap',
            'trader': 'trader joe',
            'joe': 'trader joe'
        }
        
        for short, full in special_cases.items():
            if short in protocol_clean and full in self.known_protocols:
                return full.title()
        
        # If it looks like a legitimate protocol name (has DeFi-related keywords), keep it
        defi_indicators = ['swap', 'dex', 'lending', 'dao', 'yield', 'farm', 'bridge', 'vault', 'pool']
        if any(indicator in protocol_clean for indicator in defi_indicators):
            return protocol.strip().title()
        
        # If it's a proper noun (capitalized) and not a common word, might be a protocol
        if protocol.istitle() and len(protocol) > 3 and protocol not in ['None', 'The', 'This', 'That']:
            return protocol.strip()
        
        # Otherwise, reject it
        logger.debug(f"Rejected protocol classification: {protocol}")
        return None
    
    def _fallback_classification(self, title: str, description: str) -> Optional[str]:
        """Fallback protocol classification using keyword matching"""
        text = f"{title} {description}".lower()
        
        # Look for exact protocol mentions (prioritize longer names first)
        for protocol in sorted(self.known_protocols, key=len, reverse=True):
            # Check for whole word matches to avoid false positives
            import re
            pattern = r'\b' + re.escape(protocol) + r'\b'
            if re.search(pattern, text):
                return protocol.title()
        
        # Check for protocol mentions in title (higher priority)
        title_lower = title.lower()
        for protocol in sorted(self.known_protocols, key=len, reverse=True):
            if protocol in title_lower:
                return protocol.title()
        
        return None
    
    async def is_threat_intel_relevant(self, title: str, description: str) -> Dict[str, Any]:
        """
        Determine if an article is relevant threat intelligence for a specific protocol
        Returns dict with 'is_relevant', 'protocol', and 'confidence'
        """
        protocol = await self.classify_protocol(title, description)
        
        if not protocol:
            return {
                'is_relevant': False,
                'protocol': None,
                'confidence': 0.0,
                'reason': 'No specific protocol identified'
            }
        
        # Check for threat intelligence keywords
        text = f"{title} {description}".lower()
        threat_keywords = [
            'hack', 'exploit', 'attack', 'breach', 'vulnerability', 'drained',
            'stolen', 'loss', 'rug pull', 'exit scam', 'flash loan', 'oracle',
            'smart contract', 'security', 'incident', 'compromised', 'malicious',
            'phishing', 'private key', 'admin key', 'backdoor', 'bug', 'rekt',
            'exploit', 'drain', 'manipulation', 'sandwich', 'mev', 'front-run',
            'back-run', 'slippage', 'liquidation', 'bad debt', 'insolvency',
            'pause', 'emergency', 'halt', 'freeze', 'blacklist', 'corrupted',
            'unable to withdraw', 'funds trapped', 'stuck', 'locked'
        ]
        
        # Count threat keywords
        threat_score = sum(1 for keyword in threat_keywords if keyword in text)
        
        # Boost confidence if protocol is clearly mentioned in title
        title_mentions_protocol = protocol.lower() in title.lower()
        protocol_boost = 0.2 if title_mentions_protocol else 0.0
        
        # Calculate confidence based on threat keywords and protocol clarity
        base_confidence = 0.3
        threat_confidence = min(threat_score * 0.1, 0.5)
        confidence = base_confidence + threat_confidence + protocol_boost
        
        # Must have at least some threat indicators to be relevant
        has_threat_indicators = threat_score > 0
        is_relevant = confidence >= 0.4 and protocol is not None and has_threat_indicators
        
        logger.info(f"Protocol: {protocol}, Threat score: {threat_score}, Confidence: {confidence:.2f}, Relevant: {is_relevant}")
        
        return {
            'is_relevant': is_relevant,
            'protocol': protocol,
            'confidence': confidence,
            'reason': f'Protocol: {protocol}, threat indicators: {threat_score}, confidence: {confidence:.2f}' if is_relevant else f'Low threat relevance (score: {threat_score}) or unclear protocol'
        }

# Global instance
protocol_classifier = ProtocolClassifier()
