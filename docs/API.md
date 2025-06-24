# DeFi Guard OSINT API - Endpoints Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the API does not require authentication. This may be added in future versions.

## Response Format
All API responses follow this format:
```json
{
  "status": "success|error",
  "data": [...],
  "count": 0,
  "message": "Optional message"
}
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
      "description": "Detailed description...",
      "protocol_name": "Uniswap",
      "risk_level": "high",
      "source_url": "https://rekt.news/example/",
      "source_name": "Rekt News",
      "published_date": "2024-01-15T10:30:00Z",
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

### 3. Search Threats
**GET /api/v1/search**
Search threat intelligence by text query.

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (int): Number of results (1-100, default: 20)

**Example:**
```bash
curl "http://localhost:8000/api/v1/search?q=flash%20loan&limit=5"
```

### 4. Get Trending Threats
**GET /api/v1/trending**
Get trending threats based on recent activity and severity.

**Query Parameters:**
- `days` (int): Number of days to look back (1-30, default: 7)
- `limit` (int): Number of results (1-50, default: 10)

**Example:**
```bash
curl "http://localhost:8000/api/v1/trending?days=14&limit=5"
```

### 5. Manual Scraping
**POST /api/v1/scrape**
Trigger manual scraping of threat intelligence sources.

**Request Body:**
```json
{
  "sources": ["rekt", "chainalysis"]  // Optional, scrapes all if not provided
}
```

**Response:**
```json
{
  "message": "Scraping initiated",
  "status": "started"
}
```

### 6. Get Available Sources
**GET /api/v1/sources**
Get list of available threat intelligence sources.

**Response:**
```json
{
  "status": "success",
  "sources": ["rekt", "chainalysis"]
}
```

### 7. Get Protocols
**GET /api/v1/protocols**
Get list of DeFi protocols with threat intelligence data.

**Response:**
```json
{
  "status": "success",
  "protocols": [
    {
      "name": "Uniswap",
      "incident_count": 15,
      "total_amount_lost": 50000000.0,
      "max_severity_score": 9.2,
      "latest_incident_date": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 8. Get Protocol Details
**GET /api/v1/protocols/{protocol_name}**
Get detailed information for a specific protocol.

**Path Parameters:**
- `protocol_name` (string): Name of the protocol

**Query Parameters:**
- `limit` (int): Number of incidents to return (1-100, default: 20)

**Example:**
```bash
curl "http://localhost:8000/api/v1/protocols/uniswap?limit=5"
```

### 9. Get Statistics
**GET /api/v1/stats**
Get general statistics about the threat intelligence database.

**Response:**
```json
{
  "status": "success",
  "stats": {
    "total_incidents": 1250,
    "verified_incidents": 1100,
    "verification_rate": 88.0,
    "total_amount_lost": 2500000000.0,
    "average_amount_lost": 2000000.0,
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
    },
    "latest_update": "2024-01-15T12:00:00Z"
  }
}
```

### 10. Get Threats by Risk Level
**GET /api/v1/risk-levels/{risk_level}**
Get threats filtered by specific risk level.

**Path Parameters:**
- `risk_level` (string): Risk level (low, medium, high, critical)

**Query Parameters:**
- `limit` (int): Number of results (1-200, default: 50)
- `offset` (int): Number of results to skip (default: 0)

**Example:**
```bash
curl "http://localhost:8000/api/v1/risk-levels/critical?limit=10"
```

### 11. Get Attack Types
**GET /api/v1/attack-types**
Get list of all attack types with statistics.

**Response:**
```json
{
  "status": "success",
  "attack_types": [
    {
      "attack_type": "flash_loan_attack",
      "incident_count": 125,
      "total_amount_lost": 500000000.0,
      "average_severity": 7.8
    }
  ]
}
```

### 12. Get Blockchain Statistics
**GET /api/v1/blockchains**
Get statistics for different blockchain networks.

**Response:**
```json
{
  "status": "success",
  "blockchain_statistics": [
    {
      "blockchain": "Ethereum",
      "incident_count": 850,
      "total_amount_lost": 1800000000.0,
      "average_severity": 6.9,
      "protocols_affected": 120
    }
  ]
}
```

## Error Responses

All endpoints may return error responses in this format:

**400 Bad Request:**
```json
{
  "detail": "Invalid parameter value"
}
```

**404 Not Found:**
```json
{
  "detail": "Resource not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error: [error description]"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:
- Default: 100 requests per minute per IP
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`: Request limit per window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

## Data Models

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
  "published_date": "string (ISO datetime)|null",
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

## Best Practices

### Efficient API Usage
1. Use appropriate `limit` values to avoid large responses
2. Implement pagination with `offset` for large datasets
3. Cache responses when possible
4. Use specific filters to reduce data transfer

### Error Handling
1. Always check the `status` field in responses
2. Implement retry logic for 5xx errors
3. Handle rate limiting gracefully
4. Log errors for debugging

### Performance
1. Avoid setting `fresh_scrape=true` frequently
2. Use trending and search endpoints for real-time data
3. Consider the impact of large `limit` values
4. Monitor response times and adjust accordingly

## WebSocket Support (Future)
Planned features for real-time updates:
- Real-time threat alerts
- Live scraping status updates
- Protocol-specific notifications

## SDK and Libraries (Future)
Planned client libraries:
- Python SDK
- JavaScript/TypeScript SDK
- Go SDK
