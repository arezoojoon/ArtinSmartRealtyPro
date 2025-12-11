#!/bin/bash
# 🎯 راه‌حل نهایی - Waha بدون Authentication

echo "🚀 دیپلوی Waha با noweb image..."

# Pull changes
echo "📥 Pulling latest code..."
git pull origin main

# Stop old Waha
echo "⏹️  Stopping old Waha container..."
docker-compose down waha

# Pull new image
echo "📦 Pulling Waha noweb image..."
docker-compose pull waha

# Clean old volume
echo "🗑️  Cleaning old data..."
docker volume rm artinsmartrealty_waha_data 2>/dev/null || true

# Start Waha
echo "🚀 Starting Waha..."
docker-compose up -d waha

# Wait for initialization
echo "⏳ Waiting 15 seconds for Waha to start..."
sleep 15

# Test health
echo ""
echo "🏥 Testing Waha health..."
HEALTH=$(curl -s http://localhost:3001/api/server/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Waha is responding: $HEALTH"
else
    echo "⚠️  Waha not responding yet, checking logs..."
    docker-compose logs --tail=20 waha
fi

echo ""
echo "================================================"
echo "✅ Deployment Complete!"
echo "================================================"
echo ""
echo "📱 NEXT STEPS:"
echo ""
echo "1️⃣  Start WhatsApp Session:"
echo "   curl -X POST http://localhost:3001/api/sessions/start \\"
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"name":"default","config":{"webhooks":[{"url":"http://backend:8000/api/webhook/waha","events":["message"]}]}}'"'"''
echo ""
echo "2️⃣  Get QR Code (Open in Browser):"
echo "   http://72.60.196.192:3001/api/sessions/default/auth/qr"
echo ""
echo "3️⃣  Scan with WhatsApp:"
echo "   Settings → Linked Devices → Link a Device"
echo ""
echo "4️⃣  Check Session Status:"
echo "   curl http://localhost:3001/api/sessions/default"
echo ""
echo "   Should show: \"status\":\"WORKING\" after QR scan"
echo ""
echo "📊 Monitor Logs:"
echo "   docker-compose logs -f waha"
echo ""
