# DeFi Guard OSINT API

A comprehensive threat intelligence API for DeFi protocols that scrapes and analyzes security incidents, exploits, and vulnerabilities from multiple sources including Rekt News and Chainalysis.

## Features

- **Multi-source scraping**: Automatically scrapes threat intelligence from Rekt News, Chainalysis, and other sources
- **AI-powered protocol detection**: Uses OpenAI ChatGPT for accurate DeFi protocol identification and threat relevance assessment
- **Smart filtering**: Only stores protocol-specific threat intelligence, filtering out generic articles
- **Risk assessment**: Automatically categorizes threats by risk level (Low, Medium, High, Critical)
- **Amount tracking**: Extracts and tracks financial losses from incidents
- **RESTful API**: Clean API endpoints for easy integration
- **Real-time data**: Background scraping with up-to-date threat intelligence
- **Flexible filtering**: Filter by protocol, risk level, source, date range, and more
- **Dockerized**: Easy deployment with Docker and Docker Compose

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd defi-guard-osint
```

2. Copy environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=your_openai_api_key_here
```

3. Start the services:
```bash
docker-compose up -d
```

4. The API will be available at `http://localhost:8000`

### Manual Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration, including OpenAI API key
```

3. Initialize the database:
```bash
python -c "from app.database.database import create_tables; create_tables()"
```

4. Run the application:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Core Endpoints

#### `GET /api/v1/threat-intel`
Get threat intelligence data with optional filters.

**Query Parameters:**
- `protocol` (string): Filter by DeFi protocol name
- `risk_level` (string): Filter by risk level (low, medium, high, critical)
- `source` (string): Filter by source (rekt, chainalysis)
- `limit` (int): Number of results (default: 50, max: 1000)
- `offset` (int): Number of results to skip (default: 0)
- `fresh_scrape` (bool): Force fresh scraping (default: false)

**Example:**
```bash
curl "http://localhost:8000/api/v1/threat-intel?protocol=uniswap&risk_level=high&limit=10"
```

**Response:**
```json
{
  "status": "success",
  "count": 10,
  "data": [
    {
      "id": "abc123",
      "title": "Uniswap V3 Flash Loan Attack",
      "description": "Detailed description of the attack...",
      "protocol_name": "Uniswap",
      "risk_level": "high",
      "source_url": "https://rekt.news/uniswap-attack/",
      "source_name": "Rekt News",
      "published_date": "2024-01-15",
      "amount_lost": 15000000.0,
      "attack_type": "flash_loan_attack",
      "blockchain": "Ethereum",
      "severity_score": 8.5,
      "tags": ["exploit", "flash_loan", "defi"],
      "is_verified": true
    }
  ]
}
```

#### `POST /api/v1/scrape`
Trigger manual scraping of threat intelligence sources.

**Body:**
```json
{
  "sources": ["rekt", "chainalysis"]  // optional, scrapes all if not provided
}
```

#### `GET /api/v1/sources`
Get list of available threat intelligence sources.

#### `GET /api/v1/protocols`
Get list of DeFi protocols with threat intelligence data.

#### `GET /api/v1/stats`
Get statistics about the threat intelligence database.

### Data Model

Each threat intelligence item contains:

- **id**: Unique identifier
- **title**: Title of the threat/incident
- **description**: Detailed description
- **protocol_name**: Affected DeFi protocol (auto-detected)
- **risk_level**: Risk assessment (low/medium/high/critical)
- **source_url**: Original article/report URL
- **source_name**: Source publication name
- **published_date**: When the article was published (date only)
- **scraped_date**: When we scraped the data
- **amount_lost**: Financial loss in USD (if applicable)
- **attack_type**: Type of attack (if applicable)
- **blockchain**: Affected blockchain network
- **severity_score**: Numerical severity score (0-10)
- **tags**: Related keywords/categories
- **is_verified**: Whether the information is verified
- **additional_data**: Source-specific metadata

## Sources

### Currently Supported

1. **Rekt News** (`rekt`)
   - DeFi security incidents and post-mortems
   - High-quality verified reports
   - Focus on major exploits and hacks

2. **Chainalysis** (`chainalysis`)
   - Professional blockchain analysis
   - Market trends and threat analysis
   - Regulatory and compliance insights

### Planned Sources

- CoinDesk Security section
- The Block security reports
- Immunefi vulnerability reports
- Official protocol security advisories
- GitHub security advisories

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Scrapers      │    │   Database      │
│                 │    │                 │    │                 │
│ • REST API      │◄──►│ • Rekt Scraper  │◄──►│ • PostgreSQL    │
│ • Data Models   │    │ • Chainalysis   │    │ • SQLAlchemy    │
│ • Validation    │    │ • Base Scraper  │    │ • Alembic       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Scheduler     │
│                 │    │                 │
│ • React/Vue     │    │ • Background    │
│ • Dashboard     │    │ • Auto-scraping │
│ • Alerts        │    │ • Rate Limiting │
└─────────────────┘    └─────────────────┘
```

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string (for caching)
- `OPENAI_API_KEY`: OpenAI API key for protocol classification (required)
- `SECRET_KEY`: API secret key
- `DEBUG`: Debug mode (True/False)
- `SCRAPER_DELAY`: Delay between requests (seconds)
- `MAX_CONCURRENT_REQUESTS`: Max concurrent scraping requests

### Docker Configuration

The application is fully containerized with:
- **API Container**: FastAPI application
- **Database Container**: PostgreSQL 15
- **Cache Container**: Redis 7
- **Volume**: Persistent database storage

## Development

### Adding New Sources

1. Create a new scraper class inheriting from `BaseScraper`:

```python
from app.scrapers.base_scraper import BaseScraper

class NewSourceScraper(BaseScraper):
    def __init__(self):
        super().__init__(name="New Source", base_url="https://newsource.com")
    
    async def scrape(self) -> List[ThreatIntelItem]:
        # Implement scraping logic
        pass
```

2. Register the scraper in `ScraperManager`:

```python
self.scrapers["newsource"] = NewSourceScraper()
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## API Documentation

Once the application is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Monitoring and Logging

- Logs are written to `logs/defi_guard.log`
- Console output with structured logging
- Health check endpoint at `/`
- Statistics endpoint for monitoring data freshness

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub  
- Check the documentation at `/docs`
- Review logs in the `logs/` directory
