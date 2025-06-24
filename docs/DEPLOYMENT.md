# DeFi Guard OSINT API - Deployment Guide

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- At least 2GB RAM
- 10GB free disk space

### 1. Clone and Setup
```bash
git clone <repository-url>
cd defi-guard-osint

# Copy environment configuration
cp .env.example .env

# Edit .env if needed (optional for local development)
# nano .env
```

### 2. Start Services
```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f defi-guard-api

# Initialize database (first time only)
docker-compose exec defi-guard-api python scripts/init_db.py
```

### 3. Verify Installation
```bash
# Test API
curl http://localhost:8000/

# Run comprehensive tests
python test_api.py
```

### 4. Access API
- **API Base URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## Manual Installation

### Prerequisites
- Python 3.8+
- PostgreSQL (optional, SQLite is default)
- Redis (optional, for caching)

### 1. Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy environment file
cp .env.example .env

# Edit configuration
# Set DATABASE_URL, REDIS_URL, etc.
```

### 3. Initialize Database
```bash
# Run initialization script
python scripts/init_db.py

# Start the API
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Production Deployment

### Environment Variables
Configure these environment variables for production:

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Redis (optional)
REDIS_URL=redis://host:port

# Security
SECRET_KEY=your-secure-secret-key
DEBUG=False

# API Configuration
API_TITLE=DeFi Guard OSINT API
API_VERSION=1.0.0

# Scraping
SCRAPER_DELAY=2.0
MAX_CONCURRENT_REQUESTS=3
ENABLE_BACKGROUND_SCRAPING=True
SCRAPING_INTERVAL_HOURS=6

# Logging
LOG_LEVEL=INFO
```

### Docker Production Setup

1. **Create production docker-compose.yml:**
```yaml
version: '3.8'

services:
  defi-guard-api:
    image: defi-guard-osint:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/defi_guard
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
    depends_on:
      - db
      - redis
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=defi_guard
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - defi-guard-api
    restart: unless-stopped

volumes:
  postgres_data:
```

2. **Nginx Configuration:**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server defi-guard-api:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Cloud Deployment Options

#### AWS ECS/Fargate
1. Build and push Docker image to ECR
2. Create ECS task definition
3. Deploy as Fargate service
4. Use RDS for PostgreSQL
5. Use ElastiCache for Redis

#### Google Cloud Run
1. Build and push to Container Registry
2. Deploy to Cloud Run
3. Use Cloud SQL for PostgreSQL
4. Use Memorystore for Redis

#### Azure Container Instances
1. Build and push to Azure Container Registry
2. Deploy to Container Instances
3. Use Azure Database for PostgreSQL
4. Use Azure Cache for Redis

### Kubernetes Deployment

Create Kubernetes manifests:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: defi-guard-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: defi-guard-api
  template:
    metadata:
      labels:
        app: defi-guard-api
    spec:
      containers:
      - name: api
        image: defi-guard-osint:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: defi-guard-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: defi-guard-secrets
              key: secret-key

---
apiVersion: v1
kind: Service
metadata:
  name: defi-guard-api-service
spec:
  selector:
    app: defi-guard-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Monitoring and Maintenance

### Health Checks
The API provides several health check endpoints:
- `GET /` - Basic health check
- `GET /api/v1/stats` - Detailed statistics
- Database connectivity check
- Source availability check

### Logging
Logs are written to:
- Console (structured JSON in production)
- File: `logs/defi_guard.log`
- Rotation: Daily, 30-day retention

### Metrics
Monitor these key metrics:
- Response time
- Error rate
- Scraping success rate
- Database connections
- Memory usage
- CPU usage

### Backup Strategy
1. **Database Backups:**
   - Daily automated backups
   - Point-in-time recovery
   - Cross-region replication

2. **Configuration Backups:**
   - Environment variables
   - Docker configurations
   - Nginx configurations

### Scaling
- **Horizontal scaling**: Multiple API instances behind load balancer
- **Vertical scaling**: Increase CPU/memory for single instance
- **Database scaling**: Read replicas, connection pooling
- **Caching**: Redis for frequently accessed data

## Security Considerations

### Network Security
- Use HTTPS in production
- Implement proper firewall rules
- Use private networks for internal communication
- Consider VPN for management access

### Application Security
- Keep dependencies updated
- Use strong secret keys
- Implement rate limiting
- Validate all inputs
- Use parameterized database queries

### Data Security
- Encrypt sensitive data at rest
- Use secure database connections
- Implement proper access controls
- Regular security audits

## Troubleshooting

### Common Issues

1. **Database Connection Errors:**
   ```bash
   # Check database connectivity
   docker-compose exec defi-guard-api python -c "from app.database.database import engine; print(engine.connect())"
   ```

2. **Scraping Failures:**
   ```bash
   # Check scraper logs
   docker-compose logs defi-guard-api | grep -i scraper
   
   # Test individual scrapers
   docker-compose exec defi-guard-api python -c "
   import asyncio
   from app.scrapers.rekt_scraper import RektScraper
   scraper = RektScraper()
   asyncio.run(scraper.scrape())
   "
   ```

3. **High Memory Usage:**
   - Check for memory leaks
   - Increase container memory limits
   - Optimize database queries
   - Implement proper pagination

4. **Slow Response Times:**
   - Check database performance
   - Optimize queries with indexes
   - Implement caching
   - Scale horizontally

### Support
- Check logs in `logs/defi_guard.log`
- Review API documentation at `/docs`
- Monitor system metrics
- Check database connectivity
- Verify source accessibility
