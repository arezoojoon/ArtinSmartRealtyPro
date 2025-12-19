#!/bin/bash

# ArtinSmartRealty - Quick WhatsApp Setup
# Fixes common issues and connects WhatsApp in one go

echo "🚀 Quick WhatsApp Setup for ArtinSmartRealty"
echo "============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "❌ Please run as root (or use sudo)"
  exit 1
fi

# Install jq if missing
if ! command -v jq &> /dev/null; then
    echo "📦 Installing jq..."
    apt-get update -qq && apt-get install -y jq -qq
    echo "✅ jq installed"
else
    echo "✅ jq already installed"
fi
echo ""

# Enable pgcrypto extension
echo "🔧 Enabling PostgreSQL pgcrypto extension..."
docker-compose exec -T db psql -U postgres -d artinrealty -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;" 2>&1 | grep -v "already exists" || true
echo "✅ Extension enabled"
echo ""

# Reset password for tenant 1
echo "🔐 Resetting password for tenant 1 (mohsen@artinsmartagent.com)..."
docker-compose exec -T db psql -U postgres -d artinrealty <<'EOF'
UPDATE tenants 
SET password_hash = encode(
  digest('Test1234!artinsmartrealty_salt_v2'::bytea, 'sha256'::text), 
  'hex'
)
WHERE id = 1;

SELECT 
  id, 
  email, 
  substring(password_hash, 1, 20) as hash_check
FROM tenants 
WHERE id = 1;
EOF
echo ""

# Verify backend is running
echo "🔍 Checking backend service..."
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "")
if [[ "$HEALTH" == *"healthy"* ]]; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend might not be ready. Response: $HEALTH"
    echo "Checking containers..."
    docker-compose ps backend
fi
echo ""

# Login test
echo "🔑 Testing login..."
LOGIN_RESP=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"mohsen@artinsmartagent.com","password":"Test1234!"}')

TOKEN=$(echo "$LOGIN_RESP" | jq -r '.access_token // empty')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo "❌ Login failed!"
  echo "Response: $LOGIN_RESP" | jq '.'
  echo ""
  echo "💡 Try checking .env file for PASSWORD_SALT setting"
  echo "   It should be: PASSWORD_SALT=artinsmartrealty_salt_v2"
  exit 1
fi

TENANT_ID=$(echo "$LOGIN_RESP" | jq -r '.tenant_id')
echo "✅ Login successful! Token: ${TOKEN:0:30}..."
echo "✅ Tenant ID: $TENANT_ID"
echo ""

# Check current WhatsApp status
echo "📊 Checking WhatsApp status..."
STATUS=$(curl -s -X GET "http://localhost:8000/api/tenants/$TENANT_ID/whatsapp/status" \
  -H "Authorization: Bearer $TOKEN")
echo "$STATUS" | jq '.'
echo ""

# Check if already connected
IS_CONNECTED=$(echo "$STATUS" | jq -r '.connected // false')
if [ "$IS_CONNECTED" == "true" ]; then
  PHONE=$(echo "$STATUS" | jq -r '.phone // "unknown"')
  echo "✅ WhatsApp already connected: $PHONE"
  echo ""
  echo "🎉 Setup complete! WhatsApp is ready."
  exit 0
fi

# Create new session
echo "🔌 Creating WhatsApp session..."
CONNECT_RESP=$(curl -s -X POST "http://localhost:8000/api/tenants/$TENANT_ID/whatsapp/connect" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "$CONNECT_RESP" | jq '.'
echo ""

QR_URL=$(echo "$CONNECT_RESP" | jq -r '.qr_url // empty')

if [ -n "$QR_URL" ] && [ "$QR_URL" != "null" ]; then
  echo ""
  echo "╔═══════════════════════════════════════════════════════════╗"
  echo "║          ✅ QR CODE READY FOR WHATSAPP! ✅               ║"
  echo "╚═══════════════════════════════════════════════════════════╝"
  echo ""
  echo "📱 SCAN THIS QR CODE:"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "$QR_URL"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "📋 STEPS TO CONNECT:"
  echo "  1. Open the URL above in your browser"
  echo "  2. Open WhatsApp on your phone"
  echo "  3. Go to: Settings → Linked Devices → Link a Device"
  echo "  4. Scan the QR code from your browser"
  echo ""
  echo "⏱️  After scanning, wait 5-10 seconds then check status:"
  echo "   curl -s -X GET \"http://localhost:8000/api/tenants/$TENANT_ID/whatsapp/status\" \\"
  echo "     -H \"Authorization: Bearer $TOKEN\" | jq"
  echo ""
  
  # Save for later use
  cat > /tmp/whatsapp_session.env <<ENV
export TENANT_ID=$TENANT_ID
export TOKEN=$TOKEN
export QR_URL=$QR_URL
ENV
  
  echo "💾 Session saved to: /tmp/whatsapp_session.env"
  echo "   To reuse: source /tmp/whatsapp_session.env"
  echo ""
  
  # Check Waha sessions
  echo "📋 Current Waha sessions:"
  curl -s http://localhost:3002/api/sessions 2>/dev/null | jq '.' || echo "[]"
  
  echo ""
  echo "🎉 Setup complete! Scan the QR code to finish."
else
  echo "❌ Failed to generate QR URL"
  echo "Response: $CONNECT_RESP"
  exit 1
fi
