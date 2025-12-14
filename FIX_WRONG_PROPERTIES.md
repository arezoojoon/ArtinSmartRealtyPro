# 🚨 فوری: پاک کردن املاک اشتباه و اضافه کردن املاک درست

## مشکل فعلی

بات 3 تا ملک نشون میده که یکیش اشتباهه:
- ✅ Sky Gardens - Off-Plan (1.2M AED) - درسته
- ✅ Marina Heights (2.5M AED) - درسته  
- ❌ **binghatti-flare-digital-brochure** (50 AED, 7 sqft) - این یک PDF برشوره نه ملک!

## راه حل سریع (روی سرور production)

### گام 1: حذف املاک اشتباه

```bash
# SSH to server
ssh root@88.99.45.159
cd /opt/ArtinSmartRealtyPro

# Check current properties
docker-compose exec db psql -U postgres artinrealty -c "SELECT id, name, price, area_sqft FROM tenant_properties WHERE tenant_id=1;"

# Delete the wrong PDF "property"
docker-compose exec db psql -U postgres artinrealty -c "DELETE FROM tenant_properties WHERE name LIKE '%binghatti%' OR price < 100000;"

# Verify deletion
docker-compose exec db psql -U postgres artinrealty -c "SELECT COUNT(*) FROM tenant_properties WHERE tenant_id=1;"
```

### گام 2: اضافه کردن 5 ملک نمونه

```bash
# Pull latest code (includes sample properties SQL)
git pull origin main

# Insert sample properties
docker-compose exec -T db psql -U postgres artinrealty < add_sample_properties.sql

# Verify 5 properties inserted
docker-compose exec db psql -U postgres artinrealty -c "SELECT id, name, price, location, is_featured FROM tenant_properties WHERE tenant_id=1 ORDER BY is_featured DESC, price ASC;"
```

**باید 5 ملک ببینی:**
1. Marina Heights Luxury Tower - 2,500,000 AED - Dubai Marina
2. Investment Studio - Downtown - 850,000 AED - Downtown Dubai  
3. Luxury Villa with Private Pool - 4,200,000 AED - Arabian Ranches
4. Sky Gardens - Off-Plan - 1,200,000 AED - Business Bay
5. Exclusive Penthouse - Palm Jumeirah - 8,500,000 AED - Palm Jumeirah

### گام 3: Restart Backend

```bash
docker-compose restart backend

# Wait 10 seconds
sleep 10

# Check logs
docker-compose logs --tail=30 backend | grep -E "(property|Found|✅)"
```

---

## تست بات بعد از Fix

1. `/start`
2. `arezoo`
3. Share contact
4. بگو: `show me properties` یا `عکس ملک`
5. **باید 5 تا عکس با این املاک بیاد:**
   - Marina Heights (3BR, 2.5M, Golden Visa)
   - Investment Studio (Studio, 850K, 9.2% ROI)
   - Luxury Villa (5BR, 4.2M, Pool)
   - Sky Gardens (2BR, 1.2M, Off-Plan, 10.5% ROI)
   - Palm Penthouse (4BR, 8.5M)

---

## اگه باز هم برشور PDF نشون داد

```bash
# Find and delete ALL non-property items
docker-compose exec db psql -U postgres artinrealty

-- In psql:
SELECT id, name, property_type, price, area_sqft 
FROM tenant_properties 
WHERE tenant_id = 1;

-- Delete anything suspicious:
DELETE FROM tenant_properties 
WHERE name LIKE '%brochure%' 
   OR name LIKE '%pdf%'
   OR price < 100000
   OR area_sqft < 100;

-- Exit
\q
```

بعد دوباره املاک نمونه رو اضافه کن (گام 2).

---

## چک سریع دیتابیس

```bash
# Count properties
docker-compose exec db psql -U postgres artinrealty -c "SELECT COUNT(*) FROM tenant_properties WHERE tenant_id=1 AND is_available=true;"

# Expected: 5

# Show all property names
docker-compose exec db psql -U postgres artinrealty -c "SELECT name, price, property_type FROM tenant_properties WHERE tenant_id=1;"
```

---

## نتیجه نهایی

بعد از این مراحل:
- ✅ بات 5 تا ملک واقعی نشون میده
- ✅ همه ملک‌ها عکس دارن
- ✅ ROI و قیمت‌ها درست هستن
- ✅ دیگه PDF برشور به عنوان ملک نمایش داده نمیشه
