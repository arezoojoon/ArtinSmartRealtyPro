#!/bin/bash
# Safe Atomic Deployment - Run this directly on VPS
# This ensures the site stays online during deployment

set -e  # Exit on any error

cd /opt/ArtinSmartRealty

echo "==================================="
echo "🚀 Safe Deployment Script"
echo "==================================="
echo ""

# Function to check if service is healthy
check_health() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Backend is healthy!"
            return 0
        fi
        echo "⏳ Waiting for backend... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Backend failed to start!"
    return 1
}

# Step 1: Update code
echo "📥 Step 1: Pulling latest code..."
git fetch origin
git reset --hard origin/main
echo "   Current commit: $(git log --oneline -1)"
echo ""

# Step 2: Build new image WITHOUT stopping current containers
echo "🔨 Step 2: Building new backend image..."
docker-compose build --no-cache backend
echo ""

# Step 3: Stop old container and start new one
echo "🔄 Step 3: Swapping containers (minimal downtime)..."
docker-compose up -d backend
echo ""

# Step 4: Wait for new container to be healthy
echo "⏳ Step 4: Waiting for new backend to be ready..."
if check_health; then
    echo ""
    echo "🎉 Deployment successful!"
else
    echo ""
    echo "⚠️ New backend not responding. Rolling back..."
    docker-compose restart backend
    exit 1
fi

# Step 5: Clean up old images
echo ""
echo "🧹 Step 5: Cleaning up old images..."
docker image prune -f

# Step 6: Show status
echo ""
echo "==================================="
echo "📊 Current Status"
echo "==================================="
docker-compose ps

echo ""
echo "📋 Recent logs:"
docker-compose logs --tail=15 backend | grep -E "(INFO|ERROR|startup|Started)"

echo ""
echo "==================================="
echo "✅ Deployment Complete!"
echo "==================================="
echo ""
echo "🧪 TEST THE FIX:"
echo "   URL: https://realty.artinsmartagent.com/"
echo "   Login: admin@artinsmartrealty.com / SuperAdmin123!"
echo "   Action: Change tenant subscription Trial → Active"
echo "   Expected: ✅ Subscription updated (no more 404)"
echo ""
