#!/bin/bash
# 🚀 Complete Deployment Fix - Calendar + Subscription
# این اسکریپت هر دو مشکل را حل می‌کند

set -e

echo "🔧 ArtinSmartRealty - Complete Fix Deployment"
echo "=============================================="
echo ""
echo "Fixes:"
echo "✅ 1. Calendar in bot: Click 'رزرو مشاوره' shows available times"
echo "✅ 2. Calendar navigation: Dashboard button opens full calendar"
echo "✅ 3. Subscription update 404 error fixed"
echo ""

cd /opt/ArtinSmartRealty

# Step 1: Pull latest code
echo "📥 Step 1: Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/main
echo "   ✓ Code updated"
echo ""

# Step 2: Verify fixes are present
echo "🔍 Step 2: Verifying fixes..."
echo "   Checking backend fix (UpdateSubscriptionRequest)..."
if grep -q "class UpdateSubscriptionRequest" backend/api/admin.py; then
    echo "   ✓ Backend subscription fix found"
else
    echo "   ✗ Backend fix missing - deployment may fail!"
fi

echo "   Checking frontend fix (onOpenFullCalendar)..."
if grep -q "onOpenFullCalendar" frontend/src/components/Dashboard.jsx; then
    echo "   ✓ Frontend calendar fix found"
else
    echo "   ✗ Frontend fix missing - deployment may fail!"
fi
echo ""

# Step 3: Stop services gracefully
echo "🛑 Step 3: Stopping services..."
docker-compose down
echo "   ✓ Services stopped"
echo ""

# Step 4: Clean Docker cache
echo "🧹 Step 4: Cleaning Docker cache..."
docker system prune -f
echo "   ✓ Cache cleaned"
echo ""

# Step 5: Build fresh images
echo "🔨 Step 5: Building fresh images (this may take 2-3 minutes)..."
docker-compose build --no-cache backend
docker-compose build --no-cache frontend
echo "   ✓ Images built"
echo ""

# Step 6: Start services
echo "🚀 Step 6: Starting services..."
docker-compose up -d
echo "   ✓ Services started"
echo ""

# Step 7: Wait for services to be ready
echo "⏳ Step 7: Waiting for services to initialize..."
sleep 15

# Step 8: Health checks
echo "🏥 Step 8: Running health checks..."
echo ""
echo "Backend status:"
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✓ Backend is healthy"
else
    echo "   ✗ Backend not responding"
fi

echo ""
echo "Container status:"
docker-compose ps
echo ""

echo "Recent backend logs:"
docker-compose logs --tail=20 backend | grep -E "(INFO|ERROR|startup|Uvicorn)" || echo "   No startup logs yet..."
echo ""

# Final status
echo "=============================================="
echo "✅ Deployment Complete!"
echo "=============================================="
echo ""
echo "🧪 TESTING INSTRUCTIONS:"
echo ""
echo "Test 1 - Calendar in Telegram/WhatsApp Bot:"
echo "   1. Send message to your bot on Telegram/WhatsApp"
echo "   2. When you see buttons, click: 📅 رزرو مشاوره"
echo "   3. Should show calendar with available time slots"
echo "   4. Select a time → Should confirm booking"
echo ""
echo "Test 2 - Calendar Navigation in Dashboard:"
echo "   1. Login: https://realty.artinsmartagent.com/"
echo "   2. در Dashboard Overview پایین صفحه"
echo "   3. کلیک روی: 🗓️ مدیریت تقویم"
echo "   4. باید به صفحه Calendar برود"
echo ""
echo "Test 3 - Subscription Update:"
echo "   1. Login as Super Admin:"
echo "      Email: admin@artinsmartrealty.com"
echo "      Password: SuperAdmin123!"
echo "   2. Go to SuperAdminDashboard"
echo "   3. Change Tenant subscription: Trial → Active"
echo "   4. Should see: ✅ Subscription updated (no 404 error)"
echo ""
echo "📋 View live logs:"
echo "   docker-compose logs -f backend"
echo ""
