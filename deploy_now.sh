#!/bin/bash
# Quick Deploy Script - ArtinSmartRealty
# Run this to deploy latest changes to production

echo "🚀 Deploying ArtinSmartRealty to Production..."
echo "================================================"

# SSH to production server
ssh root@srv1151343.hstgr.io << 'ENDSSH'

# Navigate to project
cd /opt/ArtinSmartRealty || exit 1

echo "📥 Pulling latest code from GitHub..."
git pull origin main

echo "🔄 Restarting backend service..."
docker-compose restart backend

echo "⏳ Waiting for backend to start (10 seconds)..."
sleep 10

echo "📊 Checking backend logs..."
docker-compose logs --tail=50 backend

echo ""
echo "✅ Deployment Complete!"
echo "======================="
echo ""
echo "🔍 To monitor logs in real-time, run:"
echo "   ssh root@srv1151343.hstgr.io 'cd /opt/ArtinSmartRealty && docker-compose logs -f backend'"

ENDSSH

echo ""
echo "🎉 Done! Backend restarted with latest code."
