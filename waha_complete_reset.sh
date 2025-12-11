#!/bin/bash
# 🔥 راه‌حل نهایی نهایی - پاک کردن کامل و شروع از صفر

echo "🔥 پاک کردن کامل Waha و شروع از صفر..."

# Stop everything related to Waha
echo "⏹️  Stopping all Waha processes..."
docker-compose stop waha
docker rm -f artinrealty-waha 2>/dev/null || true
docker rm -f $(docker ps -a | grep waha | awk '{print $1}') 2>/dev/null || true

# Remove images
echo "🗑️  Removing old Waha images..."
docker rmi devlikeapro/waha:noweb 2>/dev/null || true
docker rmi devlikeapro/waha:latest 2>/dev/null || true

# Clean volumes
echo "🗑️  Removing Waha data volume..."
docker volume rm artinsmartrealty_waha_data 2>/dev/null || true

# Pull latest code
echo "📥 Pulling latest docker-compose.yml..."
git pull origin main

# Pull fresh image
echo "📦 Pulling fresh Waha image..."
docker-compose pull waha

# Start Waha
echo "🚀 Starting Waha with new configuration..."
docker-compose up -d waha

# Wait
echo "⏳ Waiting 20 seconds for Waha to initialize..."
sleep 20

# Check if container is running
echo ""
echo "🔍 Checking container status..."
docker-compose ps waha

# Check logs
echo ""
echo "📋 Recent logs:"
docker-compose logs --tail=30 waha

# Test connection
echo ""
echo "🧪 Testing connection..."
curl -v http://localhost:3001/api/server/health 2>&1 | grep -E "HTTP|Unauthorized|200 OK" || echo "Connection test completed"

echo ""
echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "🔧 Environment Variable Check:"
docker-compose exec waha env | grep -E "WAHA|WHATSAPP" || echo "Cannot access container environment"
echo ""
echo "📱 Try this command to start session:"
echo 'curl -X POST http://localhost:3001/api/sessions/start -H "Content-Type: application/json" -d '"'"'{"name":"default"}'"'"''
echo ""
