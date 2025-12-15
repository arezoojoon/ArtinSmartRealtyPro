#!/bin/bash

# WhatsApp Gateway Deployment Script
# Deploy the Single Gateway Multi-Tenant Router

set -e

echo "🚀 Deploying WhatsApp Gateway Router..."

# Configuration
GATEWAY_PHONE="+971557357753"
WAHA_URL="http://localhost:3002"
WAHA_API_KEY="0e86a8c2dd774defb6d2da56b409bb89"
BACKEND_URL="http://backend:8000"

echo "📱 Gateway Phone: $GATEWAY_PHONE"
echo "🔧 Waha URL: $WAHA_URL"
echo "🔗 Backend URL: $BACKEND_URL"

# Step 1: Stop existing session
echo ""
echo "⏸️  Stopping existing Waha session..."
curl -X POST \
  -H "X-Api-Key: $WAHA_API_KEY" \
  "$WAHA_URL/api/sessions/default/stop" \
  || echo "Session already stopped or doesn't exist"

sleep 2

# Step 2: Start session with gateway webhook
echo ""
echo "🔄 Starting Waha session with Gateway Router webhook..."
curl -X POST \
  -H "X-Api-Key: $WAHA_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"config\": {
      \"webhooks\": [{
        \"url\": \"$BACKEND_URL/api/gateway/waha\",
        \"events\": [\"message.any\"]
      }]
    }
  }" \
  "$WAHA_URL/api/sessions/default/start"

echo ""
echo "⏳ Waiting for session to initialize..."
sleep 5

# Step 3: Check session status
echo ""
echo "📊 Checking session status..."
curl -s -H "X-Api-Key: $WAHA_API_KEY" \
  "$WAHA_URL/api/sessions/default" | python3 -m json.tool || echo "Could not parse status"

echo ""
echo ""
echo "✅ Gateway Router Deployment Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Check if WhatsApp is connected (status should be WORKING)"
echo "2. If not connected, scan QR code at: $WAHA_URL/"
echo "3. Test with deep link: https://wa.me/${GATEWAY_PHONE##+}?text=start_realty_1"
echo "4. Monitor logs: docker-compose logs -f backend | grep -i 'gateway\\|routing'"
echo ""
echo "🔍 Gateway Stats API: $BACKEND_URL/api/gateway/stats"
echo ""
