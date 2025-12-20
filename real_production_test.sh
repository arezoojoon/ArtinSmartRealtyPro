#!/bin/bash
# Real Production Testing Script - No Fake Reports!
# این اسکریپت واقعاً همه چیز را تست می‌کند

set -e

echo "🔍 REAL PRODUCTION TESTING - No Fake Checks!"
echo "=============================================="
echo ""

# 1. بررسی واقعی container ها
echo "📊 Real Container Status:"
docker-compose ps
echo ""

# 2. بررسی واقعی logs برای ERROR
echo "🚨 Checking for REAL ERRORS in last 100 lines:"
docker-compose logs --tail=100 backend | grep -i "error\|exception\|failed\|traceback" || echo "✅ No errors in backend"
docker-compose logs --tail=100 router | grep -i "error\|exception\|failed\|traceback" || echo "✅ No errors in router"
echo ""

# 3. تست واقعی API endpoints
echo "🧪 Testing REAL API Endpoints:"
echo "1. Health endpoint:"
curl -f http://localhost:8000/health || echo "❌ Backend health FAILED"
echo ""

echo "2. Router health:"
curl -f http://localhost:8001/health || echo "❌ Router health FAILED"
echo ""

echo "3. Login test with real credentials:"
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@artinsmartagent.com","password":"SuperARTIN2588357!"}' || echo "❌ Login FAILED"
echo ""

# 4. بررسی واقعی دیتابیس
echo "📊 Real Database Check:"
docker-compose exec -T db psql -U postgres -d artinrealty_db -c "SELECT COUNT(*) as tenant_count FROM tenants;" || echo "❌ Database query FAILED"
docker-compose exec -T db psql -U postgres -d artinrealty_db -c "SELECT COUNT(*) as lead_count FROM leads;" || echo "❌ Database query FAILED"
echo ""

# 5. بررسی واقعی Redis
echo "🔴 Real Redis Check:"
docker-compose exec -T redis redis-cli ping || echo "❌ Redis FAILED"
docker-compose exec -T redis redis-cli -n 0 DBSIZE || echo "❌ Redis DB 0 FAILED"
docker-compose exec -T redis redis-cli -n 1 DBSIZE || echo "❌ Redis DB 1 FAILED"
echo ""

# 6. بررسی واقعی Telegram bots
echo "🤖 Real Telegram Bot Status:"
docker-compose logs --tail=50 backend | grep -i "telegram" || echo "⚠️ No telegram logs found"
echo ""

# 7. بررسی واقعی WhatsApp
echo "📱 Real WhatsApp Status:"
docker-compose logs --tail=50 waha || echo "⚠️ WAHA logs check"
echo ""

# 8. تست واقعی Router API
echo "🔗 Testing Real Router API:"
curl -X POST http://localhost:8001/router/generate-link \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": 1, "vertical": "realty", "gateway_number": "971557357753"}' || echo "❌ Router generate-link FAILED"
echo ""

# 9. بررسی منابع واقعی سرور
echo "💻 Real Server Resources:"
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" || echo "⚠️ CPU check failed"
echo ""
echo "Memory:"
free -h || echo "⚠️ Memory check failed"
echo ""
echo "Disk:"
df -h / || echo "⚠️ Disk check failed"
echo ""

# 10. بررسی network
echo "🌐 Real Network Check:"
netstat -tlnp | grep -E "8000|8001|3000|5432|6379" || echo "⚠️ Port check"
echo ""

echo "=============================================="
echo "✅ REAL PRODUCTION TESTING COMPLETE"
echo "Any failures above are REAL issues that need fixing!"
