#!/bin/bash
# Quick Deploy - فقط دستورات اصلی
# این را روی سرور اجرا کن

cd /opt/ArtinSmartRealty

echo "🔄 Deploying fixes..."

# دریافت آخرین کد
git pull origin main

# پاک کردن Docker cache
docker-compose down
docker system prune -f

# ساخت و اجرای مجدد
docker-compose build --no-cache
docker-compose up -d

# صبر برای آماده شدن
sleep 15

# نمایش وضعیت
echo ""
echo "✅ Deployed!"
echo ""
docker-compose ps
echo ""
echo "Test: https://realty.artinsmartagent.com/"
