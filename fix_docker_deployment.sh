#!/bin/bash
# Fix Docker Image Corruption and Deploy Subscription Fix
# Run this on VPS: ssh root@srv1151343.hstgr.io < fix_docker_deployment.sh

set -e  # Exit on error

cd /opt/ArtinSmartRealty

echo "🛑 Stopping all containers..."
docker-compose down

echo "🧹 Cleaning up corrupted Docker images..."
docker system prune -af --volumes

echo "📥 Pulling latest code..."
git pull origin main

echo "🔨 Building fresh backend image..."
docker-compose build --no-cache backend

echo "🚀 Starting all services..."
docker-compose up -d

echo "⏳ Waiting for services to start (15 seconds)..."
sleep 15

echo ""
echo "🔍 Backend container status:"
docker-compose ps backend

echo ""
echo "📋 Recent backend logs:"
docker-compose logs --tail=30 backend | grep -E "(INFO|ERROR|Started|Uvicorn)"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🧪 TEST THE FIX:"
echo "1. Visit: https://realty.artinsmartagent.com/"
echo "2. Login: admin@artinsmartrealty.com / SuperAdmin123!"
echo "3. Change tenant subscription: Trial → Active"
echo "4. Should see: ✅ Subscription updated to ACTIVE"
