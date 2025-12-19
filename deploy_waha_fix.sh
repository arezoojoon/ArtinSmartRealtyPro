#!/bin/bash
# Waha Authentication Fix Deployment Script

echo "🔄 Deploying Waha authentication fix..."

# Pull latest changes
git pull origin main

# Restart Waha with new configuration
echo "🔄 Restarting Waha service..."
docker-compose down waha
docker-compose up -d waha

# Wait for Waha to start
echo "⏳ Waiting for Waha to initialize (10 seconds)..."
sleep 10

# Check Waha health
echo "🏥 Checking Waha health..."
curl -s http://localhost:3001/api/server/health || echo "⚠️  Health endpoint not responding yet"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📱 Next steps:"
echo "1. Open browser: http://$(hostname -I | awk '{print $1}'):3001"
echo "   OR: http://srv1151343.hstgr.io:3001"
echo ""
echo "2. Navigate to: http://YOUR_SERVER_IP:3001/api/sessions/default/start"
echo "   This will initialize the WhatsApp session"
echo ""
echo "3. Get QR Code: http://YOUR_SERVER_IP:3001/api/sessions/default/auth/qr"
echo ""
echo "4. Scan QR code with WhatsApp:"
echo "   - Open WhatsApp on your phone"
echo "   - Settings → Linked Devices"
echo "   - Link a Device"
echo "   - Scan the QR code from browser"
echo ""
echo "🔍 Monitor logs:"
echo "   docker-compose logs -f waha"
