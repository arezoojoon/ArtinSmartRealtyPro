#!/bin/bash
# URGENT FIXES for Production Issues
# Run on server: bash FIX_PRODUCTION_ISSUES.sh

echo "=== ARTINSMARTREALTY - URGENT PRODUCTION FIXES ==="
echo "Found Issues:"
echo "1. Database name mismatch (artinrealty vs artinrealty_db)"
echo "2. Router unhealthy status"
echo "3. Ghost Protocol SQLAlchemy .astext error"
echo ""

cd /opt/ArtinSmartRealty

# === FIX 1: Verify Database Name ===
echo "=== FIX 1: Checking Database Name ==="
docker-compose exec -T db psql -U postgres -c "\l" | grep artinrealty
echo ""

# Get actual database name
DB_NAME=$(docker-compose exec -T db psql -U postgres -c "\l" | grep artinrealty | awk '{print $1}' | head -1)
echo "Found database: $DB_NAME"
echo ""

if [ "$DB_NAME" == "artinrealty" ]; then
    echo "✅ Database name is correct: artinrealty"
    echo "Checking tables..."
    docker-compose exec -T db psql -U postgres -d artinrealty -c "SELECT COUNT(*) as tenant_count FROM tenants;" 2>/dev/null
    docker-compose exec -T db psql -U postgres -d artinrealty -c "SELECT COUNT(*) as lead_count FROM leads;" 2>/dev/null
else
    echo "❌ Database name issue detected!"
fi
echo ""

# === FIX 2: Check Router Logs ===
echo "=== FIX 2: Router Health Check ==="
echo "Checking router logs for errors..."
docker-compose logs --tail=50 router | grep -i "error\|exception\|failed"
echo ""
echo "Testing router health endpoint..."
curl -s http://localhost:8001/health || echo "❌ Router health check failed"
echo ""

# === FIX 3: Ghost Protocol Error ===
echo "=== FIX 3: Ghost Protocol Error ==="
echo "Checking backend logs for Ghost Protocol errors..."
docker-compose logs --tail=100 backend | grep "Ghost Protocol"
echo ""

# === Summary ===
echo "=== SERVICE STATUS ==="
docker-compose ps
echo ""

echo "=== NEXT STEPS ==="
echo "1. If database is 'artinrealty' - NO CHANGES NEEDED (commands used wrong name)"
echo "2. If router fails - check: docker-compose logs router"
echo "3. Ghost Protocol error - needs code fix (SQLAlchemy .astext → .as_string())"
echo ""
echo "Run verification again:"
echo "  docker-compose exec -T db psql -U postgres -d artinrealty -c 'SELECT COUNT(*) FROM tenants;'"
echo "  docker-compose exec -T db psql -U postgres -d artinrealty -c 'SELECT COUNT(*) FROM leads;'"
