#!/bin/bash
# Production Deployment Script for ArtinSmartRealty
# Server: 72.62.93.119
# Date: 2024-12-20

set -e  # Exit on error

echo "🚀 Starting Production Deployment..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Navigate to project directory
echo -e "${BLUE}📂 Navigating to project directory...${NC}"
cd /root/ArtinSmartRealty || cd ~/ArtinSmartRealty || cd /var/www/ArtinSmartRealty || {
    echo -e "${RED}❌ Project directory not found${NC}"
    exit 1
}

# Step 2: Pull latest code
echo -e "${BLUE}📥 Pulling latest code from GitHub...${NC}"
git fetch origin
git pull origin main

# Step 3: Backup current containers (if running)
echo -e "${BLUE}💾 Creating backup of current state...${NC}"
docker-compose ps > deployment_backup_$(date +%Y%m%d_%H%M%S).txt || true

# Step 4: Stop services gracefully
echo -e "${BLUE}⏸️  Stopping current services...${NC}"
docker-compose down || true

# Step 5: Rebuild with new dependencies
echo -e "${BLUE}🔨 Building new Docker images...${NC}"
docker-compose build --no-cache backend router || {
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
}

# Step 6: Start database and Redis first
echo -e "${BLUE}🗄️  Starting database and Redis...${NC}"
docker-compose up -d db redis
sleep 10  # Wait for database to be ready

# Step 7: Run migrations
echo -e "${BLUE}📊 Running database migrations...${NC}"
docker-compose run --rm backend alembic upgrade head || {
    echo -e "${RED}⚠️  Migrations failed - continuing anyway${NC}"
}

# Step 8: Start all services
echo -e "${BLUE}🚀 Starting all services...${NC}"
docker-compose up -d

# Step 9: Wait for services to be healthy
echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
sleep 15

# Step 10: Health checks
echo -e "${BLUE}🏥 Running health checks...${NC}"

# Check backend
if curl -f http://localhost:8000/health &>/dev/null; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
fi

# Check router
if curl -f http://localhost:8001/health &>/dev/null; then
    echo -e "${GREEN}✅ Router is healthy${NC}"
else
    echo -e "${RED}❌ Router health check failed${NC}"
fi

# Check frontend
if curl -f http://localhost:3000 &>/dev/null; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${RED}❌ Frontend not accessible${NC}"
fi

# Step 11: Show container status
echo -e "${BLUE}📊 Container Status:${NC}"
docker-compose ps

# Step 12: Show recent logs
echo -e "${BLUE}📝 Recent Logs (last 50 lines):${NC}"
docker-compose logs --tail=50 backend router

echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo "📊 Monitor logs with: docker-compose logs -f"
echo "🔍 Check health: curl http://localhost:8000/health"
echo "📈 Router stats: curl http://localhost:8001/router/stats"
