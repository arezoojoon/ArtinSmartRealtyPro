#!/bin/bash

echo "🚀 ArtinSmartRealty - WhatsApp Multi-Session Deployment"
echo "======================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8000"
DB_NAME="artinrealty"
DB_USER="postgres"

echo "Step 1: Installing required packages..."
echo "---------------------------------------"
if ! command -v jq &> /dev/null; then
    echo "📦 Installing jq for JSON parsing..."
    apt-get update -qq && apt-get install -y jq
else
    echo "✅ jq already installed"
fi
echo ""

echo "Step 2: Enabling PostgreSQL extensions..."
echo "------------------------------------------"
docker-compose exec -T db psql -U $DB_USER -d $DB_NAME <<'EOF'
CREATE EXTENSION IF NOT EXISTS pgcrypto;
SELECT extname, extversion FROM pg_extension WHERE extname = 'pgcrypto';
EOF
echo ""

echo "Step 3: Fixing password hash for tenant 1..."
echo "---------------------------------------------"
docker-compose exec -T db psql -U $DB_USER -d $DB_NAME <<'EOF'
UPDATE tenants 
SET password_hash = encode(
  digest('Test1234!artinsmartrealty_salt_v2', 'sha256'), 
  'hex'
)
WHERE id = 1;

SELECT id, email, substring(password_hash, 1, 20) as hash_preview 
FROM tenants 
WHERE id = 1;
EOF
echo ""

echo "Step 4: Verifying Waha service..."
echo "----------------------------------"
WAHA_SESSIONS=$(curl -s http://localhost:3002/api/sessions 2>/dev/null || echo "not accessible")
if [[ "$WAHA_SESSIONS" == "["* ]] || [[ "$WAHA_SESSIONS" == "{"* ]]; then
    echo -e "${GREEN}✅ Waha service is running${NC}"
    echo "Current sessions: $WAHA_SESSIONS"
else
    echo -e "${YELLOW}⚠️  Waha response: $WAHA_SESSIONS${NC}"
    echo "Checking Docker containers..."
    docker-compose ps waha
fi
echo ""

echo "Step 5: Testing login..."
echo "------------------------"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"mohsen@artinsmartagent.com","password":"Test1234!"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo -e "${RED}❌ Login failed. Response:${NC}"
  echo "$LOGIN_RESPONSE" | jq '.'
  exit 1
fi

echo -e "${GREEN}✅ Login successful!${NC}"
TENANT_ID=$(echo "$LOGIN_RESPONSE" | jq -r '.tenant_id')
echo "Tenant ID: $TENANT_ID"
echo ""

echo "Step 6: Connecting WhatsApp..."
echo "-------------------------------"
CONNECT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/tenants/$TENANT_ID/whatsapp/connect" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "$CONNECT_RESPONSE" | jq '.'

QR_URL=$(echo "$CONNECT_RESPONSE" | jq -r '.qr_url // empty')

if [ -n "$QR_URL" ] && [ "$QR_URL" != "null" ]; then
  echo ""
  echo -e "${GREEN}✅ ✅ ✅ SUCCESS! QR Code Ready! ✅ ✅ ✅${NC}"
  echo "=========================================="
  echo -e "${YELLOW}$QR_URL${NC}"
  echo "=========================================="
  echo ""
  echo "📱 SCAN THIS QR CODE:"
  echo "1. Open URL in browser: $QR_URL"
  echo "2. WhatsApp > Settings > Linked Devices > Link a Device"
  echo "3. Scan the QR code"
  echo ""
  
  # Save credentials for future tests
  cat > /tmp/whatsapp_test_creds.sh <<CREDS
export TENANT_ID=$TENANT_ID
export TOKEN=$TOKEN
export QR_URL=$QR_URL
CREDS
  
  echo "💾 Credentials saved to /tmp/whatsapp_test_creds.sh"
  echo ""
  echo "After scanning, check status:"
  echo "curl -X GET \"$BASE_URL/api/tenants/$TENANT_ID/whatsapp/status\" -H \"Authorization: Bearer \$TOKEN\" | jq"
else
  echo -e "${RED}❌ Failed to generate QR URL${NC}"
  echo "Response: $CONNECT_RESPONSE"
  exit 1
fi

echo ""
echo "Step 7: Current Waha sessions..."
echo "---------------------------------"
SESSIONS=$(curl -s http://localhost:3002/api/sessions 2>/dev/null || echo '[]')
echo "$SESSIONS" | jq '.'

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo "Summary:"
echo "--------"
echo "• Database: pgcrypto extension enabled"
echo "• Password: Reset for tenant 1"
echo "• Waha: Session tenant_$TENANT_ID created"
echo "• QR Code: $QR_URL"
echo ""
echo "Next: Scan QR code to connect WhatsApp!"
