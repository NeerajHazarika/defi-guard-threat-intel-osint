# DeFi Guard OSINT API - Documentation

## Base URL
```
http://localhost:8000
```

## Core Endpoints

### 1. Health Check
**GET /** 
Check if the API is running and healthy.

**Response:**
```json
{
  "message": "DeFi Guard OSINT API is running",
  "status": "healthy"
}
```

### 2. Get Threat Intelligence
**GET /api/v1/threat-intel**
Retrieve threat intelligence data with optional filtering.

**Query Parameters:**
- `protocol` (string): Filter by DeFi protocol name
- `risk_level` (string): Filter by risk level (low, medium, high, critical)
- `source` (string): Filter by source (rekt, chainalysis)
- `limit` (int): Number of results (1-1000, default: 50)
- `offset` (int): Number of results to skip (default: 0)

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
      "description": "Detailed description...",
      "protocol_name": "Uniswap",
      "risk_level": "high",
      "source_url": "https://rekt.news/example/",
      "source_name": "Rekt News",
      "published_date": "2024-01-15",
      "scraped_date": "2024-01-15T11:00:00Z",
      "amount_lost": 15000000.0,
      "attack_type": "flash_loan_attack",
      "blockchain": "Ethereum",
      "severity_score": 8.5,
      "tags": ["exploit", "flash_loan", "defi"],
      "is_verified": true,
      "additional_data": {}
    }
  ]
}
```

### 3. Manual Scraping
**POST /api/v1/scrape**
Trigger manual scraping of threat intelligence sources.

**Request Body:**
```json
{
  "sources": ["rekt", "chainalysis"]
}
```

**Response:**
```json
{
  "message": "Scraping initiated",
  "status": "started"
}
```

### 4. Get Statistics
**GET /api/v1/stats**
Get general statistics about the threat intelligence database.

**Response:**
```json
{
  "status": "success",
  "stats": {
    "total_incidents": 1250,
    "total_amount_lost": 2500000000.0,
    "recent_incidents_30d": 45,
    "risk_level_distribution": {
      "low": 300,
      "medium": 450,
      "high": 350,
      "critical": 150
    },
    "source_distribution": {
      "Rekt News": 800,
      "Chainalysis": 450
    }
  }
}
```

## Data Model

### ThreatIntelItem
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "protocol_name": "string|null",
  "risk_level": "low|medium|high|critical",
  "source_url": "string (URL)",
  "source_name": "string",
  "published_date": "string (ISO date YYYY-MM-DD)|null",
  "scraped_date": "string (ISO datetime)",
  "tags": ["string"],
  "amount_lost": "number|null",
  "attack_type": "string|null",
  "blockchain": "string|null",
  "severity_score": "number|null",
  "is_verified": "boolean",
  "additional_data": "object"
}
```

### Risk Levels
- **low**: Minor issues, informational alerts
- **medium**: Moderate risks, potential vulnerabilities  
- **high**: Significant threats, confirmed exploits
- **critical**: Severe threats, major financial losses

## Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
