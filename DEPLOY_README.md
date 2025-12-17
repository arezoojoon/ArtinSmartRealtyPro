# 🎯 راهنمای کامل دیپلوی فیکس بات

## مشکلات حل شده ✅

### 1. حلقه بی‌نهایت شماره تلفن ❌ → ✅
**قبل:** بات صد بار شماره می‌پرسید  
**بعد:** فقط یک بار می‌پرسه

### 2. نمایش املاک ❌ → ✅
**قبل:** فقط متن جنریک  
**بعد:** املاک واقعی از database با عکس + ROI + قیمت

### 3. رزرو مشاوره ❌ → ✅
**قبل:** "وقت خالی نداریم"  
**بعد:** لینک Calendly + شماره تماس + واتساپ

---

## گام‌های دیپلوی

### گام 0: Commit کردن تغییرات (اگه local هستید)

```bash
git add backend/brain.py
git commit -m "Fix: Remove HARD_GATE loop + Add real property display + Calendly integration"
git push origin main
```

### گام 1: SSH به سرور

```bash
ssh root@88.99.45.159
cd /opt/ArtinSmartRealtyPro
```

### گام 2: اجرای اسکریپت خودکار 🚀

```bash
chmod +x deploy_complete_fix.sh
./deploy_complete_fix.sh
```

این اسکریپت:
- ✅ تغییرات رو pull می‌کنه
- ✅ Backup از database می‌گیره (اختیاری)
- ✅ Backend رو rebuild می‌کنه
- ✅ Health check انجام میده
- ✅ Logs رو نمایش میده

### گام 3: اضافه کردن املاک نمونه (اگه database خالیه)

```bash
docker-compose exec postgres psql -U postgres artin_smart_realty < add_sample_properties.sql
```

این دستور 5 ملک نمونه اضافه می‌کنه:
- 🏢 آپارتمان لوکس دبی مارینا (ویزای طلایی)
- 💰 استودیو سرمایه‌گذاری (ROI 9.2%)
- 🏡 ویلا 5 خوابه با استخر
- 🏗️ پیش‌فروش (payment plan)
- 👑 پنت‌هاوس Palm Jumeirah

---

## تست دستی

1. **شروع بات:**
   ```
   /start
   ```

2. **انتخاب زبان:**
   ```
   فارسی
   ```

3. **دادن اسم:**
   ```
   ارزو
   ```

4. **انتخاب هدف:**
   ```
   [کلیک روی: سرمایه‌گذاری]
   ```

5. **انتظار:** باید 5 ملک با عکس ببینی:
   ```
   🏠 5 ملک مناسب برای شما:
   
   1. Marina Heights...
      💰 2,500,000 AED
      📈 ROI: 8.5%
      [عکس ملک]
   ```

6. **درخواست ملک:**
   ```
   ملک بهم نشون بده
   ```
   یا
   ```
   پیش خرید میخوام
   ```

7. **Share کردن شماره:**
   ```
   [کلیک روی دکمه Share Contact]
   ```

8. **رزرو مشاوره:**
   ```
   [کلیک روی: 📅 رزرو مشاوره]
   ```
   
   باید ببینی:
   ```
   🎉 عالیه! بیایید جلسه مشاوره رایگان‌تون رو تنظیم کنیم.
   
   1️⃣ آنلاین: https://calendly.com/...
   2️⃣ تماس: +971 50 503 7158
   3️⃣ واتساپ: https://wa.me/...
   ```

---

## دستورات مفید

### مشاهده logs زنده
```bash
docker-compose logs -f backend
```

### فیلتر error‌ها
```bash
docker-compose logs backend | grep ERROR
```

### فیلتر موفقیت‌ها
```bash
docker-compose logs backend | grep "✅"
```

### چک کردن املاک در database
```bash
docker-compose exec postgres psql -U postgres artin_smart_realty -c "
SELECT name, price, expected_roi, is_available 
FROM tenant_properties 
WHERE tenant_id = 1;
"
```

### Restart backend
```bash
docker-compose restart backend
```

### ورود به backend container
```bash
docker-compose exec backend bash
```

---

## عیب‌یابی

### ❌ مشکل: بات همچنان شماره می‌پرسه

**راه‌حل:**
1. چک کن که تغییرات pull شده:
   ```bash
   git log --oneline -5
   ```
2. چک کن backend rebuild شده:
   ```bash
   docker-compose ps backend
   ```
3. مشاهده logs:
   ```bash
   docker-compose logs backend | grep HARD_GATE
   ```

### ❌ مشکل: املاک نمایش داده نمیشه

**راه‌حل:**
1. چک کن املاک در database هست:
   ```bash
   docker-compose exec postgres psql -U postgres artin_smart_realty -c "SELECT COUNT(*) FROM tenant_properties WHERE tenant_id = 1;"
   ```
2. اگه 0 بود، اضافه کن:
   ```bash
   docker-compose exec postgres psql -U postgres artin_smart_realty < add_sample_properties.sql
   ```

### ❌ مشکل: Error در logs

**راه‌حل:**
1. مشاهده آخرین 100 خط:
   ```bash
   docker-compose logs --tail=100 backend
   ```
2. اگه import error بود:
   ```bash
   docker-compose restart backend
   ```

### ❌ مشکل: Database connection failed

**راه‌حل:**
1. چک کن postgres در حال اجراست:
   ```bash
   docker-compose ps postgres
   ```
2. Restart کن:
   ```bash
   docker-compose restart postgres
   sleep 5
   docker-compose restart backend
   ```

---

## Rollback (اگه چیزی خراب شد)

```bash
# برگشت به commit قبلی
git log --oneline -5  # پیدا کردن hash قبلی
git checkout <hash_قبلی>
docker-compose up -d --build backend
```

یا:

```bash
# Restore از backup
docker-compose exec postgres psql -U postgres artin_smart_realty < backup_YYYYMMDD_HHMMSS.sql
```

---

## نکات مهم

1. **قبل از دیپلوی:**
   - ✅ Commit تغییرات
   - ✅ Backup از database
   - ✅ چک کردن اینکه سرور فضا داره

2. **بعد از دیپلوی:**
   - ✅ تست فلو کامل
   - ✅ چک کردن logs برای error
   - ✅ تست با کاربر واقعی

3. **اختیاری اما توصیه میشه:**
   - 🔑 گرفتن Gemini API key جدید (برای voice)
   - 📅 ساخت حساب Calendly و عوض کردن لینک
   - 📸 اضافه کردن عکس‌های واقعی املاک

---

## تماس در صورت مشکل

اگه مشکلی پیش اومد:
1. Screenshot از error بگیر
2. آخرین logs رو کپی کن:
   ```bash
   docker-compose logs --tail=50 backend > error_logs.txt
   ```
3. بفرست برای بررسی

---

**آخرین بروزرسانی:** 2025-01-14  
**نسخه:** 2.0 - Complete Fix  
**وضعیت:** ✅ آماده دیپلوی
