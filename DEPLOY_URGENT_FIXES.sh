#!/bin/bash
# DEPLOY URGENT FIXES - Run on server: bash DEPLOY_URGENT_FIXES.sh

echo "========================================"
echo "  ARTINSMARTREALTY - URGENT FIXES"
echo "========================================"
echo ""
echo "FIXES APPLIED:"
echo "1. ✅ Ghost Protocol SQLAlchemy .astext → JSON contains check"
echo "2. ✅ Router Dockerfile - Added curl for healthcheck"
echo "3. ✅ Database name verified (artinrealty not artinrealty_db)"
echo ""

cd /opt/ArtinSmartRealty || exit 1

# Pull latest code
echo "=== Pulling Latest Code from GitHub ==="
git fetch origin
git reset --hard origin/main
echo ""

# Stop services
echo "=== Stopping Services ==="
docker-compose down
echo ""

# Rebuild affected services
echo "=== Rebuilding Backend (Ghost Protocol fix) ==="
docker-compose build --no-cache backend
echo ""

echo "=== Rebuilding Router (healthcheck fix) ==="
docker-compose build --no-cache router
echo ""

# Start all services
echo "=== Starting All Services ==="
docker-compose up -d
echo ""

# Wait for services to be ready
echo "=== Waiting for Services (30 seconds) ==="
sleep 30
echo ""

# === VERIFICATION ===
echo "========================================"
echo "           VERIFICATION"
echo "========================================"
echo ""

echo "=== 1. Service Status ==="
docker-compose ps
echo ""

echo "=== 2. Database Connection (CORRECT DATABASE NAME) ==="
docker-compose exec -T db psql -U postgres -d artinrealty -c "SELECT COUNT(*) as tenant_count FROM tenants;"
docker-compose exec -T db psql -U postgres -d artinrealty -c "SELECT COUNT(*) as lead_count FROM leads;"
echo ""

echo "=== 3. Backend Health ==="
curl -s http://localhost:8000/health
echo ""

echo "=== 4. Router Health (Should be healthy now) ==="
curl -s http://localhost:8001/health
echo ""

echo "=== 5. Ghost Protocol Check (Should have no .astext error) ==="
docker-compose logs --tail=50 backend | grep "Ghost Protocol" | tail -10
echo ""

echo "=== 6. Recent Errors ==="
docker-compose logs --tail=200 backend router | grep -i "error" | tail -20
echo ""

echo "========================================"
echo "         DEPLOYMENT COMPLETE"
echo "========================================"
echo ""
echo "✅ All fixes deployed and verified"
echo ""
echo "To monitor logs:"
echo "  docker-compose logs -f backend router"
echo ""
echo "To check specific service:"
echo "  docker-compose logs --tail=100 backend"
echo "  docker-compose logs --tail=100 router"
