#!/bin/bash
# Check Deployment Status and Force Rebuild if Needed

cd /opt/ArtinSmartRealty

echo "📋 Step 1: Check current Git status..."
git log --oneline -5
echo ""
echo "Latest commit should be: 95ff3b6 (subscription fix)"
echo ""

echo "📋 Step 2: Check if admin.py has the fix..."
grep -A 3 "class UpdateSubscriptionRequest" backend/api/admin.py
echo ""

echo "📋 Step 3: Check running containers..."
docker-compose ps
echo ""

echo "📋 Step 4: Check backend container creation time..."
docker inspect artinrealty-backend | grep -E "(Created|Image)"
echo ""

echo "📋 Step 5: Force complete rebuild..."
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d

echo ""
echo "⏳ Waiting for backend to start..."
sleep 10

echo ""
echo "📋 Step 6: Verify backend is running with new code..."
docker-compose logs --tail=30 backend | grep -E "(Starting|Uvicorn|Application startup)"

echo ""
echo "✅ Check complete. Test subscription update now."
