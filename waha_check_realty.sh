#!/bin/bash

# Waha Status Check Script for Realty Service
# Port: 3002 (dedicated for Realty)

echo "🔍 Checking Waha status for Realty Service..."
echo "=============================================="

# Check if container is running
if ! docker-compose ps waha | grep -q "Up"; then
    echo "❌ Waha container is not running. Starting it..."
    docker-compose up -d waha
    sleep 5
fi

# Extract API key from logs
API_KEY=$(docker-compose logs waha | grep "WAHA_API_KEY=" | tail -1 | sed 's/.*WAHA_API_KEY=\(.*\)/\1/')

if [ -z "$API_KEY" ]; then
    echo "⚠️  No API key found in logs. Waha might still be starting..."
    echo "Run this script again in 30 seconds."
    exit 1
fi

echo "✅ API Key found: $API_KEY"
echo ""

# Check session status
echo "📱 Checking session status..."
SESSION_STATUS=$(curl -s -H "X-Api-Key: $API_KEY" http://localhost:3002/api/sessions/default | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SESSION_STATUS" ]; then
    echo "⚠️  Session doesn't exist. Creating it..."
    curl -X POST http://localhost:3002/api/sessions/default/start \
      -H "X-Api-Key: $API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "config": {
          "webhooks": [{
            "url": "http://backend:8000/api/webhook/waha",
            "events": ["message.any"]
          }]
        }
      }'
    echo ""
    SESSION_STATUS="STARTING"
fi

echo "📊 Session Status: $SESSION_STATUS"
echo ""

# Display QR code URL if not working
if [ "$SESSION_STATUS" != "WORKING" ]; then
    echo "📲 Scan QR Code to connect WhatsApp:"
    echo "🔗 http://72.60.196.192:3002/api/sessions/default/auth/qr?api_key=$API_KEY"
    echo ""
    echo "Or check QR in logs:"
    echo "docker-compose logs waha --tail=50"
else
    echo "✅ WhatsApp is connected and ready!"
    # Show phone number
    PHONE=$(curl -s -H "X-Api-Key: $API_KEY" http://localhost:3002/api/sessions/default | grep -o '"id":"[^"]*@c.us"' | cut -d'"' -f4 | sed 's/@c.us//')
    echo "📞 Connected Phone: $PHONE"
fi

echo ""
echo "💾 Save this API key to .env file:"
echo "WAHA_API_KEY=$API_KEY"
echo ""
echo "🔧 Useful Commands:"
echo "  - Check logs: docker-compose logs -f waha"
echo "  - Restart session: curl -X POST -H 'X-Api-Key: $API_KEY' http://localhost:3002/api/sessions/default/restart"
echo "  - Check webhook: curl -H 'X-Api-Key: $API_KEY' http://localhost:3002/api/sessions/default"
