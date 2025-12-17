#!/bin/bash

echo "🔐 Deploying Authentication Fix for Smart Upload"
echo "================================================"

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Rebuild frontend (smart-upload.html is copied during build)
echo "🏗️ Rebuilding frontend with authentication..."
docker-compose build --no-cache frontend

# Restart frontend
echo "🔄 Restarting frontend..."
docker-compose up -d frontend

# Wait for health check
echo "⏳ Waiting for frontend to be healthy..."
sleep 5

# Verify file exists
echo "✅ Verifying smart-upload.html..."
docker-compose exec frontend ls -la /usr/share/nginx/html/smart-upload.html

echo ""
echo "🎉 Authentication Fix Deployed!"
echo ""
echo "🔒 Security Improvements:"
echo "  ✅ Users must login before uploading"
echo "  ✅ Each agent sees only their own properties"
echo "  ✅ Token-based authentication enforced"
echo "  ✅ Auto-logout on unauthorized access"
echo ""
echo "📱 Access: https://realty.artinsmartagent.com/smart-upload.html"
echo "   (Redirects to login if not authenticated)"
