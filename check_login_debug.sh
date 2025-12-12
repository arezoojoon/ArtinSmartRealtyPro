#!/bin/bash

echo "🔍 Debugging Login Issue"
echo "========================"
echo ""

# Check .env file
echo "1️⃣ Checking .env file..."
if [ -f .env ]; then
    echo "✅ .env file exists"
    echo ""
    echo "PASSWORD_SALT setting:"
    grep "^PASSWORD_SALT" .env || echo "❌ PASSWORD_SALT not found in .env"
    echo ""
else
    echo "❌ .env file not found!"
    echo ""
fi

# Try login with raw curl
echo "2️⃣ Testing login endpoint..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"mohsen@artinsmartagent.com","password":"Test1234!"}')

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d':' -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE")

echo "HTTP Status: $HTTP_CODE"
echo "Response Body:"
echo "$BODY"
echo ""

# Check backend logs
echo "3️⃣ Recent backend logs (last 20 lines):"
docker-compose logs --tail=20 backend

echo ""
echo "4️⃣ Database password hash check:"
docker-compose exec -T db psql -U postgres -d artinrealty -c "SELECT id, email, substring(password_hash, 1, 40) as hash FROM tenants WHERE id = 1;"

echo ""
echo "5️⃣ Testing password hash generation in Python:"
docker-compose exec -T backend python3 -c "
import hashlib
password = 'Test1234!'
salt = 'artinsmartrealty_salt_v2'
hash_result = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
print(f'Generated hash: {hash_result[:40]}...')
"

echo ""
echo "✅ Debug complete!"
