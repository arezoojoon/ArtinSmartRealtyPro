#!/bin/bash

# Quick Test Script for WhatsApp Gateway Router

echo "🧪 WhatsApp Gateway Router - Quick Test"
echo "========================================"
echo ""

BACKEND_URL="http://localhost:8000"

# Test 1: Check gateway stats
echo "📊 Test 1: Gateway Statistics"
echo "------------------------------"
curl -s "$BACKEND_URL/api/gateway/stats" | python3 -m json.tool
echo ""

# Test 2: Check specific user mapping
echo "📱 Test 2: Check User Mapping (Example: 971501234567)"
echo "------------------------------------------------------"
curl -s "$BACKEND_URL/api/gateway/user/971501234567/tenant" | python3 -m json.tool
echo ""

# Test 3: Check mapping file directly
echo "📄 Test 3: View Mapping File"
echo "----------------------------"
if [ -f "backend/data/user_tenant_mapping.json" ]; then
    cat backend/data/user_tenant_mapping.json | python3 -m json.tool
else
    echo "⚠️  Mapping file not found (will be created on first message)"
fi
echo ""

echo "✅ Test Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Send test message to gateway WhatsApp: +971 55 735 7753"
echo "2. Message format: 'start_realty_1' (replace 1 with your tenant_id)"
echo "3. Monitor logs: docker-compose logs -f backend | grep -i gateway"
echo ""
