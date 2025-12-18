#!/bin/bash
# Database Fix Script - Run on Production Server
# This creates the database if missing and runs migrations

echo "🔧 Step 1: Checking database existence..."
docker-compose exec -T db psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'artinrealty'" | grep -q 1 || \
docker-compose exec -T db psql -U postgres -c "CREATE DATABASE artinrealty;"

echo "✅ Database 'artinrealty' exists"

echo "🔧 Step 2: Running Alembic migrations..."
docker-compose exec -T backend alembic upgrade head

echo "🔧 Step 3: Restarting backend..."
docker-compose restart backend

echo "🔧 Step 4: Checking backend health..."
sleep 5
curl -s http://localhost:8000/health

echo ""
echo "✅ Database fix complete!"
echo "📊 View logs: docker-compose logs -f backend"
