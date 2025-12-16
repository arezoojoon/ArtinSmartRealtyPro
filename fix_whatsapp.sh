#!/bin/bash
# WhatsApp/WAHA Troubleshooting & Fix Script
# Purpose: Diagnose and fix common WhatsApp bot issues

echo "======================================"
echo "WhatsApp Bot Diagnostic & Fix"
echo "======================================"
echo ""

cd /opt/ArtinSmartRealtyPro/ArtinSmartRealty

# Check 1: WAHA Container Status
echo "[1/6] Checking WAHA container status..."
if docker ps | grep -q artinrealty-waha; then
    echo "✅ WAHA container is running"
    WAHA_STATUS="running"
else
    echo "❌ WAHA container is NOT running"
    WAHA_STATUS="stopped"
    echo "   Attempting to start..."
    docker-compose up -d waha
    sleep 5
fi

# Check 2: WAHA Health Endpoint
echo ""
echo "[2/6] Testing WAHA API health..."
WAHA_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health 2>/dev/null || echo "000")
if [ "$WAHA_RESPONSE" = "200" ]; then
    echo "✅ WAHA API is responding (HTTP 200)"
else
    echo "❌ WAHA API not responding (HTTP $WAHA_RESPONSE)"
    echo "   Check logs:"
    docker logs artinrealty-waha --tail 20
fi

# Check 3: WhatsApp Sessions
echo ""
echo "[3/6] Checking active WhatsApp sessions..."
SESSIONS=$(curl -s http://localhost:3000/api/sessions 2>/dev/null || echo "[]")
echo "Active sessions: $SESSIONS"

if [ "$SESSIONS" = "[]" ]; then
    echo "⚠️  No WhatsApp sessions found"
    echo "   Tenants need to scan QR code to connect WhatsApp"
fi

# Check 4: Database WhatsApp Configuration
echo ""
echo "[4/6] Checking database WhatsApp settings..."
docker exec artinrealty-db psql -U postgres -d artinrealty -c "
SELECT 
    id, 
    name, 
    whatsapp_phone_id,
    CASE WHEN whatsapp_access_token IS NOT NULL THEN 'Set' ELSE 'Not Set' END as token_status
FROM tenants 
WHERE whatsapp_phone_id IS NOT NULL OR whatsapp_access_token IS NOT NULL;
" 2>/dev/null || echo "❌ Could not query database"

# Check 5: WhatsApp Bot Code
echo ""
echo "[5/6] Checking WhatsApp bot initialization..."
if docker logs artinrealty-backend --tail 200 | grep -i "whatsapp.*initialized" > /dev/null; then
    echo "✅ WhatsApp bot initialized in backend"
else
    echo "⚠️  WhatsApp bot may not be initialized"
    echo "   Recent backend logs:"
    docker logs artinrealty-backend --tail 30 | grep -i whatsapp || echo "   No WhatsApp logs found"
fi

# Check 6: Network Connectivity
echo ""
echo "[6/6] Checking Docker network..."
NETWORK_EXISTS=$(docker network ls | grep artinrealty-network || echo "")
if [ -n "$NETWORK_EXISTS" ]; then
    echo "✅ Docker network exists"
    echo "   Containers on network:"
    docker network inspect artinrealty-network --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null
else
    echo "❌ Docker network missing - recreating..."
    docker-compose down
    docker-compose up -d
fi

echo ""
echo "======================================"
echo "COMMON WHATSAPP ISSUES & FIXES"
echo "======================================"
echo ""
echo "ISSUE 1: 'No WhatsApp sessions found'"
echo "FIX: Tenant needs to connect WhatsApp via dashboard:"
echo "   1. Login to tenant dashboard"
echo "   2. Go to Settings > WhatsApp Integration"
echo "   3. Click 'Connect WhatsApp'"
echo "   4. Scan QR code with WhatsApp mobile app"
echo ""
echo "ISSUE 2: 'Messages not sending'"
echo "FIX: Check WAHA logs for errors:"
echo "   docker logs artinrealty-waha -f"
echo ""
echo "ISSUE 3: 'WAHA container keeps restarting'"
echo "FIX: Chromium dependency issue - rebuild:"
echo "   docker-compose down"
echo "   docker-compose pull waha"
echo "   docker-compose up -d"
echo ""
echo "ISSUE 4: 'WhatsApp disconnected after working'"
echo "FIX: Re-scan QR code (session expired)"
echo ""
echo "ISSUE 5: 'Backend can't reach WAHA'"
echo "FIX: Check .env has correct WAHA_URL:"
echo "   WAHA_API_URL=http://waha:3000"
echo "   (Use service name 'waha', not 'localhost')"
echo ""
echo "======================================"
echo "MANUAL TESTING"
echo "======================================"
echo ""
echo "Test WAHA directly:"
echo "  curl http://localhost:3000/api/sessions"
echo ""
echo "Check backend can reach WAHA:"
echo "  docker exec artinrealty-backend curl http://waha:3000/health"
echo ""
echo "======================================"
