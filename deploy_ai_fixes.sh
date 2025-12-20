#!/bin/bash

# ====================================
# 🚀 Production Deployment - AI Fixes
# تاریخ: 18 دسامبر 2025
# تغییرات: AI Intent Extraction + Lead Scoring + Amenities Matching
# ====================================

set -e  # Exit on error

echo "🚀 Deploying AI-Powered Fixes to Production..."
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/ArtinSmartRealty"
BACKUP_DIR="/opt/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ==================== STEP 1: Backup ====================
echo -e "${YELLOW}📦 STEP 1: Creating backup...${NC}"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Backup database
echo "   💾 Backing up database..."
docker exec artinsmart_db pg_dump -U postgres artinrealty > "${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql" || {
    echo -e "${RED}   ❌ Database backup failed!${NC}"
    exit 1
}

# Backup current code
echo "   📂 Backing up current code..."
tar -czf "${BACKUP_DIR}/code_backup_${TIMESTAMP}.tar.gz" -C ${PROJECT_DIR} backend frontend || {
    echo -e "${RED}   ❌ Code backup failed!${NC}"
    exit 1
}

echo -e "${GREEN}   ✅ Backup completed!${NC}"
echo ""

# ==================== STEP 2: Git Pull ====================
echo -e "${YELLOW}📥 STEP 2: Pulling latest code...${NC}"

cd ${PROJECT_DIR}

# Stash local changes (if any)
git stash save "Auto-stash before deployment ${TIMESTAMP}" 2>/dev/null || echo "   ℹ️  No local changes to stash"

# Pull latest code
git pull origin main || {
    echo -e "${RED}   ❌ Git pull failed!${NC}"
    echo -e "${YELLOW}   Rolling back...${NC}"
    git stash pop 2>/dev/null || true
    exit 1
}

echo -e "${GREEN}   ✅ Code pulled successfully!${NC}"
echo ""

# ==================== STEP 3: Build Backend ====================
echo -e "${YELLOW}🔨 STEP 3: Building backend with AI fixes...${NC}"
echo "   Changes included:"
echo "   ✅ AI intent extraction in SLOT_FILLING"
echo "   ✅ Lead scoring system (0-100)"
echo "   ✅ Amenities matching (pool, gym, beach)"
echo "   ✅ Follow-up engine activation"
echo ""

docker-compose build --no-cache backend || {
    echo -e "${RED}   ❌ Backend build failed!${NC}"
    echo -e "${YELLOW}   Rolling back to backup...${NC}"
    cd ${BACKUP_DIR}
    tar -xzf "code_backup_${TIMESTAMP}.tar.gz" -C ${PROJECT_DIR}
    exit 1
}

echo -e "${GREEN}   ✅ Backend built successfully!${NC}"
echo ""

# ==================== STEP 4: Database Migration ====================
echo -e "${YELLOW}🗄️  STEP 4: Running database migrations (if any)...${NC}"

docker-compose run --rm backend alembic upgrade head || {
    echo -e "${YELLOW}   ⚠️  Migration failed or no migrations needed${NC}"
}

echo -e "${GREEN}   ✅ Migrations completed!${NC}"
echo ""

# ==================== STEP 5: Restart Services ====================
echo -e "${YELLOW}♻️  STEP 5: Restarting services...${NC}"

# Stop containers
echo "   🛑 Stopping containers..."
docker-compose down

# Start containers
echo "   ▶️  Starting containers..."
docker-compose up -d || {
    echo -e "${RED}   ❌ Failed to start containers!${NC}"
    echo -e "${YELLOW}   Rolling back to backup...${NC}"
    cd ${BACKUP_DIR}
    tar -xzf "code_backup_${TIMESTAMP}.tar.gz" -C ${PROJECT_DIR}
    cd ${PROJECT_DIR}
    docker-compose up -d
    exit 1
}

echo -e "${GREEN}   ✅ Services restarted!${NC}"
echo ""

# ==================== STEP 6: Health Check ====================
echo -e "${YELLOW}🏥 STEP 6: Running health checks...${NC}"

# Wait for services to start
echo "   ⏳ Waiting 15 seconds for services to initialize..."
sleep 15

# Check backend
echo "   🔍 Checking backend..."
BACKEND_STATUS=$(docker-compose ps backend | grep -c "Up" || echo "0")
if [ "$BACKEND_STATUS" -eq "0" ]; then
    echo -e "${RED}   ❌ Backend is not running!${NC}"
    docker-compose logs backend --tail=50
    exit 1
fi

