#!/bin/bash

echo "🔍 Direct WhatsApp Connection Test"
echo "==================================="
echo ""

# Get credentials
SALT=$(grep "^PASSWORD_SALT=" .env | cut -d'=' -f2)
echo "🔐 Logging in..."

LOGIN_RESP=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"mohsen@artinsmartagent.com","password":"Test1234!"}')

echo "Login response:"
echo "$LOGIN_RESP"
echo ""

TOKEN=$(echo "$LOGIN_RESP" | jq -r '.access_token // empty' 2>/dev/null)
TENANT_ID=$(echo "$LOGIN_RESP" | jq -r '.tenant_id // empty' 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Could not extract token"
    exit 1
fi

echo "✅ Token: ${TOKEN:0:30}..."
echo "✅ Tenant ID: $TENANT_ID"
echo ""

echo "📊 Checking current WhatsApp status..."
STATUS_RESP=$(curl -s -X GET "http://localhost:8000/api/tenants/$TENANT_ID/whatsapp/status" \
  -H "Authorization: Bearer $TOKEN")

echo "Status response:"
echo "$STATUS_RESP"
echo ""

echo "🔌 Creating WhatsApp connection..."
CONNECT_RESP=$(curl -s -X POST "http://localhost:8000/api/tenants/$TENANT_ID/whatsapp/connect" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "Connect response:"
echo "$CONNECT_RESP"
echo ""

# Try to extract QR URL without jq first
QR_URL=$(echo "$CONNECT_RESP" | grep -o '"qr_url":"[^"]*' | cut -d'"' -f4)

if [ -n "$QR_URL" ]; then
  echo ""
  echo "╔═══════════════════════════════════════════════════════════╗"
  echo "║          ✅ QR CODE URL FOUND! ✅                        ║"
  echo "╚═══════════════════════════════════════════════════════════╝"
  echo ""
  echo "📱 SCAN THIS QR CODE:"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "$QR_URL"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "STEPS:"
  echo "1. Open in browser: $QR_URL"
  echo "2. WhatsApp → Settings → Linked Devices → Link a Device"
  echo "3. Scan the QR code"
  echo ""
  
  # Save credentials
  cat > /tmp/whatsapp_creds.txt <<EOF
TENANT_ID=$TENANT_ID
TOKEN=$TOKEN
QR_URL=$QR_URL
EOF
  
  echo "💾 Saved to /tmp/whatsapp_creds.txt"
  echo ""
  echo "After scanning, check with:"
  echo "curl -s \"http://localhost:8000/api/tenants/$TENANT_ID/whatsapp/status\" -H \"Authorization: Bearer $TOKEN\""
else
  echo "⚠️  Could not find QR URL in response"
  echo "Full response above - check for errors"
fi

echo ""
echo "✅ Done!"
