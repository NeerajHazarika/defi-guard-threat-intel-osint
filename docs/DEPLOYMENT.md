# DeFi Guard OSINT API - Deployment Guide

## Docker Deployment (Recommended)

### Prerequisites
- Docker and Docker Compose
- OpenAI API key

### Quick Start
```bash
# 1. Clone repository
git clone <repository-url>
cd defi-guard-osint

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=your_api_key_here

# 3. Start services
docker-compose up -d

# 4. Verify deployment
curl http://localhost:8000/
```

### Services
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Database**: PostgreSQL (internal)
- **Cache**: Redis (internal)

## Manual Installation

### Prerequisites
- Python 3.11+
- PostgreSQL (optional, SQLite by default)
- OpenAI API key

### Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Add your OpenAI API key to .env

# 3. Initialize database
python -c "from app.database.database import create_tables; create_tables()"

# 4. Run application
uvicorn app.main:app --host 0.0.0.0 --port 8000
## Environment Variables

### Required
- `OPENAI_API_KEY`: Your OpenAI API key for protocol classification

### Optional  
- `DATABASE_URL`: PostgreSQL connection string (defaults to SQLite)
- `REDIS_URL`: Redis connection string (optional caching)
- `SECRET_KEY`: API secret key
- `DEBUG`: Debug mode (default: False)

## Basic Usage

### 1. Get Threat Intelligence
```bash
curl "http://localhost:8000/api/v1/threat-intel?limit=5"
```

### 2. Trigger Scraping
```bash
curl -X POST "http://localhost:8000/api/v1/scrape" \
     -H "Content-Type: application/json" \
     -d '{"sources": ["rekt", "chainalysis"]}'
```

### 3. View Statistics
```bash
curl "http://localhost:8000/api/v1/stats"
```

## Monitoring

### Health Check
```bash
curl http://localhost:8000/
```

### Logs
```bash
# Docker logs
docker-compose logs -f defi-guard-api

# Local logs
tail -f logs/defi_guard.log
```

## Troubleshooting

### Common Issues
1. **OpenAI API errors**: Verify your API key is set correctly
2. **Database connection**: Check DATABASE_URL if using PostgreSQL
3. **Port conflicts**: Change port in docker-compose.yml if needed

### Reset Database
```bash
# Docker
docker-compose exec defi-guard-api python -c "from app.database.database import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"

# Local
python -c "from app.database.database import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"
```
