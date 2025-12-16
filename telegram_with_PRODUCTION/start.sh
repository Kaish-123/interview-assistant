#!/bin/bash

# TechyEra Marketing - Start Script

echo "🚀 TechyEra Marketing - Production Setup"
echo "========================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env with your configuration"
fi

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -q

# Check if PostgreSQL is available
echo "🔍 Checking PostgreSQL..."
if command -v docker &> /dev/null; then
    if ! docker ps | grep -q "postgres"; then
        echo "🐘 Starting PostgreSQL with Docker..."
        docker run -d --name techyera-postgres \
            -e POSTGRES_PASSWORD=password \
            -e POSTGRES_DB=techyera_db \
            -p 5432:5432 \
            postgres:15-alpine 2>/dev/null || true
        sleep 5
    fi
fi

# Start the application
echo ""
echo "✅ Starting TechyEra Marketing..."
echo "📍 Dashboard: http://localhost:8000"
echo "📍 API Docs:  http://localhost:8000/docs"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

