#!/bin/bash

# Quick test script for WhatsApp Multi-Session API

echo "🔧 Testing WhatsApp Multi-Session for ArtinSmartRealty..."
echo "=================================================="

# Step 1: Create a new tenant with known password
echo ""
echo "1️⃣ Creating test tenant..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/admin/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Agent",
    "email": "test@test.com",
    "password": "TestPass123!",
    "company_name": "Test Realty"
  }')

echo "$RESPONSE"

# Step 2: Login with test tenant
echo ""
echo "2️⃣ Logging in as test tenant..."
LOGIN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"TestPass123!"}')

TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
TENANT_ID=$(echo "$LOGIN" | grep -o '"tenant_id":[0-9]*' | cut -d':' -f2)

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed. Trying with existing tenant mohsen@artinsmartagent.com..."
    
    # Try resetting password for tenant 1
    echo ""
    echo "3️⃣ Resetting password for tenant 1..."
    docker-compose exec -T db psql -U postgres -d artinrealty <<EOF
UPDATE tenants 
SET password_hash = encode(digest('TestPass123!artinsmartrealty_salt_v2', 'sha256'), 'hex')
WHERE id = 1;
EOF
    
    LOGIN=$(curl -s -X POST http://localhost:8000/api/auth/login \
      -H "Content-Type: application/json" \
      -d '{"email":"mohsen@artinsmartagent.com","password":"TestPass123!"}')
    
    TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    TENANT_ID=1
fi

echo "✅ Token: ${TOKEN:0:30}..."
echo "✅ Tenant ID: $TENANT_ID"

# Step 3: Check WhatsApp status
echo ""
echo "3️⃣ Checking WhatsApp status for tenant $TENANT_ID..."
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/tenants/$TENANT_ID/whatsapp/status | jq

# Step 4: Connect WhatsApp
echo ""
echo "4️⃣ Connecting WhatsApp for tenant $TENANT_ID..."
CONNECT_RESULT=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/tenants/$TENANT_ID/whatsapp/connect)

echo "$CONNECT_RESULT" | jq

# Extract QR URL
QR_URL=$(echo "$CONNECT_RESULT" | grep -o '"qr_url":"[^"]*"' | cut -d'"' -f4)

if [ ! -z "$QR_URL" ]; then
    echo ""
    echo "📱 QR CODE URL:"
    echo "$QR_URL"
    echo ""
    echo "✅ Open this URL in your browser to scan the QR code!"
else
    echo "⚠️  No QR URL received. Check response above."
fi

# Step 5: Check Waha sessions
echo ""
echo "5️⃣ Checking Waha sessions..."
API_KEY=$(grep "WAHA_API_KEY=" .env 2>/dev/null | cut -d'=' -f2)

if [ ! -z "$API_KEY" ]; then
    curl -s -H "X-Api-Key: $API_KEY" http://localhost:3002/api/sessions | jq
else
    curl -s http://localhost:3002/api/sessions | jq
fi

echo ""
echo "✅ Test completed!"
