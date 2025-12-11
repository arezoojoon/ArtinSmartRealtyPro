#!/bin/bash

# Deploy Waha for Realty Service
# Run this on the production server: root@72.60.196.192

set -e

echo "🚀 Deploying Waha for Realty Service..."
echo "========================================"

cd /opt/ArtinSmartRealty

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Rebuild Waha container with new port (3002)
echo "🔨 Rebuilding Waha container..."
docker-compose up -d waha

echo "⏳ Waiting for Waha to start (30 seconds)..."
sleep 30

# Extract API key
echo "🔑 Extracting API key from logs..."
API_KEY=$(docker-compose logs waha | grep "WAHA_API_KEY=" | tail -1 | sed 's/.*WAHA_API_KEY=\(.*\)/\1/')

if [ -z "$API_KEY" ]; then
    echo "❌ Failed to extract API key. Check logs:"
    docker-compose logs waha --tail=20
    exit 1
fi

echo "✅ API Key: $API_KEY"

# Save to .env
if ! grep -q "WAHA_API_KEY=" .env; then
    echo "WAHA_API_KEY=$API_KEY" >> .env
    echo "💾 API key saved to .env"
else
    sed -i "s/^WAHA_API_KEY=.*/WAHA_API_KEY=$API_KEY/" .env
    echo "💾 API key updated in .env"
fi

# Restart backend to pick up new API key
echo "🔄 Restarting backend with new API key..."
docker-compose restart backend

sleep 5

# Check session status
echo "📱 Checking session status..."
SESSION_STATUS=$(curl -s -H "X-Api-Key: $API_KEY" http://localhost:3002/api/sessions/default 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SESSION_STATUS" ]; then
    echo "⚠️  Session doesn't exist. Creating and starting it..."
    
    # Create and start session with webhook
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
      }' 2>/dev/null
    
    echo ""
    SESSION_STATUS="STARTING"
fi

echo "📊 Current Status: $SESSION_STATUS"
echo ""

# Display next steps based on status
if [ "$SESSION_STATUS" = "WORKING" ]; then
    PHONE=$(curl -s -H "X-Api-Key: $API_KEY" http://localhost:3002/api/sessions/default | grep -o '"id":"[^"]*@c.us"' | cut -d'"' -f4 | sed 's/@c.us//')
    echo "✅ WhatsApp Connected!"
    echo "📞 Phone Number: $PHONE"
    echo ""
    echo "🔗 Test Deep Links:"
    echo "  https://wa.me/$PHONE?text=start_realty"
else
    echo "📲 Next Step: Scan QR Code"
    echo "🔗 Open in browser:"
    echo "   http://72.60.196.192:3002/api/sessions/default/auth/qr?api_key=$API_KEY"
    echo ""
    echo "Or view QR in terminal:"
    echo "   docker-compose logs waha --tail=50 | grep '█'"
fi

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "🔧 Monitoring Commands:"
echo "  docker-compose logs -f waha              # Watch Waha logs"
echo "  docker-compose logs -f backend           # Watch backend logs"
echo "  curl -H 'X-Api-Key: $API_KEY' http://localhost:3002/api/sessions/default  # Check status"
