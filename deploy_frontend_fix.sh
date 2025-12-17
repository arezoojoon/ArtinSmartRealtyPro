#!/bin/bash

echo "🔧 Deploying Frontend Fix for smart-upload.html"
echo "================================================"

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Rebuild frontend with no cache
echo "🏗️ Rebuilding frontend container..."
docker-compose build --no-cache frontend

# Restart frontend
echo "🔄 Restarting frontend..."
docker-compose up -d frontend

# Wait for container to be healthy
echo "⏳ Waiting for frontend to be healthy..."
sleep 5

# Check if file exists in container
echo "✅ Checking if smart-upload.html is accessible..."
docker-compose exec frontend ls -la /usr/share/nginx/html/ | grep smart-upload

# Test web access
echo "🌐 Testing web access..."
curl -I http://localhost/smart-upload.html

echo ""
echo "🎉 Frontend deployment complete!"
echo "📱 Access at: https://realty.artinsmartagent.com/smart-upload.html"
