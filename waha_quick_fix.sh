#!/bin/bash
# Waha Quick Fix - بدون نیاز به rebuild

echo "🔧 Fixing Waha authentication issue..."

# Stop Waha completely
echo "⏹️  Stopping Waha..."
docker-compose stop waha
docker-compose rm -f waha

# Remove volume to reset everything
echo "🗑️  Removing old Waha data..."
docker volume rm artinsmartrealty_waha_data 2>/dev/null || echo "Volume already removed or doesn't exist"

# Start Waha with new config
echo "🚀 Starting Waha with new configuration..."
docker-compose up -d waha

# Wait for Waha to fully start
echo "⏳ Waiting 15 seconds for Waha to initialize..."
sleep 15

# Check Waha status
echo ""
echo "🏥 Checking Waha health..."
curl -s http://localhost:3001/api/server/health 2>/dev/null || echo "Health check endpoint not responding"

echo ""
echo "✅ Waha restarted!"
echo ""
echo "📱 Now run these commands:"
echo ""
echo "1️⃣  Start WhatsApp session:"
echo 'curl -X POST http://localhost:3001/api/sessions/start -H "Content-Type: application/json" -d '"'"'{"name":"default","config":{"webhooks":[{"url":"http://backend:8000/api/webhook/waha","events":["message"]}]}}'"'"''
echo ""
echo "2️⃣  Get QR Code in browser:"
echo "   http://72.60.196.192:3001/api/sessions/default/auth/qr"
echo ""
echo "3️⃣  Check session status:"
echo "   curl http://localhost:3001/api/sessions/default"
echo ""
