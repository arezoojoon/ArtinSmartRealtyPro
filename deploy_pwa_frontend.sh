#!/bin/bash
# PWA Frontend Deployment Script
# Deploy new PWA features to production

echo "🚀 Deploying PWA Frontend to Production"
echo "========================================"

# Pull latest code from GitHub
echo "📥 Pulling latest code from GitHub..."
git pull origin main

# Rebuild frontend container with PWA changes (no cache to ensure fresh build)
echo "🏗️ Rebuilding frontend container with PWA features..."
docker-compose build --no-cache frontend

# Restart frontend container
echo "🔄 Restarting frontend container..."
docker-compose up -d frontend

# Wait for container to be healthy
echo "⏳ Waiting for frontend to be ready (10 seconds)..."
sleep 10

# Check container status
echo "📊 Container Status:"
docker-compose ps frontend

# Test web access
echo ""
echo "🌐 Testing web access..."
curl -I http://localhost:3000/ || true

# Check if PWA manifest is accessible
echo ""
echo "📱 Testing PWA manifest..."
curl -I http://localhost:3000/manifest.json || true

# Show recent logs
echo ""
echo "📝 Recent Frontend Logs:"
docker-compose logs --tail=30 frontend

echo ""
echo "✅ PWA Frontend Deployment Complete!"
echo ""
echo "📋 Next Steps:"
echo "  1. Generate PWA icons (see PWA_ICON_GUIDE.md)"
echo "  2. Test on mobile: https://realty.artinsmartagent.com"
echo "  3. Resize browser < 1024px to see mobile bottom nav"
echo "  4. Install prompt appears after 3 seconds"
echo ""
echo "📱 Test installation:"
echo "  - iOS: Open in Safari → Share → Add to Home Screen"
echo "  - Android: Open in Chrome → Install button"
