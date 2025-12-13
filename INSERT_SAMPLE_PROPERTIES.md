# 🏠 راهنمای اضافه کردن املاک نمونه به دیتابیس

## ⚠️ مشکل فعلی
بات میگه "عکس‌ها رو فرستادم!" ولی هیچی نمیفرسته چون دیتابیس خالیه.

## ✅ راه حل (روی سرور production)

### روش 1: اجرای مستقیم SQL (توصیه می‌شود)

```bash
# روی سرور SSH کرده‌اید
cd /opt/ArtinSmartRealtyPro

# Check if database name is correct
docker-compose exec db psql -U postgres -l

# Run the SQL file
docker-compose exec -T db psql -U postgres artin_smart_realty < add_sample_properties.sql

# اگر خطای "database does not exist" گرفتید:
docker-compose exec -T db psql -U postgres artinrealty < add_sample_properties.sql
```

**توجه:** استفاده از `-T` (disable pseudo-TTY) برای اجرای SQL از فایل ضروریه.

### روش 2: Copy کردن فایل به container و اجرا

```bash
# Copy SQL file into container
docker cp add_sample_properties.sql artinrealty-db:/tmp/sample.sql

# Execute inside container
docker-compose exec db psql -U postgres artin_smart_realty -f /tmp/sample.sql

# یا با database name دیگه:
docker-compose exec db psql -U postgres artinrealty -f /tmp/sample.sql
```

### روش 3: اجرای دستی یک به یک (اگر روش‌های بالا کار نکرد)

```bash
# Connect to database
docker-compose exec db psql -U postgres artin_smart_realty

# حالا SQL commands را یک به یک paste کنید از add_sample_properties.sql
```

---

## 🔍 چک کردن موفقیت‌آمیز بودن

```bash
# Check if properties were inserted
docker-compose exec db psql -U postgres artin_smart_realty -c "SELECT COUNT(*) FROM tenant_properties;"

# باید 5 ملک برگردونه
# Expected output: count = 5

# Show all properties
docker-compose exec db psql -U postgres artin_smart_realty -c "SELECT id, name, price, location FROM tenant_properties ORDER BY is_featured DESC;"
```

---

## 📋 املاک نمونه‌ای که اضافه می‌شه:

1. **Marina Heights Luxury Tower** - 2,500,000 AED - 3BR - Golden Visa
2. **Investment Studio - Downtown** - 850,000 AED - Studio - 9.2% ROI
3. **Luxury Villa with Private Pool** - 4,200,000 AED - 5BR - Golden Visa
4. **Sky Gardens - Off-Plan** - 1,200,000 AED - 2BR - 10.5% ROI
5. **Exclusive Penthouse - Palm Jumeirah** - 8,500,000 AED - 4BR - Golden Visa

---

## 🎯 تست کردن بات بعد از اضافه کردن

1. به بات تلگرام برو
2. بگو: `/start`
3. بگو: `عکس ملک بده`
4. بات باید **واقعاً** 5 تا عکس + جزئیات املاک رو بفرسته

---

## 🐛 اگه باز هم عکس نفرستاد

```bash
# Check bot logs
docker-compose logs --tail=100 backend | grep -E "(property|عکس|Found.*properties)"

# باید این خط رو ببینی:
# ✅ Found 5 real properties in database

# اگه این خط رو دیدی:
# ⚠️ No real properties found in database for lead X
# یعنی SQL اجرا نشده یا database name اشتباهه
```

---

## 💡 Database Name های ممکن

ممکنه database name یکی از اینها باشه:
- `artinrealty`
- `artin_smart_realty`
- `artinsmartrealty`

برای چک کردن:

```bash
docker-compose exec db psql -U postgres -c "\l"
```

از اون لیست، database درست رو پیدا کن و دستور رو با اون نام اجرا کن.
