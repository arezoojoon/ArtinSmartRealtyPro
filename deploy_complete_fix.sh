#!/bin/bash

# 🚀 اسکریپت دیپلوی فیکس کامل بات
# این اسکریپت تمام تغییرات رو به production deploy میکنه

set -e  # Exit on error

echo "========================================="
echo "🚀 شروع دیپلوی فیکس کامل بات"
echo "========================================="
echo ""

# رنگ‌ها برای output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. چک کردن اینکه داخل پروژه هستیم
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ خطا: فایل docker-compose.yml پیدا نشد!${NC}"
    echo "لطفاً از داخل پوشه /opt/ArtinSmartRealtyPro اجرا کنید"
    exit 1
fi

echo -e "${GREEN}✅ داخل پوشه پروژه هستیم${NC}"

# 2. Pull کردن آخرین تغییرات
echo ""
echo "📥 در حال pull کردن تغییرات از GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ خطا در git pull${NC}"
    echo "ممکنه تغییرات local داشته باشید که conflict داره"
    echo "دستور manual: git stash && git pull origin main"
    exit 1
fi

echo -e "${GREEN}✅ تغییرات pull شد${NC}"

# 3. چک کردن اینکه brain.py تغییر کرده
if git diff HEAD@{1} HEAD --name-only | grep -q "backend/brain.py"; then
    echo -e "${GREEN}✅ brain.py تغییر کرده (فیکس‌ها اعمال شده)${NC}"
else
    echo -e "${YELLOW}⚠️  brain.py تغییری نکرده - ممکنه commit نشده باشه${NC}"
fi

# 4. Backup گرفتن از database (اختیاری)
echo ""
read -p "❓ میخوای از database backup بگیری؟ (y/n): " BACKUP_CHOICE
if [ "$BACKUP_CHOICE" = "y" ]; then
    echo "📦 در حال backup از database..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    docker-compose exec -T postgres pg_dump -U postgres artin_smart_realty > "$BACKUP_FILE"
    echo -e "${GREEN}✅ Backup ذخیره شد: $BACKUP_FILE${NC}"
fi

# 5. Rebuild کردن backend
echo ""
echo "🔨 در حال rebuild کردن backend..."
docker-compose up -d --build backend

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ خطا در rebuild backend${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend rebuild شد${NC}"

# 6. منتظر موندن تا backend بالا بیاد
echo ""
echo "⏳ منتظر می‌مونیم تا backend بالا بیاد (15 ثانیه)..."
sleep 15

# 7. چک کردن health backend
echo ""
echo "🏥 چک کردن سلامت backend..."
if docker-compose ps backend | grep -q "Up"; then
    echo -e "${GREEN}✅ Backend در حال اجراست${NC}"
else
    echo -e "${RED}❌ Backend اجرا نشده!${NC}"
    echo "Logs:"
    docker-compose logs --tail=50 backend
    exit 1
fi

# 8. نمایش آخرین logs
echo ""
echo "📋 آخرین logs backend:"
echo "========================================="
docker-compose logs --tail=30 backend | grep -E "(ERROR|WARNING|🏠|✅|❌|INFO)"
echo "========================================="

# 9. چک کردن error‌ها
ERROR_COUNT=$(docker-compose logs --tail=100 backend | grep -c "ERROR" || true)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $ERROR_COUNT خطا در logs پیدا شد${NC}"
    echo "برای دیدن جزئیات: docker-compose logs -f backend"
else
    echo -e "${GREEN}✅ هیچ خطایی در logs نیست${NC}"
fi

# 10. تست ساده
echo ""
echo "🧪 تست ساده:"
echo "----------------------------------------"
echo "1. برو به بات تلگرام"
echo "2. دستور /start بزن"
echo "3. اسمت رو بده"
echo "4. یکی از دکمه‌ها (سرمایه‌گذاری) رو بزن"
echo "5. باید املاک واقعی با عکس ببینی"
echo "6. شماره رو share کن"
echo "7. باید لینک Calendly ببینی، نه 'وقت خالی نداریم'"
echo "----------------------------------------"

# 11. نمایش دستورات مفید
echo ""
echo "📚 دستورات مفید:"
echo "----------------------------------------"
echo "• مشاهده logs زنده:    docker-compose logs -f backend"
echo "• Restart backend:      docker-compose restart backend"
echo "• چک کردن status:      docker-compose ps"
echo "• ورود به container:    docker-compose exec backend bash"
echo "• چک کردن database:    docker-compose exec postgres psql -U postgres artin_smart_realty -c 'SELECT COUNT(*) FROM tenant_properties;'"
echo "----------------------------------------"

echo ""
echo "========================================="
echo -e "${GREEN}🎉 دیپلوی با موفقیت انجام شد!${NC}"
echo "========================================="
echo ""
echo "حالا برو بات رو تست کن! 🚀"
echo ""
