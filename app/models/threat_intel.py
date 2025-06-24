from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatIntelItem(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier")
    title: str = Field(..., description="Title of the threat intelligence item")
    description: str = Field(..., description="Detailed description of the threat")
    protocol_name: Optional[str] = Field(None, description="Name of the affected DeFi protocol")
    risk_level: RiskLevel = Field(..., description="Risk level assessment")
    source_url: HttpUrl = Field(..., description="Source URL of the article/report")
    source_name: str = Field(..., description="Name of the source (e.g., Rekt, Chainalysis)")
    published_date: Optional[date] = Field(None, description="Publication date")
    scraped_date: datetime = Field(default_factory=datetime.utcnow, description="Date when data was scraped")
    tags: List[str] = Field(default_factory=list, description="Related tags/keywords")
    amount_lost: Optional[float] = Field(None, description="Amount lost in USD (if applicable)")
    attack_type: Optional[str] = Field(None, description="Type of attack (if applicable)")
    blockchain: Optional[str] = Field(None, description="Blockchain network affected")
    severity_score: Optional[float] = Field(None, ge=0, le=10, description="Severity score (0-10)")
    is_verified: bool = Field(default=False, description="Whether the information is verified")
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None
        }

class ThreatIntelResponse(BaseModel):
    status: str = Field(..., description="Response status")
    count: int = Field(..., description="Number of items returned")
    total_count: Optional[int] = Field(None, description="Total number of items available")
    data: List[ThreatIntelItem] = Field(..., description="List of threat intelligence items")
    filters_applied: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Filters applied to the query")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")

class ScrapeRequest(BaseModel):
    sources: Optional[List[str]] = Field(None, description="List of sources to scrape")
    force_refresh: bool = Field(default=False, description="Force refresh of cached data")
    max_pages: Optional[int] = Field(default=5, description="Maximum pages to scrape per source")

class ScrapeResponse(BaseModel):
    status: str = Field(..., description="Scrape status")
    sources_scraped: List[str] = Field(..., description="List of sources that were scraped")
    items_found: int = Field(..., description="Number of new items found")
    errors: Optional[List[str]] = Field(default_factory=list, description="Any errors encountered")
    duration: Optional[float] = Field(None, description="Scraping duration in seconds")
