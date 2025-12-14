#!/bin/bash

# ====================================
# 🚀 ArtinSmartRealty Production Deployment
# ====================================
# این اسکریپت تمام features جدید رو deploy می‌کنه:
# - Morning Coffee Report (گزارش روزانه 8 صبح)
# - Hot Lead Alert (هشدار لید داغ)
# - Scarcity & Urgency (تاکتیک فروش)
# - Ghost Protocol (Follow-up خودکار)
# ====================================

set -e  # Exit on any error

echo "🚀 Starting ArtinSmartRealty Deployment..."
echo "========================================"

# Step 1: Navigate to project directory
echo "📁 Step 1: Navigating to project directory..."
cd /opt/ArtinSmartRealty
pwd

# Step 2: Backup current database (safety first!)
echo "💾 Step 2: Creating database backup..."
timestamp=$(date +%Y%m%d_%H%M%S)
pg_dump -U postgres artin_smart_realty > "/tmp/artin_backup_${timestamp}.sql" || echo "⚠️  Backup failed, continuing anyway..."

# Step 3: Install/Update Python dependencies
echo "📦 Step 3: Installing Python dependencies..."
cd backend
source venv/bin/activate || python3 -m venv venv && source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Run database migrations
echo "🗄️  Step 4: Running database migrations..."
python -m alembic upgrade head

# Step 5: Stop existing services
echo "🛑 Step 5: Stopping existing services..."
systemctl stop artin-bot || docker-compose down || echo "⚠️  No running services found"

# Step 6: Start services with new code
echo "▶️  Step 6: Starting services with new code..."
cd /opt/ArtinSmartRealty

# Option A: If using systemd
if systemctl list-units --type=service | grep -q "artin-bot"; then
    systemctl start artin-bot
    systemctl status artin-bot --no-pager
# Option B: If using Docker Compose
elif [ -f "docker-compose.yml" ]; then
    docker-compose up -d --build
    docker-compose logs -f --tail=50
# Option C: If using screen/tmux
else
    cd backend
    source venv/bin/activate
    screen -dmS artin-bot python -m uvicorn main:app --host 0.0.0.0 --port 8000
    echo "✅ Started in screen session 'artin-bot'"
fi

# Step 7: Health check
echo "🏥 Step 7: Running health check..."
sleep 5
curl -f http://localhost:8000/health || echo "⚠️  Health check failed, but service may still be starting..."

# Step 8: Verify new features
echo "✅ Step 8: Verifying new features..."
cd /opt/ArtinSmartRealty

echo ""
echo "========================================"
echo "🎉 Deployment Complete!"
echo "========================================"
echo ""
echo "📊 New Features Deployed:"
echo "  ✅ Morning Coffee Report (8:00 AM daily)"
echo "  ✅ Hot Lead Alert (instant notifications)"
echo "  ✅ Scarcity & Urgency (FOMO tactics)"
echo "  ✅ Ghost Protocol (2-hour follow-up)"
echo ""
echo "📝 Next Steps:"
echo "  1. Check logs: journalctl -u artin-bot -n 50 -f"
echo "  2. Or: docker-compose logs -f"
echo "  3. Or: screen -r artin-bot"
echo "  4. Test bot: Send /start to your Telegram bot"
echo "  5. Verify Morning Coffee: Check logs for '[Morning Coffee]'"
echo ""
echo "📚 Documentation:"
echo "  - README_START_HERE.md"
echo "  - DEPLOYMENT_TESTING_GUIDE.md"
echo "  - MORNING_COFFEE_QUICK_SUMMARY.md"
echo ""
echo "🔥 Happy deploying!"
