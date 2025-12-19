#!/bin/bash
# چک وضعیت Waha و راه‌اندازی مجدد

echo "🔍 بررسی وضعیت Waha..."

# چک container
echo ""
echo "📦 Container Status:"
docker-compose ps waha

# چک لاگ‌های اخیر
echo ""
echo "📋 Recent Logs (last 50 lines):"
docker-compose logs --tail=50 waha

# اگر container down بود، start کن
STATUS=$(docker-compose ps -q waha)
if [ -z "$STATUS" ]; then
    echo ""
    echo "⚠️  Waha container is down! Starting..."
    docker-compose up -d waha
    sleep 15
else
    RUNNING=$(docker inspect -f '{{.State.Running}}' $(docker-compose ps -q waha) 2>/dev/null)
    if [ "$RUNNING" != "true" ]; then
        echo ""
        echo "⚠️  Waha container exists but not running! Starting..."
        docker-compose start waha
        sleep 15
    fi
fi

# Extract API key
echo ""
echo "🔑 Extracting API Key..."
API_KEY=$(docker-compose logs waha | grep "WAHA_API_KEY=" | tail -1 | sed 's/.*WAHA_API_KEY=//' | tr -d '\r')

if [ -z "$API_KEY" ]; then
    echo "❌ Could not find API key in logs!"
    echo "Check logs manually:"
    echo "docker-compose logs waha | grep WAHA_API_KEY"
    exit 1
fi

echo "✅ API Key: $API_KEY"

# چک session
echo ""
echo "🔍 Checking existing sessions..."
curl -s -H "X-Api-Key: $API_KEY" http://localhost:3001/api/sessions 2>/dev/null || echo "Cannot connect to Waha API"

# Check if default session exists
SESSION_STATUS=$(curl -s -H "X-Api-Key: $API_KEY" http://localhost:3001/api/sessions/default 2>/dev/null)

if echo "$SESSION_STATUS" | grep -q "status"; then
    echo ""
    echo "✅ Default session exists:"
    echo "$SESSION_STATUS" | grep -o '"status":"[^"]*"'
else
    echo ""
    echo "⚠️  Default session doesn't exist. Creating..."
    curl -X POST http://localhost:3001/api/sessions/start \
      -H "Content-Type: application/json" \
      -H "X-Api-Key: $API_KEY" \
      -d '{"name":"default","config":{"webhooks":[{"url":"http://backend:8000/api/webhook/waha","events":["message"]}]}}'
    echo ""
    sleep 3
    
    # Check again
    SESSION_STATUS=$(curl -s -H "X-Api-Key: $API_KEY" http://localhost:3001/api/sessions/default 2>/dev/null)
    echo "Session status: $SESSION_STATUS"
fi

echo ""
echo "================================================"
echo "✅ Status Check Complete!"
echo "================================================"
echo ""
echo "📱 Get QR Code:"
echo "http://72.60.196.192:3001/api/sessions/default/auth/qr?api_key=$API_KEY"
echo ""
echo "🔑 Save this to .env:"
echo "WAHA_API_KEY=$API_KEY"
echo ""
echo "📊 Monitor:"
echo "docker-compose logs -f waha"
echo ""
