"""
Health monitoring and metrics for the DeFi Guard OSINT API
"""

import time
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from app.utils.logger import logger

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    uptime_seconds: float
    timestamp: datetime

@dataclass
class APIMetrics:
    """API performance metrics"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    requests_per_minute: float
    last_request_time: Optional[datetime]
    error_rate: float

@dataclass
class ScrapingMetrics:
    """Scraping performance metrics"""
    total_scrapes: int
    successful_scrapes: int
    failed_scrapes: int
    total_items_scraped: int
    total_items_saved: int
    last_scrape_time: Optional[datetime]
    average_scrape_duration: float
    sources_status: Dict[str, str]

class HealthMonitor:
    """Monitor system and application health"""
    
    def __init__(self):
        self.start_time = time.time()
        self.api_metrics = APIMetrics(
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            average_response_time=0.0,
            requests_per_minute=0.0,
            last_request_time=None,
            error_rate=0.0
        )
        self.scraping_metrics = ScrapingMetrics(
            total_scrapes=0,
            successful_scrapes=0,
            failed_scrapes=0,
            total_items_scraped=0,
            total_items_saved=0,
            last_scrape_time=None,
            average_scrape_duration=0.0,
            sources_status={}
        )
        self.request_times = []
        self.scrape_durations = []
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics (simplified without psutil)"""
        try:
            # Basic disk usage
            total, used, free = shutil.disk_usage('/')
            disk_percent = (used / total) * 100
            disk_used_gb = used / (1024 * 1024 * 1024)
            disk_total_gb = total / (1024 * 1024 * 1024)
            
            # Try to get memory info from /proc/meminfo (Linux only)
            memory_percent = 0.0
            memory_used_mb = 0.0
            memory_total_mb = 0.0
            
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    for line in meminfo.split('\n'):
                        if 'MemTotal:' in line:
                            memory_total_mb = int(line.split()[1]) / 1024
                        elif 'MemAvailable:' in line:
                            available_mb = int(line.split()[1]) / 1024
                            memory_used_mb = memory_total_mb - available_mb
                            memory_percent = (memory_used_mb / memory_total_mb) * 100
                            break
            except (FileNotFoundError, PermissionError, Exception):
                # Not on Linux or can't read /proc/meminfo
                pass
            
            # CPU percentage - simplified (just return 0 since we can't easily get it without psutil)
            cpu_percent = 0.0
            
            # Uptime
            uptime_seconds = time.time() - self.start_time
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=round(memory_used_mb, 2),
                memory_total_mb=round(memory_total_mb, 2),
                disk_percent=round(disk_percent, 2),
                disk_used_gb=round(disk_used_gb, 2),
                disk_total_gb=round(disk_total_gb, 2),
                uptime_seconds=uptime_seconds,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_total_mb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                disk_total_gb=0.0,
                uptime_seconds=time.time() - self.start_time,
                timestamp=datetime.utcnow()
            )
    
    def record_api_request(self, success: bool, response_time: float):
        """Record API request metrics"""
        self.api_metrics.total_requests += 1
        
        if success:
            self.api_metrics.successful_requests += 1
        else:
            self.api_metrics.failed_requests += 1
        
        self.api_metrics.last_request_time = datetime.utcnow()
        
        # Update response time tracking
        self.request_times.append(response_time)
        if len(self.request_times) > 1000:  # Keep only last 1000 requests
            self.request_times = self.request_times[-1000:]
        
        self.api_metrics.average_response_time = sum(self.request_times) / len(self.request_times)
        self.api_metrics.error_rate = (self.api_metrics.failed_requests / self.api_metrics.total_requests) * 100
        
        # Calculate requests per minute (last 60 seconds)
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_requests = len([t for t in self.request_times if t > one_minute_ago.timestamp()])
        self.api_metrics.requests_per_minute = recent_requests
    
    def record_scrape_attempt(self, success: bool, duration: float, items_scraped: int = 0, items_saved: int = 0, source: str = ""):
        """Record scraping attempt metrics"""
        self.scraping_metrics.total_scrapes += 1
        
        if success:
            self.scraping_metrics.successful_scrapes += 1
            self.scraping_metrics.total_items_scraped += items_scraped
            self.scraping_metrics.total_items_saved += items_saved
            self.scraping_metrics.sources_status[source] = "success"
        else:
            self.scraping_metrics.failed_scrapes += 1
            self.scraping_metrics.sources_status[source] = "failed"
        
        self.scraping_metrics.last_scrape_time = datetime.utcnow()
        
        # Update duration tracking
        self.scrape_durations.append(duration)
        if len(self.scrape_durations) > 100:  # Keep only last 100 scrapes
            self.scrape_durations = self.scrape_durations[-100:]
        
        self.scraping_metrics.average_scrape_duration = sum(self.scrape_durations) / len(self.scrape_durations)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        system_metrics = self.get_system_metrics()
        
        # Determine health status
        health_issues = []
        
        if system_metrics.cpu_percent > 80:
            health_issues.append("High CPU usage")
        
        if system_metrics.memory_percent > 85:
            health_issues.append("High memory usage")
        
        if system_metrics.disk_percent > 90:
            health_issues.append("Low disk space")
        
        if self.api_metrics.error_rate > 10:
            health_issues.append("High API error rate")
        
        # Overall status
        if not health_issues:
            status = "healthy"
        elif len(health_issues) <= 2:
            status = "warning"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": system_metrics.uptime_seconds,
            "uptime_human": self._format_uptime(system_metrics.uptime_seconds),
            "issues": health_issues,
            "system": asdict(system_metrics),
            "api": asdict(self.api_metrics),
            "scraping": asdict(self.scraping_metrics)
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for monitoring dashboards"""
        system_metrics = self.get_system_metrics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "performance": {
                "cpu_usage": system_metrics.cpu_percent,
                "memory_usage": system_metrics.memory_percent,
                "disk_usage": system_metrics.disk_percent,
                "average_response_time": self.api_metrics.average_response_time,
                "requests_per_minute": self.api_metrics.requests_per_minute,
                "error_rate": self.api_metrics.error_rate,
                "scraping_success_rate": (
                    self.scraping_metrics.successful_scrapes / max(1, self.scraping_metrics.total_scrapes)
                ) * 100
            },
            "totals": {
                "total_requests": self.api_metrics.total_requests,
                "total_scrapes": self.scraping_metrics.total_scrapes,
                "total_items_scraped": self.scraping_metrics.total_items_scraped,
                "total_items_saved": self.scraping_metrics.total_items_saved
            }
        }

# Global health monitor instance
health_monitor = HealthMonitor()

def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance"""
    return health_monitor
