#!/bin/bash

echo "🔧 Fixing Password with Correct Salt from .env"
echo "==============================================="
echo ""

# Read actual salt from .env
SALT=$(grep "^PASSWORD_SALT=" .env | cut -d'=' -f2)

if [ -z "$SALT" ]; then
    echo "❌ PASSWORD_SALT not found in .env"
    exit 1
fi

echo "✅ Using PASSWORD_SALT from .env:"
echo "   ${SALT:0:40}..."
echo ""

# Generate correct hash using Python
echo "🔐 Generating password hash for 'Test1234!'..."
CORRECT_HASH=$(docker-compose exec -T backend python3 -c "
import hashlib
import os
password = 'Test1234!'
salt = '$SALT'
hash_result = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
print(hash_result)
" | tr -d '\r')

echo "Generated hash: ${CORRECT_HASH:0:40}..."
echo ""

# Update database with correct hash
echo "💾 Updating database..."
docker-compose exec -T db psql -U postgres -d artinrealty <<EOF
UPDATE tenants 
SET password_hash = '$CORRECT_HASH'
WHERE id = 1;

SELECT 
  id, 
  email, 
  substring(password_hash, 1, 40) as hash_check,
  CASE 
    WHEN password_hash = '$CORRECT_HASH' THEN '✅ CORRECT'
    ELSE '❌ MISMATCH'
  END as status
FROM tenants 
WHERE id = 1;
EOF

echo ""
echo "🔑 Testing login..."
LOGIN_RESP=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"mohsen@artinsmartagent.com","password":"Test1234!"}')

TOKEN=$(echo "$LOGIN_RESP" | jq -r '.access_token // empty')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo "❌ Login still failed!"
  echo "$LOGIN_RESP" | jq '.'
  exit 1
fi

TENANT_ID=$(echo "$LOGIN_RESP" | jq -r '.tenant_id')
echo "✅ Login successful!"
echo "   Token: ${TOKEN:0:30}..."
echo "   Tenant ID: $TENANT_ID"
echo ""

# Now connect WhatsApp
echo "🔌 Connecting WhatsApp..."
CONNECT_RESP=$(curl -s -X POST "http://localhost:8000/api/tenants/$TENANT_ID/whatsapp/connect" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

QR_URL=$(echo "$CONNECT_RESP" | jq -r '.qr_url // empty')

if [ -n "$QR_URL" ] && [ "$QR_URL" != "null" ]; then
  echo ""
  echo "╔═══════════════════════════════════════════════════════════╗"
  echo "║          ✅ SUCCESS! QR CODE READY! ✅                   ║"
  echo "╚═══════════════════════════════════════════════════════════╝"
  echo ""
  echo "📱 SCAN THIS QR CODE:"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "$QR_URL"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "📋 STEPS:"
  echo "  1. Open URL in browser: $QR_URL"
  echo "  2. WhatsApp → Settings → Linked Devices → Link a Device"
  echo "  3. Scan the QR code"
  echo ""
  
  # Save session
  cat > /tmp/whatsapp_session.env <<ENV
export TENANT_ID=$TENANT_ID
export TOKEN=$TOKEN
export QR_URL=$QR_URL
ENV
  
  echo "💾 Session saved to /tmp/whatsapp_session.env"
  echo ""
  echo "✅ After scanning, check status:"
  echo "   source /tmp/whatsapp_session.env"
  echo "   curl -s -X GET \"http://localhost:8000/api/tenants/\$TENANT_ID/whatsapp/status\" \\"
  echo "     -H \"Authorization: Bearer \$TOKEN\" | jq"
else
  echo "Response: $CONNECT_RESP" | jq '.'
fi

echo ""
echo "🎉 Complete!"
