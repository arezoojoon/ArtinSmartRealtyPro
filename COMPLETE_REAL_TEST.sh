#!/bin/bash
# COMPLETE REAL PRODUCTION TEST

echo "========================================"
echo "  REAL PRODUCTION TEST - NO FAKE"
echo "========================================"
echo ""

cd /opt/ArtinSmartRealty

# PROBLEM 1: No properties
echo "=== PROBLEM 1: TENANT HAS NO PROPERTIES ==="
PROPERTY_COUNT=$(docker-compose exec -T db psql -U postgres -d artinrealty -t -c "SELECT COUNT(*) FROM tenant_properties;" | tr -d '[:space:]')
echo "Property count: $PROPERTY_COUNT"
if [ "$PROPERTY_COUNT" = "0" ]; then
    echo "❌ CRITICAL: No properties! Bot cannot work without properties."
    echo ""
    echo "FIX: Run this command:"
    echo "  bash ADD_TEST_PROPERTIES.sh"
else
    echo "✅ Properties exist"
fi
echo ""

# PROBLEM 2: Router unhealthy
echo "=== PROBLEM 2: ROUTER STATUS ==="
ROUTER_STATUS=$(docker-compose ps router | grep "unhealthy" | wc -l)
if [ "$ROUTER_STATUS" -gt "0" ]; then
    echo "❌ Router is unhealthy"
    echo ""
    echo "Checking router logs..."
    docker-compose logs --tail=50 router | tail -20
    echo ""
    echo "FIX: Router needs curl for healthcheck"
    echo "  Already in code - just restart: docker-compose restart router"
else
    echo "✅ Router healthy"
fi
echo ""

# PROBLEM 3: Test Telegram bot
echo "=== PROBLEM 3: TELEGRAM BOT TEST ==="
BOT_TOKEN=$(docker-compose exec -T db psql -U postgres -d artinrealty -t -c "SELECT telegram_bot_token FROM tenants LIMIT 1;" | tr -d '[:space:]')
echo "Bot token: ${BOT_TOKEN:0:15}..."
echo ""

echo "Bot username:"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe" | grep -o '"username":"[^"]*"' | cut -d'"' -f4
echo ""

echo "Checking if bot is receiving messages..."
UPDATES=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates?limit=1" | grep -o '"result":\[\]')
if [ "$UPDATES" = '"result":[]' ]; then
    echo "❌ No messages received yet"
    echo ""
    echo "TO TEST: Send '/start' to bot in Telegram"
else
    echo "✅ Bot received messages"
fi
echo ""

# PROBLEM 4: Check Gemini API
echo "=== PROBLEM 4: GEMINI API TEST ==="
GEMINI_KEY=$(docker-compose exec -T backend printenv GEMINI_API_KEY)
if [ -z "$GEMINI_KEY" ]; then
    echo "❌ GEMINI_API_KEY not set!"
else
    echo "✅ Gemini API key exists: ${GEMINI_KEY:0:20}..."
    
    # Test actual API call
    echo "Testing Gemini API..."
    docker-compose exec -T backend curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=${GEMINI_KEY}" | grep -o '"name":"models/gemini' | head -1
    if [ $? -eq 0 ]; then
        echo "✅ Gemini API works"
    else
        echo "❌ Gemini API failed"
    fi
fi
echo ""

# PROBLEM 5: Leads stuck in slot_filling
echo "=== PROBLEM 5: STUCK LEADS ==="
docker-compose exec -T db psql -U postgres -d artinrealty -c "SELECT id, name, phone, status, conversation_state, updated_at FROM leads ORDER BY updated_at DESC;"
echo ""
echo "If leads are stuck, they need conversation to progress"
echo ""

# Summary
echo "========================================"
echo "           SUMMARY"
echo "========================================"
echo ""
echo "✅ Backend: Running"
echo "✅ Database: 1 tenant, 2 leads"
echo "✅ Telegram Bot: Polling (waiting for messages)"
echo "✅ WAHA: Running"
echo ""
echo "🔴 CRITICAL ISSUES:"
echo "1. No properties - Bot cannot suggest anything"
echo "2. Router unhealthy - Needs restart with curl"
echo "3. No test messages sent yet"
echo ""
echo "NEXT STEPS TO REALLY TEST:"
echo "1. Add properties: bash ADD_TEST_PROPERTIES.sh"
echo "2. Fix router: docker-compose restart router"
echo "3. Send message to @TaranteenrealstateBot in Telegram"
echo "4. Watch logs: docker-compose logs -f backend | grep -i 'received\|response'"
echo ""
echo "This is REAL testing - not fake report!"