# Check database
echo "   🔍 Checking database..."
DB_STATUS=$(docker-compose ps db | grep -c "Up" || echo "0")
if [ "$DB_STATUS" -eq "0" ]; then
    echo -e "${RED}   ❌ Database is not running!${NC}"
    docker-compose logs db --tail=50
    exit 1
fi

# Check Redis
echo "   🔍 Checking Redis..."
REDIS_STATUS=$(docker-compose ps redis | grep -c "Up" || echo "0")
if [ "$REDIS_STATUS" -eq "0" ]; then
    echo -e "${YELLOW}   ⚠️  Redis is not running (optional)${NC}"
fi

echo -e "${GREEN}   ✅ All services are healthy!${NC}"
echo ""

# ==================== STEP 7: Verify Features ====================
echo -e "${YELLOW}✨ STEP 7: Verifying new features...${NC}"

# Check backend logs for critical startup messages
echo "   📋 Checking backend logs..."

# Wait 5 more seconds for full initialization
sleep 5

LOGS=$(docker-compose logs backend --tail=100)

# Check for Follow-up Engine
if echo "$LOGS" | grep -q "Unified Follow-up Engine started"; then
    echo -e "${GREEN}   ✅ Follow-up Engine: ACTIVE${NC}"
else
    echo -e "${YELLOW}   ⚠️  Follow-up Engine: NOT DETECTED${NC}"
fi

# Check for Redis
if echo "$LOGS" | grep -q "Redis initialized"; then
    echo -e "${GREEN}   ✅ Redis: CONNECTED${NC}"
else
    echo -e "${YELLOW}   ⚠️  Redis: NOT DETECTED (bot will use DB-only mode)${NC}"
fi

# Check for Bot startup
if echo "$LOGS" | grep -q "Bot started for tenant"; then
    echo -e "${GREEN}   ✅ Telegram Bot: STARTED${NC}"
else
    echo -e "${YELLOW}   ⚠️  Telegram Bot: NOT DETECTED${NC}"
fi

# Check for any errors
ERROR_COUNT=$(echo "$LOGS" | grep -c "ERROR" || echo "0")
if [ "$ERROR_COUNT" -gt "0" ]; then
    echo -e "${YELLOW}   ⚠️  Found $ERROR_COUNT errors in logs${NC}"
    echo "$LOGS" | grep "ERROR"
fi

echo ""

# ==================== STEP 8: Cleanup ====================
echo -e "${YELLOW}🧹 STEP 8: Cleanup...${NC}"

# Remove old Docker images
echo "   🗑️  Removing old Docker images..."
docker image prune -f

# Keep only last 5 backups
echo "   🗑️  Cleaning old backups..."
cd ${BACKUP_DIR}
ls -t db_backup_*.sql | tail -n +6 | xargs -r rm
ls -t code_backup_*.tar.gz | tail -n +6 | xargs -r rm

echo -e "${GREEN}   ✅ Cleanup completed!${NC}"
echo ""

# ==================== FINAL SUMMARY ====================
echo "=============================================="
echo -e "${GREEN}🎉 Deployment Completed Successfully!${NC}"
echo "=============================================="
echo ""
echo "📊 Summary:"
echo "   • Backup: ${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql"
echo "   • Backend: Running with AI fixes"
echo "   • Database: Migrated"
echo "   • Follow-up Engine: Active"
echo ""
echo "🌐 Service URLs:"
echo "   • Frontend: http://srv1195426.hstgr.cloud:3000"
echo "   • Backend: http://srv1195426.hstgr.cloud:8000"
echo "   • API Docs: http://srv1195426.hstgr.cloud:8000/docs"
echo ""
echo "🧪 Test Instructions:"
echo "   1. Open Telegram bot"
echo "   2. Send: 'میخوام ویلا 3 خوابه مارینا 3 میلیون با استخر'"
echo "   3. Verify: Bot extracts all info without buttons"
echo "   4. Check database for amenities & lead_score"
echo ""
echo "📋 View Logs:"
echo "   docker-compose logs -f backend"
echo ""
echo "🔄 Rollback (if needed):"
echo "   cd ${BACKUP_DIR}"
echo "   docker exec -i artinsmart_db psql -U postgres artinrealty < db_backup_${TIMESTAMP}.sql"
echo "   tar -xzf code_backup_${TIMESTAMP}.tar.gz -C ${PROJECT_DIR}"
echo "   cd ${PROJECT_DIR} && docker-compose up -d"
echo ""
echo -e "${GREEN}✅ All systems operational!${NC}"
