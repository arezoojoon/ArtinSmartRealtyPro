#!/bin/bash

echo "🔧 Simple WhatsApp Connection Test for ArtinSmartRealty..."
echo "=================================================="
echo ""

# Configuration
BASE_URL="http://localhost:8000"
TENANT_EMAIL="mohsen@artinsmartagent.com"
TENANT_PASS="Test1234!"  # Use existing password
TENANT_ID=1

echo "1️⃣ Logging in as $TENANT_EMAIL..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TENANT_EMAIL\",\"password\":\"$TENANT_PASS\"}")

# Extract token manually (no jq needed)
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed. Response:"
  echo "$LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Login successful!"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Extract tenant_id
TENANT_ID_FROM_LOGIN=$(echo "$LOGIN_RESPONSE" | grep -o '"tenant_id":[0-9]*' | cut -d':' -f2)
if [ -n "$TENANT_ID_FROM_LOGIN" ]; then
  TENANT_ID=$TENANT_ID_FROM_LOGIN
fi
echo "✅ Tenant ID: $TENANT_ID"
echo ""

echo "2️⃣ Checking WhatsApp status..."
STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/tenants/$TENANT_ID/whatsapp/status" \
  -H "Authorization: Bearer $TOKEN")

echo "$STATUS_RESPONSE"
echo ""

echo "3️⃣ Connecting WhatsApp (creating Waha session)..."
CONNECT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/tenants/$TENANT_ID/whatsapp/connect" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "$CONNECT_RESPONSE"
echo ""

# Extract QR URL manually
QR_URL=$(echo "$CONNECT_RESPONSE" | grep -o '"qr_url":"[^"]*' | cut -d'"' -f4)

if [ -n "$QR_URL" ]; then
  echo "✅ ✅ ✅ QR Code URL Generated! ✅ ✅ ✅"
  echo "=========================================="
  echo "$QR_URL"
  echo "=========================================="
  echo ""
  echo "📱 NEXT STEPS:"
  echo "1. Open this URL in browser: $QR_URL"
  echo "2. Open WhatsApp on your phone"
  echo "3. Go to: Settings > Linked Devices > Link a Device"
  echo "4. Scan the QR code from browser"
  echo ""
  echo "After scanning, check status again:"
  echo "curl -X GET \"$BASE_URL/api/tenants/$TENANT_ID/whatsapp/status\" -H \"Authorization: Bearer $TOKEN\""
else
  echo "⚠️  Could not extract QR URL. Full response above."
fi

echo ""
echo "4️⃣ Checking Waha service..."
WAHA_SESSIONS=$(curl -s http://localhost:3002/api/sessions 2>/dev/null || echo "Waha not accessible")
echo "$WAHA_SESSIONS"

echo ""
echo "✅ Test completed!"
