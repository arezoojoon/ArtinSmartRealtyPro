#!/bin/bash
# REAL PRODUCTION TESTING - Find ACTUAL problems

echo "=== REAL TESTING - NO FAKE REPORTS ==="
echo ""

cd /opt/ArtinSmartRealty

# 1. Check REAL backend errors (last 500 lines)
echo "=== 1. BACKEND REAL ERRORS ==="
docker-compose logs --tail=500 backend | grep -i "error\|exception\|failed\|traceback" | head -50
echo ""

# 2. Check if Telegram bot is ACTUALLY running
echo "=== 2. TELEGRAM BOT STATUS ==="
docker-compose logs --tail=200 backend | grep -i "telegram.*start\|telegram.*running\|telegram.*init"
echo ""

# 3. Check Ghost Protocol CURRENT status
echo "=== 3. GHOST PROTOCOL CURRENT STATUS ==="
docker-compose logs --tail=100 backend | grep "Ghost Protocol" | tail -20
echo ""

# 4. Check Router REAL errors
echo "=== 4. ROUTER REAL ERRORS ==="
docker-compose logs --tail=300 router | grep -i "error\|exception\|failed" | head -30
echo ""

# 5. Check WhatsApp WAHA status
echo "=== 5. WAHA STATUS ==="
docker-compose logs --tail=100 waha | grep -i "error\|ready\|started" | tail -20
curl -s http://localhost:3001/api/health 2>/dev/null || echo "WAHA not responding"
echo ""

# 6. Check database for REAL tenant data
echo "=== 6. REAL TENANT DATA ==="
docker-compose exec -T db psql -U postgres -d artinrealty -c "SELECT id, email, company_name, telegram_bot_token IS NOT NULL as has_telegram FROM tenants;"
echo ""

# 7. Check if tenant has properties
echo "=== 7. TENANT PROPERTIES ==="
docker-compose exec -T db psql -U postgres -d artinrealty -c "SELECT COUNT(*) as property_count FROM tenant_properties;"
echo ""

# 8. Check REAL leads status
echo "=== 8. REAL LEADS DATA ==="
docker-compose exec -T db psql -U postgres -d artinrealty -c "SELECT id, name, phone, status, conversation_state, created_at FROM leads ORDER BY created_at DESC LIMIT 5;"
echo ""

# 9. Try to send TEST message to Telegram (if bot exists)
echo "=== 9. TELEGRAM BOT TEST ==="
BOT_TOKEN=$(docker-compose exec -T db psql -U postgres -d artinrealty -t -c "SELECT telegram_bot_token FROM tenants WHERE telegram_bot_token IS NOT NULL LIMIT 1;" | tr -d '[:space:]')
if [ ! -z "$BOT_TOKEN" ]; then
    echo "Bot token found: ${BOT_TOKEN:0:10}..."
    curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe" | head -20
else
    echo "No Telegram bot configured"
fi
echo ""

# 10. Check Redis sessions
echo "=== 10. REDIS SESSIONS ==="
docker-compose exec -T redis redis-cli KEYS "*" | head -20
echo ""

# 11. Check container resource usage
echo "=== 11. CONTAINER RESOURCES ==="
docker stats --no-stream artinrealty-backend artinrealty-router-v3
echo ""

# 12. Check if backend can reach external APIs
echo "=== 12. EXTERNAL API ACCESS ==="
docker-compose exec -T backend curl -s https://generativelanguage.googleapis.com/v1beta/models -o /dev/null -w "Gemini API: %{http_code}\n" 2>/dev/null || echo "Cannot reach Gemini API"
echo ""

echo "=== ANALYSIS COMPLETE ==="
echo "Check output above for REAL problems"
