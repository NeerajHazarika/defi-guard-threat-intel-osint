from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from app.database.database import ThreatIntelDB
from app.models.threat_intel import ThreatIntelItem, RiskLevel
from app.utils.logger import logger

class ThreatAnalyzer:
    """Service for analyzing and retrieving threat intelligence data"""
    
    def __init__(self):
        self.risk_level_weights = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
    
    async def get_threat_intel(
        self,
        db: Session,
        protocol: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        source: Optional[str] = None,
        days_back: Optional[int] = None,
        min_amount: Optional[float] = None,
        blockchain: Optional[str] = None,
        attack_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        verified_only: bool = False
    ) -> List[ThreatIntelItem]:
        """
        Get threat intelligence data with various filters
        """
        try:
            query = db.query(ThreatIntelDB)
            
            # Apply filters
            if protocol:
                query = query.filter(
                    ThreatIntelDB.protocol_name.ilike(f"%{protocol}%")
                )
            
            if risk_level:
                query = query.filter(ThreatIntelDB.risk_level == risk_level.lower())
            
            if source:
                query = query.filter(
                    ThreatIntelDB.source_name.ilike(f"%{source}%")
                )
            
            if days_back:
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                query = query.filter(
                    or_(
                        ThreatIntelDB.published_date >= cutoff_date,
                        ThreatIntelDB.scraped_date >= cutoff_date
                    )
                )
            
            if min_amount:
                query = query.filter(ThreatIntelDB.amount_lost >= min_amount)
            
            if blockchain:
                query = query.filter(
                    ThreatIntelDB.blockchain.ilike(f"%{blockchain}%")
                )
            
            if attack_type:
                query = query.filter(
                    ThreatIntelDB.attack_type.ilike(f"%{attack_type}%")
                )
            
            if verified_only:
                query = query.filter(ThreatIntelDB.is_verified == True)
            
            if tags:
                # Filter by tags (JSON contains any of the specified tags)
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append(
                        ThreatIntelDB.tags.contains([tag])
                    )
                if tag_conditions:
                    query = query.filter(or_(*tag_conditions))
            
            # Order by severity score and recency
            query = query.order_by(
                desc(ThreatIntelDB.severity_score),
                desc(ThreatIntelDB.published_date),
                desc(ThreatIntelDB.scraped_date)
            )
            
            # Apply pagination
            results = query.offset(offset).limit(limit).all()
            
            # Convert to Pydantic models
            threat_items = []
            for result in results:
                threat_item = ThreatIntelItem(
                    id=result.id,
                    title=result.title,
                    description=result.description,
                    protocol_name=result.protocol_name,
                    risk_level=RiskLevel(result.risk_level),
                    source_url=result.source_url,
                    source_name=result.source_name,
                    published_date=result.published_date,
                    scraped_date=result.scraped_date,
                    tags=result.tags or [],
                    amount_lost=result.amount_lost,
                    attack_type=result.attack_type,
                    blockchain=result.blockchain,
                    severity_score=result.severity_score,
                    is_verified=result.is_verified,
                    additional_data=result.additional_data or {}
                )
                threat_items.append(threat_item)
            
            logger.info(f"Retrieved {len(threat_items)} threat intelligence items")
            return threat_items
            
        except Exception as e:
            logger.error(f"Error retrieving threat intelligence: {str(e)}")
            raise
    
    async def get_protocols_list(self, db: Session) -> List[Dict[str, Any]]:
        """Get list of all DeFi protocols with threat intelligence data"""
        try:
            results = db.query(
                ThreatIntelDB.protocol_name,
                func.count(ThreatIntelDB.id).label('incident_count'),
                func.sum(ThreatIntelDB.amount_lost).label('total_lost'),
                func.max(ThreatIntelDB.severity_score).label('max_severity'),
                func.max(ThreatIntelDB.published_date).label('latest_incident')
            ).filter(
                ThreatIntelDB.protocol_name.isnot(None)
            ).group_by(
                ThreatIntelDB.protocol_name
            ).order_by(
                desc('total_lost'),
                desc('incident_count')
            ).all()
            
            protocols = []
            for result in results:
                protocol_data = {
                    "name": result.protocol_name,
                    "incident_count": result.incident_count,
                    "total_amount_lost": result.total_lost or 0,
                    "max_severity_score": result.max_severity,
                    "latest_incident_date": result.latest_incident
                }
                protocols.append(protocol_data)
            
            logger.info(f"Retrieved {len(protocols)} protocols")
            return protocols
            
        except Exception as e:
            logger.error(f"Error retrieving protocols list: {str(e)}")
            raise
    
    async def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get general statistics about the threat intelligence data"""
        try:
            # Basic counts
            total_incidents = db.query(func.count(ThreatIntelDB.id)).scalar()
            
            verified_incidents = db.query(func.count(ThreatIntelDB.id)).filter(
                ThreatIntelDB.is_verified == True
            ).scalar()
            
            # Amount statistics
            total_amount_lost = db.query(func.sum(ThreatIntelDB.amount_lost)).scalar() or 0
            
            avg_amount_lost = db.query(func.avg(ThreatIntelDB.amount_lost)).filter(
                ThreatIntelDB.amount_lost.isnot(None)
            ).scalar() or 0
            
            # Risk level distribution
            risk_distribution = db.query(
                ThreatIntelDB.risk_level,
                func.count(ThreatIntelDB.id).label('count')
            ).group_by(ThreatIntelDB.risk_level).all()
            
            risk_dist_dict = {level: count for level, count in risk_distribution}
            
            # Source distribution
            source_distribution = db.query(
                ThreatIntelDB.source_name,
                func.count(ThreatIntelDB.id).label('count')
            ).group_by(ThreatIntelDB.source_name).all()
            
            source_dist_dict = {source: count for source, count in source_distribution}
            
            # Recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_incidents = db.query(func.count(ThreatIntelDB.id)).filter(
                or_(
                    ThreatIntelDB.published_date >= thirty_days_ago,
                    ThreatIntelDB.scraped_date >= thirty_days_ago
                )
            ).scalar()
            
            # Top attack types
            attack_types = db.query(
                ThreatIntelDB.attack_type,
                func.count(ThreatIntelDB.id).label('count')
            ).filter(
                ThreatIntelDB.attack_type.isnot(None)
            ).group_by(ThreatIntelDB.attack_type).order_by(desc('count')).limit(10).all()
            
            attack_types_dict = {attack_type: count for attack_type, count in attack_types}
            
            # Top blockchains
            blockchains = db.query(
                ThreatIntelDB.blockchain,
                func.count(ThreatIntelDB.id).label('count'),
                func.sum(ThreatIntelDB.amount_lost).label('total_lost')
            ).filter(
                ThreatIntelDB.blockchain.isnot(None)
            ).group_by(ThreatIntelDB.blockchain).order_by(desc('total_lost')).limit(10).all()
            
            blockchain_stats = []
            for blockchain, count, total_lost in blockchains:
                blockchain_stats.append({
                    "name": blockchain,
                    "incident_count": count,
                    "total_amount_lost": total_lost or 0
                })
            
            # Latest update
            latest_update = db.query(func.max(ThreatIntelDB.scraped_date)).scalar()
            
            statistics = {
                "total_incidents": total_incidents,
                "verified_incidents": verified_incidents,
                "verification_rate": (verified_incidents / total_incidents * 100) if total_incidents > 0 else 0,
                "total_amount_lost": total_amount_lost,
                "average_amount_lost": float(avg_amount_lost),
                "recent_incidents_30d": recent_incidents,
                "risk_level_distribution": risk_dist_dict,
                "source_distribution": source_dist_dict,
                "top_attack_types": attack_types_dict,
                "blockchain_statistics": blockchain_stats,
                "latest_update": latest_update,
                "data_freshness_hours": (datetime.utcnow() - latest_update).total_seconds() / 3600 if latest_update else None
            }
            
            logger.info("Retrieved threat intelligence statistics")
            return statistics
            
        except Exception as e:
            logger.error(f"Error retrieving statistics: {str(e)}")
            raise
    
    async def get_trending_threats(self, db: Session, days: int = 7, limit: int = 10) -> List[ThreatIntelItem]:
        """Get trending threats based on recent activity and severity"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = db.query(ThreatIntelDB).filter(
                or_(
                    ThreatIntelDB.published_date >= cutoff_date,
                    ThreatIntelDB.scraped_date >= cutoff_date
                )
            ).order_by(
                desc(ThreatIntelDB.severity_score),
                desc(ThreatIntelDB.amount_lost),
                desc(ThreatIntelDB.published_date)
            ).limit(limit)
            
            results = query.all()
            
            threat_items = []
            for result in results:
                threat_item = ThreatIntelItem(
                    id=result.id,
                    title=result.title,
                    description=result.description,
                    protocol_name=result.protocol_name,
                    risk_level=RiskLevel(result.risk_level),
                    source_url=result.source_url,
                    source_name=result.source_name,
                    published_date=result.published_date,
                    scraped_date=result.scraped_date,
                    tags=result.tags or [],
                    amount_lost=result.amount_lost,
                    attack_type=result.attack_type,
                    blockchain=result.blockchain,
                    severity_score=result.severity_score,
                    is_verified=result.is_verified,
                    additional_data=result.additional_data or {}
                )
                threat_items.append(threat_item)
            
            logger.info(f"Retrieved {len(threat_items)} trending threats")
            return threat_items
            
        except Exception as e:
            logger.error(f"Error retrieving trending threats: {str(e)}")
            raise
    
    async def search_threats(self, db: Session, query_text: str, limit: int = 20) -> List[ThreatIntelItem]:
        """Search threats by text query"""
        try:
            search_query = db.query(ThreatIntelDB).filter(
                or_(
                    ThreatIntelDB.title.ilike(f"%{query_text}%"),
                    ThreatIntelDB.description.ilike(f"%{query_text}%"),
                    ThreatIntelDB.protocol_name.ilike(f"%{query_text}%"),
                    ThreatIntelDB.attack_type.ilike(f"%{query_text}%"),
                    ThreatIntelDB.blockchain.ilike(f"%{query_text}%")
                )
            ).order_by(
                desc(ThreatIntelDB.severity_score),
                desc(ThreatIntelDB.published_date)
            ).limit(limit)
            
            results = search_query.all()
            
            threat_items = []
            for result in results:
                threat_item = ThreatIntelItem(
                    id=result.id,
                    title=result.title,
                    description=result.description,
                    protocol_name=result.protocol_name,
                    risk_level=RiskLevel(result.risk_level),
                    source_url=result.source_url,
                    source_name=result.source_name,
                    published_date=result.published_date,
                    scraped_date=result.scraped_date,
                    tags=result.tags or [],
                    amount_lost=result.amount_lost,
                    attack_type=result.attack_type,
                    blockchain=result.blockchain,
                    severity_score=result.severity_score,
                    is_verified=result.is_verified,
                    additional_data=result.additional_data or {}
                )
                threat_items.append(threat_item)
            
            logger.info(f"Search for '{query_text}' returned {len(threat_items)} results")
            return threat_items
            
        except Exception as e:
            logger.error(f"Error searching threats: {str(e)}")
            raise
