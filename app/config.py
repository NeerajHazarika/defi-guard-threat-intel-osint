"""
Configuration settings for DeFi Guard OSINT API
"""

import os
from typing import List, Dict, Any
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Settings
    api_title: str = Field(default="DeFi Guard OSINT API", env="API_TITLE")
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    api_description: str = Field(default="Threat Intelligence API for DeFi Protocols", env="API_DESCRIPTION")
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    
    # Database Settings
    database_url: str = Field(default="sqlite:///./defi_guard.db", env="DATABASE_URL")
    
    # Redis Settings
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Scraping Settings
    scraper_delay: float = Field(default=1.0, env="SCRAPER_DELAY")
    max_concurrent_requests: int = Field(default=5, env="MAX_CONCURRENT_REQUESTS")
    user_agent: str = Field(default="DeFiGuard-OSINT-Bot/1.0", env="USER_AGENT")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # Scheduler Settings
    enable_background_scraping: bool = Field(default=True, env="ENABLE_BACKGROUND_SCRAPING")
    scraping_interval_hours: int = Field(default=4, env="SCRAPING_INTERVAL_HOURS")
    maintenance_hour: int = Field(default=2, env="MAINTENANCE_HOUR")  # 2 AM
    
    # Data Retention Settings
    max_items_per_source: int = Field(default=1000, env="MAX_ITEMS_PER_SOURCE")
    data_retention_days: int = Field(default=365, env="DATA_RETENTION_DAYS")
    
    # Source Configuration
    sources_config: Dict[str, Dict[str, Any]] = {
        "rekt": {
            "enabled": True,
            "base_url": "https://rekt.news",
            "max_pages": 5,
            "rate_limit": 2.0,  # seconds between requests
            "priority": 1
        },
        "chainalysis": {
            "enabled": True,
            "base_url": "https://blog.chainalysis.com",
            "max_pages": 3,
            "rate_limit": 3.0,
            "priority": 2
        }
    }
    
    # Risk Assessment Configuration
    risk_thresholds: Dict[str, Dict[str, Any]] = {
        "amount_lost": {
            "low": 0,
            "medium": 100_000,
            "high": 1_000_000,
            "critical": 10_000_000
        },
        "severity_score": {
            "low": 0.0,
            "medium": 4.0,
            "high": 7.0,
            "critical": 9.0
        }
    }
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/defi_guard.log", env="LOG_FILE")
    log_rotation: str = Field(default="1 day", env="LOG_ROTATION")
    log_retention: str = Field(default="30 days", env="LOG_RETENTION")
    
    # API Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # CORS Settings
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")
    cors_methods: List[str] = Field(default=["*"], env="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")
    
    # Feature Flags
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_auth: bool = Field(default=False, env="ENABLE_AUTH")
    
    # Chrome/Selenium Settings (for future use with dynamic content)
    chrome_headless: bool = Field(default=True, env="CHROME_HEADLESS")
    chrome_no_sandbox: bool = Field(default=True, env="CHROME_NO_SANDBOX")
    chrome_disable_dev_shm: bool = Field(default=True, env="CHROME_DISABLE_DEV_SHM")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

def get_source_config(source_name: str) -> Dict[str, Any]:
    """Get configuration for a specific source"""
    return settings.sources_config.get(source_name, {})

def get_enabled_sources() -> List[str]:
    """Get list of enabled sources"""
    return [
        source for source, config in settings.sources_config.items()
        if config.get("enabled", False)
    ]

def get_risk_threshold(metric: str, level: str) -> float:
    """Get risk threshold for a metric and level"""
    return settings.risk_thresholds.get(metric, {}).get(level, 0)

def is_development() -> bool:
    """Check if running in development mode"""
    return settings.debug

def get_chrome_options() -> List[str]:
    """Get Chrome options for Selenium (future use)"""
    options = []
    
    if settings.chrome_headless:
        options.append("--headless")
    
    if settings.chrome_no_sandbox:
        options.append("--no-sandbox")
    
    if settings.chrome_disable_dev_shm:
        options.append("--disable-dev-shm-usage")
    
    options.extend([
        "--disable-gpu",
        "--window-size=1920,1080",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-images",
        "--disable-javascript",
        f"--user-agent={settings.user_agent}"
    ])
    
    return options

# Environment-specific configurations
def get_database_config() -> Dict[str, Any]:
    """Get database configuration"""
    config = {
        "url": settings.database_url,
        "echo": settings.debug,  # Log SQL queries in debug mode
        "pool_size": 5,
        "max_overflow": 10
    }
    
    # SQLite-specific settings
    if settings.database_url.startswith("sqlite"):
        config["connect_args"] = {"check_same_thread": False}
    
    return config

def get_redis_config() -> Dict[str, Any]:
    """Get Redis configuration"""
    return {
        "url": settings.redis_url,
        "decode_responses": True,
        "socket_timeout": 5,
        "socket_connect_timeout": 5,
        "retry_on_timeout": True
    }
