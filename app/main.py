from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
from dotenv import load_dotenv

from app.models.threat_intel import ThreatIntelResponse, ThreatIntelItem
from app.scrapers.manager import ScraperManager
from app.database.database import get_db, SessionLocal
from app.services.threat_analyzer import ThreatAnalyzer
from app.services.scheduler import start_background_tasks, stop_background_tasks
from app.utils.logger import logger

load_dotenv()

app = FastAPI(
    title=os.getenv("API_TITLE", "DeFi Guard OSINT API"),
    version=os.getenv("API_VERSION", "1.0.0"),
    description=os.getenv("API_DESCRIPTION", "Threat Intelligence API for DeFi Protocols")
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
scraper_manager = ScraperManager()
threat_analyzer = ThreatAnalyzer()

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("Starting DeFi Guard OSINT API")
    await scraper_manager.initialize()
    await start_background_tasks()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down DeFi Guard OSINT API")
    await stop_background_tasks()
    await scraper_manager.close()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "DeFi Guard OSINT API is running", "status": "healthy"}

@app.get("/api/v1/threat-intel", response_model=ThreatIntelResponse)
async def get_threat_intel(
    protocol: Optional[str] = Query(None, description="Filter by DeFi protocol name"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (low, medium, high)"),
    limit: int = Query(50, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    source: Optional[str] = Query(None, description="Filter by source (rekt, chainalysis, etc.)"),
    fresh_scrape: bool = Query(False, description="Force fresh scraping of data"),
    db: SessionLocal = Depends(get_db)
):
    """
    Get threat intelligence data for DeFi protocols
    """
    try:
        if fresh_scrape:
            logger.info("Performing fresh scrape of threat intelligence data")
            await scraper_manager.scrape_all_sources()
        
        # Get data from database with filters
        threat_data = await threat_analyzer.get_threat_intel(
            db=db,
            protocol=protocol,
            risk_level=risk_level,
            limit=limit,
            offset=offset,
            source=source
        )
        
        return ThreatIntelResponse(
            status="success",
            count=len(threat_data),
            data=threat_data
        )
        
    except Exception as e:
        logger.error(f"Error getting threat intel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/v1/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    sources: Optional[List[str]] = Query(None, description="Specific sources to scrape")
):
    """
    Trigger manual scraping of threat intelligence sources
    """
    try:
        if sources:
            background_tasks.add_task(scraper_manager.scrape_sources, sources)
        else:
            background_tasks.add_task(scraper_manager.scrape_all_sources)
        
        return {"message": "Scraping initiated", "status": "started"}
        
    except Exception as e:
        logger.error(f"Error triggering scrape: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger scrape: {str(e)}")

@app.get("/api/v1/sources")
async def get_available_sources():
    """
    Get list of available threat intelligence sources
    """
    try:
        sources = scraper_manager.get_available_sources()
        return {
            "status": "success",
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Error getting sources: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sources: {str(e)}")

@app.get("/api/v1/protocols")
async def get_protocols(db: SessionLocal = Depends(get_db)):
    """
    Get list of DeFi protocols with threat intelligence data
    """
    try:
        protocols = await threat_analyzer.get_protocols_list(db)
        return {
            "status": "success",
            "protocols": protocols
        }
    except Exception as e:
        logger.error(f"Error getting protocols: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get protocols: {str(e)}")

@app.get("/api/v1/stats")
async def get_stats(db: SessionLocal = Depends(get_db)):
    """
    Get statistics about threat intelligence data
    """
    try:
        stats = await threat_analyzer.get_statistics(db)
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.get("/api/v1/search")
async def search_threats(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    db: SessionLocal = Depends(get_db)
):
    """
    Search threat intelligence data by text query
    """
    try:
        results = await threat_analyzer.search_threats(db, q, limit)
        return {
            "status": "success",
            "query": q,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Error searching threats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/v1/trending")
async def get_trending_threats(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    db: SessionLocal = Depends(get_db)
):
    """
    Get trending threats based on recent activity and severity
    """
    try:
        results = await threat_analyzer.get_trending_threats(db, days, limit)
        return {
            "status": "success",
            "timeframe_days": days,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Error getting trending threats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get trending threats: {str(e)}")

@app.get("/api/v1/protocols/{protocol_name}")
async def get_protocol_details(
    protocol_name: str,
    limit: int = Query(20, ge=1, le=100, description="Number of incidents to return"),
    db: SessionLocal = Depends(get_db)
):
    """
    Get detailed threat intelligence for a specific protocol
    """
    try:
        # Get incidents for this protocol
        incidents = await threat_analyzer.get_threat_intel(
            db=db,
            protocol=protocol_name,
            limit=limit
        )
        
        # Get protocol statistics
        protocol_stats = await threat_analyzer.get_protocols_list(db)
        protocol_info = next((p for p in protocol_stats if p["name"].lower() == protocol_name.lower()), None)
        
        return {
            "status": "success",
            "protocol": protocol_name,
            "summary": protocol_info,
            "recent_incidents": {
                "count": len(incidents),
                "data": incidents
            }
        }
    except Exception as e:
        logger.error(f"Error getting protocol details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get protocol details: {str(e)}")

@app.get("/api/v1/risk-levels/{risk_level}")
async def get_threats_by_risk_level(
    risk_level: str,
    limit: int = Query(50, ge=1, le=200, description="Number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: SessionLocal = Depends(get_db)
):
    """
    Get threats filtered by specific risk level
    """
    try:
        valid_levels = ["low", "medium", "high", "critical"]
        if risk_level.lower() not in valid_levels:
            raise HTTPException(status_code=400, detail=f"Invalid risk level. Must be one of: {', '.join(valid_levels)}")
        
        results = await threat_analyzer.get_threat_intel(
            db=db,
            risk_level=risk_level.lower(),
            limit=limit,
            offset=offset
        )
        
        return {
            "status": "success",
            "risk_level": risk_level.lower(),
            "count": len(results),
            "data": results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting threats by risk level: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get threats: {str(e)}")

@app.get("/api/v1/attack-types")
async def get_attack_types(db: SessionLocal = Depends(get_db)):
    """
    Get list of all attack types with statistics
    """
    try:
        # This would require adding a method to threat_analyzer
        # For now, return a simple implementation
        from sqlalchemy import func
        from app.database.database import ThreatIntelDB
        
        results = db.query(
            ThreatIntelDB.attack_type,
            func.count(ThreatIntelDB.id).label('count'),
            func.sum(ThreatIntelDB.amount_lost).label('total_lost'),
            func.avg(ThreatIntelDB.severity_score).label('avg_severity')
        ).filter(
            ThreatIntelDB.attack_type.isnot(None)
        ).group_by(
            ThreatIntelDB.attack_type
        ).order_by(func.count(ThreatIntelDB.id).desc()).all()
        
        attack_types = []
        for result in results:
            attack_types.append({
                "attack_type": result.attack_type,
                "incident_count": result.count,
                "total_amount_lost": result.total_lost or 0,
                "average_severity": float(result.avg_severity or 0)
            })
        
        return {
            "status": "success",
            "attack_types": attack_types
        }
    except Exception as e:
        logger.error(f"Error getting attack types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get attack types: {str(e)}")

@app.get("/api/v1/blockchains")
async def get_blockchain_stats(db: SessionLocal = Depends(get_db)):
    """
    Get statistics for different blockchain networks
    """
    try:
        from sqlalchemy import func
        from app.database.database import ThreatIntelDB
        
        results = db.query(
            ThreatIntelDB.blockchain,
            func.count(ThreatIntelDB.id).label('count'),
            func.sum(ThreatIntelDB.amount_lost).label('total_lost'),
            func.avg(ThreatIntelDB.severity_score).label('avg_severity'),
            func.count(func.distinct(ThreatIntelDB.protocol_name)).label('protocols_affected')
        ).filter(
            ThreatIntelDB.blockchain.isnot(None)
        ).group_by(
            ThreatIntelDB.blockchain
        ).order_by(func.sum(ThreatIntelDB.amount_lost).desc()).all()
        
        blockchain_stats = []
        for result in results:
            blockchain_stats.append({
                "blockchain": result.blockchain,
                "incident_count": result.count,
                "total_amount_lost": result.total_lost or 0,
                "average_severity": float(result.avg_severity or 0),
                "protocols_affected": result.protocols_affected
            })
        
        return {
            "status": "success",
            "blockchain_statistics": blockchain_stats
        }
    except Exception as e:
        logger.error(f"Error getting blockchain stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get blockchain stats: {str(e)}")
