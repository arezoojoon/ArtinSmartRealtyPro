#!/bin/bash
# استفاده از API Key تولید شده توسط Waha

echo "🔑 استخراج API Key از لاگ Waha..."

# استخراج API key از لاگ
API_KEY=$(docker-compose logs waha | grep "WAHA_API_KEY=" | tail -1 | sed 's/.*WAHA_API_KEY=//' | tr -d '\r')

if [ -z "$API_KEY" ]; then
    echo "❌ API Key پیدا نشد!"
    echo "لاگ‌های Waha را چک کن:"
    docker-compose logs waha | grep -A 10 "Generated credentials"
    exit 1
fi

echo "✅ API Key پیدا شد: $API_KEY"
echo ""

# تست با API key
echo "🧪 تست شروع session با API key..."
RESPONSE=$(curl -s -X POST http://localhost:3001/api/sessions/start \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: $API_KEY" \
  -d '{"name":"default","config":{"webhooks":[{"url":"http://backend:8000/api/webhook/waha","events":["message"]}]}}')

echo "Response: $RESPONSE"
echo ""

if echo "$RESPONSE" | grep -q "Unauthorized"; then
    echo "❌ هنوز Unauthorized!"
    echo "لطفاً این دستورات را manual اجرا کن:"
    echo ""
    echo "API_KEY=$API_KEY"
    echo ""
    echo 'curl -X POST http://localhost:3001/api/sessions/start \'
    echo '  -H "Content-Type: application/json" \'
    echo "  -H \"X-Api-Key: $API_KEY\" \\"
    echo '  -d '"'"'{"name":"default","config":{"webhooks":[{"url":"http://backend:8000/api/webhook/waha","events":["message"]}]}}'"'"''
    exit 1
fi

echo "✅ Session شروع شد!"
echo ""
echo "📱 حالا QR Code را از این آدرس دریافت کن:"
echo "http://72.60.196.192:3001/api/sessions/default/auth/qr?api_key=$API_KEY"
echo ""
echo "یا در مرورگر به این آدرس برو:"
echo "http://72.60.196.192:3001/api/sessions/default/auth/qr?api_key=$API_KEY"
echo ""
echo "🔑 API Key برای استفاده‌های بعدی:"
echo "export WAHA_API_KEY=$API_KEY"
echo ""
echo "📊 چک وضعیت session:"
echo "curl -H \"X-Api-Key: $API_KEY\" http://localhost:3001/api/sessions/default"
echo ""
