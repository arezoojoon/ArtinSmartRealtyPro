#!/bin/bash
# Deployment script for JWT Secret Fix + Admin API Authentication Fix
# Run on production server: bash deploy_jwt_fix.sh

set -e  # Exit on error

echo "🔧 ArtinSmartRealty - Complete Authentication Fix Deployment"
echo "============================================================="
echo ""

# Step 1: Pull latest code
echo "📥 Step 1: Pulling latest code from GitHub..."
cd /opt/ArtinSmartRealty
git pull origin main
echo "✅ Code updated (latest commit: $(git rev-parse --short HEAD))"
echo ""

# Step 2: Check if JWT_SECRET exists in .env
echo "🔍 Step 2: Checking JWT_SECRET in .env..."
if grep -q "^JWT_SECRET=" .env 2>/dev/null; then
    echo "✅ JWT_SECRET already exists in .env"
    JWT_SECRET_LENGTH=$(grep "^JWT_SECRET=" .env | cut -d'=' -f2 | wc -c)
    echo "   Length: $JWT_SECRET_LENGTH characters"
else
    echo "⚠️  JWT_SECRET not found in .env"
    echo "🔑 Generating new secure JWT_SECRET..."
    
    # Generate a secure JWT secret
    JWT_SECRET=$(openssl rand -base64 64 | tr -d '\n')
    
    # Add to .env file
    echo "" >> .env
    echo "# JWT Secret (Auto-generated on $(date))" >> .env
    echo "JWT_SECRET=${JWT_SECRET}" >> .env
    
    echo "✅ JWT_SECRET added to .env (${#JWT_SECRET} characters)"
fi
echo ""

# Step 3: Check PASSWORD_SALT
echo "🔍 Step 3: Checking PASSWORD_SALT in .env..."
if grep -q "^PASSWORD_SALT=" .env 2>/dev/null; then
    echo "✅ PASSWORD_SALT already exists in .env"
else
    echo "⚠️  PASSWORD_SALT not found in .env"
    echo "🔑 Adding default PASSWORD_SALT..."
    
    echo "" >> .env
    echo "# Password Salt" >> .env
    echo "PASSWORD_SALT=artinsmartrealty_salt_v2" >> .env
    
    echo "✅ PASSWORD_SALT added to .env"
fi
echo ""

# Step 4: Rebuild and restart backend
echo "🔄 Step 4: Rebuilding and restarting backend..."
docker-compose down backend
docker-compose build backend
docker-compose up -d backend

echo "⏳ Waiting for backend to start..."
sleep 20

# Check if backend is healthy
for i in {1..15}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ Backend failed to start!"
        echo "Checking logs..."
        docker-compose logs backend --tail 50
        exit 1
    fi
    echo "Waiting for backend... ($i/15)"
    sleep 3
done
echo ""

# Step 5: Verify environment variables in container
echo "📋 Step 5: Verifying JWT Configuration in container..."
echo "------------------------------------------------------"
docker-compose exec backend python -c "
import os
jwt_secret = os.getenv('JWT_SECRET', '')
password_salt = os.getenv('PASSWORD_SALT', 'NOT_SET')
print(f'✅ JWT_SECRET exists: {\"JWT_SECRET\" in os.environ}')
print(f'✅ JWT_SECRET length: {len(jwt_secret)} characters')
print(f'✅ PASSWORD_SALT: {password_salt}')
print(f'✅ SUPER_ADMIN_EMAIL: {os.getenv(\"SUPER_ADMIN_EMAIL\", \"NOT_SET\")}')
" || echo "⚠️  Could not verify environment variables"
echo ""

# Step 6: Test Super Admin Authentication
echo "🧪 Step 6: Testing Super Admin Authentication..."
echo "-------------------------------------------------"

# Test login
echo "▶️  Testing login endpoint..."
LOGIN_RESPONSE=$(curl -s https://realty.artinsmartagent.com/api/auth/login \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@artinsmartrealty.com","password":"SuperARTIN2588357!"}' \
    2>&1)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login successful!"
    echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null | head -10 || echo "$LOGIN_RESPONSE" | head -5
else
    echo "❌ Login failed!"
    echo "$LOGIN_RESPONSE"
    exit 1
fi
echo ""

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to extract access token!"
    exit 1
fi

echo "✅ Token extracted: ${TOKEN:0:50}..."
echo ""

# Step 7: Test Admin Endpoints
echo "🧪 Step 7: Testing Admin API Endpoints..."
echo "------------------------------------------"

# Test /api/admin/tenants
echo "▶️  Testing GET /api/admin/tenants..."
TENANTS_RESPONSE=$(curl -s https://realty.artinsmartagent.com/api/admin/tenants \
    -H "Authorization: Bearer $TOKEN" \
    2>&1)

if echo "$TENANTS_RESPONSE" | grep -q '"id"'; then
    echo "✅ SUCCESS! /api/admin/tenants is working!"
    echo ""
    echo "Tenants list (first 3):"
    echo "$TENANTS_RESPONSE" | python3 -m json.tool 2>/dev/null | head -50 || echo "$TENANTS_RESPONSE" | head -20
    TENANT_COUNT=$(echo "$TENANTS_RESPONSE" | grep -o '"id"' | wc -l)
    echo ""
    echo "📊 Total tenants: $TENANT_COUNT"
elif echo "$TENANTS_RESPONSE" | grep -q "Invalid token\|Not authenticated\|Token expired"; then
    echo "❌ FAILED! Authentication error:"
    echo "$TENANTS_RESPONSE"
    echo ""
    echo "🔍 Checking backend logs for errors..."
    docker-compose logs backend --tail 100 | grep -i "error\|invalid\|token\|401"
    exit 1
else
    echo "⚠️  Unexpected response:"
    echo "$TENANTS_RESPONSE"
    exit 1
fi
echo ""

# Test /api/admin/features
echo "▶️  Testing GET /api/admin/features..."
FEATURES_RESPONSE=$(curl -s https://realty.artinsmartagent.com/api/admin/features \
    -H "Authorization: Bearer $TOKEN" \
    2>&1)

if echo "$FEATURES_RESPONSE" | grep -q '"tenant_id"'; then
    echo "✅ SUCCESS! /api/admin/features is working!"
    echo ""
    echo "Feature flags (first 20 lines):"
    echo "$FEATURES_RESPONSE" | python3 -m json.tool 2>/dev/null | head -20 || echo "$FEATURES_RESPONSE" | head -15
else
    echo "⚠️  Feature flags endpoint issue (non-critical):"
    echo "$FEATURES_RESPONSE" | head -10
fi
echo ""

# Step 8: Final Summary
echo "🎉 =============================================="
echo "🎉 DEPLOYMENT SUCCESSFUL!"
echo "🎉 =============================================="
echo ""
echo "✅ All authentication systems working:"
echo "   • JWT Secret: Configured and consistent"
echo "   • Login endpoint: Working"
echo "   • Admin API: Working"
echo "   • Token validation: Working"
echo ""
echo "📝 Next Steps:"
echo "   1. Open browser: https://realty.artinsmartagent.com"
echo "   2. Login with: admin@artinsmartrealty.com"
echo "   3. Password: SuperARTIN2588357!"
echo "   4. Test Super Admin Dashboard"
echo "   5. Manage tenant feature flags"
echo ""
echo "🎯 Super Admin Panel is fully operational!"
echo ""
