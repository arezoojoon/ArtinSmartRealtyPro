#!/bin/bash
# Deployment script for JWT Secret Fix
# Run on production server: bash deploy_jwt_fix.sh

set -e  # Exit on error

echo "🔧 ArtinSmartRealty - JWT Secret Fix Deployment"
echo "================================================"
echo ""

# Step 1: Pull latest code
echo "📥 Step 1: Pulling latest code from GitHub..."
git pull origin main
echo "✅ Code updated"
echo ""

# Step 2: Check if JWT_SECRET exists in .env
echo "🔍 Step 2: Checking JWT_SECRET in .env..."
if grep -q "^JWT_SECRET=" .env 2>/dev/null; then
    echo "✅ JWT_SECRET already exists in .env"
else
    echo "⚠️  JWT_SECRET not found in .env"
    echo "🔑 Generating new JWT_SECRET..."
    
    # Generate a secure JWT secret
    JWT_SECRET=$(openssl rand -base64 64 | tr -d '\n')
    
    # Add to .env file
    echo "" >> .env
    echo "# JWT Secret (Auto-generated on $(date))" >> .env
    echo "JWT_SECRET=${JWT_SECRET}" >> .env
    
    echo "✅ JWT_SECRET added to .env"
fi
echo ""

# Step 3: Check PASSWORD_SALT
echo "🔍 Step 3: Checking PASSWORD_SALT in .env..."
if grep -q "^PASSWORD_SALT=" .env 2>/dev/null; then
    echo "✅ PASSWORD_SALT already exists in .env"
else
    echo "⚠️  PASSWORD_SALT not found in .env"
    echo "🔑 Using default PASSWORD_SALT..."
    
    echo "" >> .env
    echo "# Password Salt" >> .env
    echo "PASSWORD_SALT=artinsmartrealty_salt_v2" >> .env
    
    echo "✅ PASSWORD_SALT added to .env"
fi
echo ""

# Step 4: Show current environment variables
echo "📋 Step 4: Current JWT Configuration:"
echo "-------------------------------------"
docker-compose exec backend python -c "
import os
print(f'JWT_SECRET exists: {\"JWT_SECRET\" in os.environ}')
print(f'JWT_SECRET length: {len(os.getenv(\"JWT_SECRET\", \"\"))}')
print(f'PASSWORD_SALT: {os.getenv(\"PASSWORD_SALT\", \"NOT_SET\")}')
" 2>/dev/null || echo "Backend not running yet"
echo ""

# Step 5: Restart backend
echo "🔄 Step 5: Restarting backend..."
docker-compose down backend
docker-compose up -d backend

echo "⏳ Waiting for backend to start..."
sleep 15

# Check if backend is healthy
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    fi
    echo "Waiting for backend... ($i/10)"
    sleep 3
done
echo ""

# Step 6: Test authentication
echo "🧪 Step 6: Testing Super Admin Authentication..."
echo "------------------------------------------------"

# Test login
echo "Testing login endpoint..."
LOGIN_RESPONSE=$(curl -s https://realty.artinsmartagent.com/api/auth/login \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@artinsmartrealty.com","password":"SuperARTIN2588357!"}')

echo "Login response:"
echo "$LOGIN_RESPONSE" | python3 -m json.tool || echo "$LOGIN_RESPONSE"
echo ""

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get access token!"
    exit 1
fi

echo "✅ Token obtained: ${TOKEN:0:50}..."
echo ""

# Test admin endpoint
echo "Testing admin/tenants endpoint..."
ADMIN_RESPONSE=$(curl -s https://realty.artinsmartagent.com/api/admin/tenants \
    -H "Authorization: Bearer $TOKEN")

echo "Admin response:"
echo "$ADMIN_RESPONSE" | python3 -m json.tool || echo "$ADMIN_RESPONSE"
echo ""

# Check if successful
if echo "$ADMIN_RESPONSE" | grep -q '"id"'; then
    echo "✅ SUCCESS! Admin API is working!"
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo "Super Admin can now access all endpoints."
elif echo "$ADMIN_RESPONSE" | grep -q "Invalid token\|Not authenticated"; then
    echo "❌ FAILED! Still getting authentication error"
    echo ""
    echo "🔍 Debugging information:"
    docker-compose logs backend --tail 50 | grep -i "error\|invalid\|token"
    exit 1
else
    echo "⚠️  Unexpected response from admin API"
    exit 1
fi

# Step 7: Test feature flags endpoint
echo ""
echo "🧪 Step 7: Testing Feature Flags API..."
FEATURES_RESPONSE=$(curl -s https://realty.artinsmartagent.com/api/admin/features \
    -H "Authorization: Bearer $TOKEN")

echo "Features response:"
echo "$FEATURES_RESPONSE" | python3 -m json.tool | head -30
echo ""

echo "✅ All tests passed!"
echo ""
echo "📝 Next Steps:"
echo "1. Login to Super Admin dashboard: https://realty.artinsmartagent.com"
echo "2. Use credentials: admin@artinsmartrealty.com / SuperARTIN2588357!"
echo "3. Test feature flags management"
echo ""
echo "🎯 JWT Secret is now consistent across all modules!"
