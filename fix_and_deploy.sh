#!/bin/bash
# کپی کنید و در سرور اجرا کنید

# رنگ‌ها
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 حل کردن conflict و deployment...${NC}"

# مرحله 1: بررسی تغییرات محلی
echo -e "${BLUE}📋 تغییرات محلی:${NC}"
git diff backend/brain.py | head -20

# مرحله 2: Backup تغییرات محلی
echo -e "${BLUE}💾 Backup از تغییرات محلی...${NC}"
cp backend/brain.py backend/brain.py.backup.$(date +%Y%m%d_%H%M%S)

# مرحله 3: Stash تغییرات
echo -e "${BLUE}📦 Stash کردن تغییرات...${NC}"
git stash push -m "Local changes before deployment $(date)"

# مرحله 4: Pull کد جدید
echo -e "${BLUE}📥 دریافت کد جدید...${NC}"
git pull origin main

# مرحله 5: بررسی که pull موفق شد
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ کد جدید دریافت شد${NC}"
else
    echo -e "${RED}❌ Pull ناموفق بود${NC}"
    exit 1
fi

# مرحله 6: لیست backup ها
echo -e "${BLUE}📄 Backup های موجود:${NC}"
ls -lh backend/brain.py.backup.* 2>/dev/null

# مرحله 7: شروع deployment
echo -e "${BLUE}🚀 شروع deployment...${NC}"

docker-compose down
docker-compose build --no-cache backend router
docker-compose up -d db redis
sleep 15
docker-compose run --rm backend alembic upgrade head
docker-compose up -d

# مرحله 8: Health checks
echo -e "${BLUE}🏥 Health checks...${NC}"
sleep 10

curl -s http://localhost:8000/health && echo -e "${GREEN}✅ Backend healthy${NC}" || echo -e "${RED}❌ Backend failed${NC}"
curl -s http://localhost:8001/health && echo -e "${GREEN}✅ Router healthy${NC}" || echo -e "${RED}❌ Router failed${NC}"

# مرحله 9: وضعیت container ها
echo -e "${BLUE}📊 Container status:${NC}"
docker-compose ps

echo -e "${GREEN}✅ Deployment کامل شد!${NC}"
echo ""
echo -e "${BLUE}📝 دستورات مفید:${NC}"
echo "  - مشاهده logs: docker-compose logs -f backend"
echo "  - بررسی stash: git stash list"
echo "  - بازگرداندن backup: cp backend/brain.py.backup.* backend/brain.py"
