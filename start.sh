#!/bin/bash

# DeFi Guard OSINT API Startup Script

set -e

echo "=== DeFi Guard OSINT API Startup ==="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before proceeding."
    exit 1
fi

# Check if using Docker
if command -v docker-compose &> /dev/null; then
    echo "Docker Compose detected. Starting services..."
    
    # Build and start services
    docker-compose up -d --build
    
    echo "Services started. Waiting for database to be ready..."
    sleep 10
    
    # Initialize database in container
    docker-compose exec defi-guard-api python scripts/init_db.py
    
    echo "=== API is ready! ==="
    echo "API URL: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
    echo "Health Check: http://localhost:8000/"
    
else
    echo "Docker not found. Starting manually..."
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
    echo "Python version: $python_version"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        echo "Error: Python 3.8+ is required"
        exit 1
    fi
    
    # Install dependencies
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
    
    # Initialize database
    echo "Initializing database..."
    python3 scripts/init_db.py
    
    # Start the API server
    echo "Starting API server..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
