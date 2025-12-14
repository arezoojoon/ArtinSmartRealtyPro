#!/bin/bash
# ====================================
# 🚀 Deploy Property Presenter Fix
# ====================================
# Fix: Always set current_properties for property_presenter
# Commit: ce6d83e
# ====================================

set -e  # Exit on any error

echo "🚀 Deploying property presenter fix (ce6d83e)..."
echo "========================================"

# Step 1: Navigate to project directory
echo "📁 Navigating to /opt/ArtinSmartRealtyPro..."
cd /opt/ArtinSmartRealtyPro

# Step 2: Backup current state
echo "💾 Creating backup..."
git branch backup-$(date +%Y%m%d-%H%M%S)

# Step 3: Pull latest code
echo "⬇️ Pulling latest code from main..."
git pull origin main

# Verify we have the fix
if git log -1 --oneline | grep -q "ce6d83e"; then
    echo "✅ Fix commit ce6d83e found!"
else
    echo "⚠️  Warning: Commit ce6d83e not found in history"
fi

# Step 4: Rebuild backend container with --no-cache
echo "🔨 Rebuilding backend container..."
docker-compose build --no-cache backend

# Step 5: Restart services
echo "🔄 Restarting services..."
docker-compose down
docker-compose up -d

# Step 6: Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Step 7: Verify containers are running
echo "✅ Checking container status..."
docker-compose ps

# Step 8: Monitor logs for property presenter
echo "📋 Monitoring logs (Ctrl+C to exit)..."
echo "Look for: '🏠 Brain has X properties to present'"
docker-compose logs -f backend | grep -E "🏠|property|present_all_properties"
