#!/bin/bash
# Emergency Recovery: Restore ArtinSmartRealty Services
# Run on VPS to bring everything back online

set -e

cd /opt/ArtinSmartRealty

echo "🛑 Step 1: Stop all containers..."
docker-compose down 2>/dev/null || true

echo "🧹 Step 2: Remove corrupted images and containers..."
docker system prune -f

echo "📥 Step 3: Pull latest code..."
git fetch origin
git reset --hard origin/main

echo "🔨 Step 4: Rebuild everything from scratch..."
docker-compose build --no-cache

echo "🚀 Step 5: Start all services..."
docker-compose up -d

echo "⏳ Step 6: Wait for services to initialize..."
sleep 20

echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🔍 Backend Health Check:"
curl -s http://localhost:8000/health || echo "⚠️ Backend not responding yet..."

echo ""
echo "📋 Backend Logs (last 20 lines):"
docker-compose logs --tail=20 backend

echo ""
echo "📋 Frontend Logs (last 10 lines):"
docker-compose logs --tail=10 frontend

echo ""
echo "✅ Recovery complete!"
echo ""
echo "🌐 Check website: https://realty.artinsmartagent.com/"
