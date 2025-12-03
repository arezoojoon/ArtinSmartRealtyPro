#!/bin/bash
# Deploy Subscription Fix to Production
# Run this on the VPS server

cd /opt/ArtinSmartRealty

echo "📥 Pulling latest code..."
git pull origin main

echo "🔨 Rebuilding backend container..."
docker-compose up -d --build backend

echo "⏳ Waiting for backend to start..."
sleep 5

echo "🔍 Checking backend health..."
docker-compose logs --tail=20 backend

echo "✅ Deployment complete!"
echo ""
echo "🧪 Test subscription update:"
echo "1. Login as Super Admin at https://realty.artinsmartagent.com/"
echo "2. Go to SuperAdminDashboard"
echo "3. Change Tenant subscription from Trial → Active"
echo "4. Should see: ✅ Subscription updated to ACTIVE"
