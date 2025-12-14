# 🧪 اسکریپت تست کامل Conversation Flow

## وضعیت فعلی
✅ **Database:** 14 properties added for tenant_id=2  
✅ **Backend:** Container running  
⏳ **Code:** Need to verify latest commit (599091c) is deployed

## دستورات بررسی Pre-Test

### 1. تایید نسخه کد در container
```bash
# روی سرور اجرا کنید:
docker exec artinrealty-backend git log --oneline -1
```

**خروجی مورد انتظار:**
```
599091c CRITICAL FIX: تشخیص yes/no متنی - رفع باگ loop بی‌نهایت financing
```

**اگر commit قدیمی‌تر نشان داد:**
```bash
cd /opt/ArtinSmartRealtyPro
git pull origin main
cd ArtinSmartRealty
git pull origin main
docker-compose build --no-cache backend
docker-compose up -d backend
```

### 2. بررسی کد fix در container
```bash
docker exec artinrealty-backend grep -n "AFFIRMATIVE RESPONSE detected" backend/brain.py
```

**خروجی مورد انتظار:**
```
3460:                logger.info(f"✅ AFFIRMATIVE RESPONSE detected from lead {lead.id} - Triggering property presentation with photos+PDFs")
```

**اگر "No such file" یا خط پیدا نشد:** کد جدید deploy نشده، باید rebuild کنید.

### 3. تایید properties در database
```bash
docker exec -i artinrealty-db psql -U postgres -d artinrealty -c "
SELECT COUNT(*), tenant_id 
FROM tenant_properties 
WHERE tenant_id IN (1,2) 
GROUP BY tenant_id;
"
```

**خروجی مورد انتظار:**
```
 count | tenant_id 
-------+-----------
     1 |         1
    14 |         2
```

## 🎯 تست اصلی: Conversation Flow

### تست 1: Happy Path (مسیر موفق)

**مراحل دقیق:**

1. **باز کردن Telegram** و سرچ: `@samanahmadi_Bot`

2. **شروع مکالمه:**
   ```
   /start
   ```
   
   **پاسخ ربات:**
   ```
   خوشحالم که با شما آشنا شدم! 👋
   اسم شما چیه؟
   ```

3. **وارد کردن نام:**
   ```
   Arezoo
   ```
   
   **پاسخ ربات:**
   ```
   Arezoo عزیز، خوشحالم آشنا شدیم! 🎯
   ...
   📱 لطفاً شماره تلفنتون رو به اشتراک بذارید
   ```

4. **اشتراک شماره:**
   - کلیک دکمه "Share Contact" زیر پیام
   - یا تایپ: `+989177105840`
   
   **پاسخ ربات:**
   ```
   انتخاب عالی! 🎯
   قبل از ارسال گزارش کامل، بذارید گزینه‌های تامین مالی رو توضیح بدم...
   می‌خواهید ماشین‌حساب تامین مالی شخصی‌سازی شده؟
   ```

5. **تایپ کردن "yes"** (نه کلیک دکمه!):
   ```
   yes
   ```
   
   **یا به فارسی:**
   ```
   بله
   ```

6. **نتیجه مورد انتظار (CRITICAL TEST):**

   ✅ **پیام تایید:**
   ```
   عالی! بذار براتون املاک رو با عکس و تحلیل ROI کامل بفرستم...
   ```
   
   ✅ **Property 1: Sky Gardens - Marina Heights**
   - 📸 Media Group با 3 عکس (از Unsplash)
   - 📝 Caption کامل:
     ```
     🏠 Sky Gardens - Marina Heights
     📍 Dubai Marina
     💰 AED 2,800,000
     🛏️ 3 BR | 🚿 2 BA | 📐 1,650 sq ft
     
     ✨ Features:
     • Marina view panoramic windows
     • Premium finishing
     • Smart home automation
     ...
     
     🛂 Golden Visa Eligible
     📊 ROI: 7.5% annually
     ```
   - 📄 PDF ROI Report (اگر brochure_pdf موجود باشد)
   
   ⏱️ **5 ثانیه صبر**
   
   ✅ **Property 2: Arabian Ranches Luxury Villa**
   - 📸 Media Group با 4 عکس
   - 📝 Caption کامل
   - 📄 PDF
   
   ⏱️ **5 ثانیه صبر**
   
   ✅ **Property 3: Business Bay Studio**
   - 📸 Media Group
   - 📝 Caption
   - 📄 PDF

### تست 2: Negative Response

**مرحله 5 را تغییر دهید:**
```
no
```

**یا:**
```
نه
```

**نتیجه مورد انتظار:**
```
مشکلی نیست! سوالی درباره این ملک‌ها یا املاک دبی دارید؟ 😊
```

✅ State تغییر به ENGAGEMENT  
✅ کاربر می‌تواند سوال بپرسد

### تست 3: Button Click (روش قدیمی)

**مرحله 5:**
- کلیک دکمه "✅ بله" به جای تایپ

**نتیجه مورد انتظار:**
- باید همان نتیجه تست 1 را بدهد
- این تست تایید می‌کند که fix جدید روش قدیمی را خراب نکرده

## 📊 Monitoring در زمان تست

**در یک terminal جداگانه روی سرور:**

```bash
docker-compose logs -f backend | grep -E "lead.*Arezoo|AFFIRMATIVE|current_properties|property_presenter|VALUE_PROPOSITION"
```

**لاگ‌های مورد انتظار بعد از تایپ "yes":**

```
INFO: 📝 VALUE_PROPOSITION text input from lead 123: 'yes'
INFO: ✅ AFFIRMATIVE RESPONSE detected from lead 123 - Triggering property presentation with photos+PDFs
INFO: ✅ Found 3 properties in database for lead 123
INFO: 🏠 Brain has 3 properties to present - using property_presenter
INFO: 📸 Sending Media Group for property 'Sky Gardens - Marina Heights' (3 images)
INFO: ⏱️ Waiting 5 seconds before next property...
INFO: 📸 Sending Media Group for property 'Arabian Ranches Luxury Villa' (4 images)
INFO: ⏱️ Waiting 5 seconds before next property...
INFO: 📸 Sending Media Group for property 'Business Bay Studio' (2 images)
INFO: ✅ Professional property presentation complete for lead 123
```

**اگر این لاگ‌ها ظاهر نشد:**
- یعنی کد جدید deploy نشده
- یا مشکل در database query است

## ❌ سناریوهای خطا و Troubleshooting

### خطا 1: "I don't have exact properties in my system"

**علت:** Query به database نتیجه نداد  
**بررسی:**
```sql
docker exec -i artinrealty-db psql -U postgres -d artinrealty -c "
SELECT id, name, tenant_id, is_active 
FROM tenant_properties 
WHERE tenant_id = 2 AND is_active = true;
"
```

**راه‌حل:**
- اگر `is_active = false`: `UPDATE tenant_properties SET is_active = true WHERE tenant_id = 2;`
- اگر `tenant_id` اشتباه: بررسی کنید ربات به کدام tenant متصل است

### خطا 2: ربات همچنان financing را تکرار می‌کند

**علت:** کد جدید deploy نشده  
**راه‌حل:**
```bash
cd /opt/ArtinSmartRealtyPro/ArtinSmartRealty
git log --oneline -1  # باید 599091c نشان دهد

# اگر commit قدیمی‌تر بود:
git pull origin main
cd ..
docker-compose build --no-cache backend
docker-compose up -d backend
```

### خطا 3: عکس‌ها نشان داده نمی‌شوند

**علت:** `image_urls` خالی یا URLهای معتبر نیست  
**بررسی:**
```sql
docker exec -i artinrealty-db psql -U postgres -d artinrealty -c "
SELECT id, name, image_urls 
FROM tenant_properties 
WHERE tenant_id = 2 
LIMIT 3;
"
```

**راه‌حل:**
- اگر `image_urls = []` یا `null`: املاک sample ما URLهای Unsplash دارند، باید کار کنند
- اگر مشکل داشت: یک property با smart upload از dashboard آپلود کنید

### خطا 4: PDF فرستاده نمی‌شود

**علت:** `brochure_pdf` NULL است  
**توضیح:** این normal است برای sample properties - ربات به جای آن ROI PDF generate می‌کند
**بررسی:** در لاگ باید ببینید:
```
INFO: 📄 Generating ROI PDF for property 'Sky Gardens'...
INFO: ✅ ROI PDF generated and sent
```

## ✅ Success Criteria

**تست موفق است اگر:**

1. ✅ کاربر "yes" یا "بله" تایپ می‌کند
2. ✅ ربات پیام "عالی! بذار براتون املاک رو بفرستم..." می‌فرستد
3. ✅ 3 property به صورت Media Group با عکس فرستاده می‌شوند
4. ✅ هر property شامل caption کامل است (قیمت، مشخصات، features)
5. ✅ بین properties فاصله 5 ثانیه است
6. ✅ اگر برای property دوم "no" بنویسید، state به ENGAGEMENT تغییر می‌کند

**اگر همه موارد بالا OK بود:**
🎉 **FIX SUCCESSFUL!** باگ حلقه بی‌نهایت رفع شده است.

## 🔄 تست مجدد (Re-test)

برای اطمینان کامل، تست را با یک user جدید تکرار کنید:

```
/start
[نام دیگری وارد کنید]
[شماره اشتراک]
yes
```

باید همان نتیجه را بدهد.

## 📝 گزارش نتایج

بعد از تست، این اطلاعات را بررسی کنید:

- ✅ آیا property ها فرستاده شدند؟ (بله/خیر)
- ✅ چند property فرستاده شد؟ (باید 3 باشد)
- ✅ آیا عکس‌ها نمایش داده شدند؟ (بله/خیر)
- ✅ آیا PDF فرستاده شد؟ (بله/خیر)
- ✅ آیا "no" به ENGAGEMENT منتقل شد؟ (بله/خیر)
- ❌ آیا باگ loop همچنان هست؟ (بله/خیر)

اگر هر کدام Failed بود، لاگ کامل را با دستور زیر ذخیره کنید:
```bash
docker-compose logs backend > /tmp/backend_test_$(date +%Y%m%d_%H%M%S).log
```

---

**آماده برای تست واقعی؟** ✅  
**Monitoring فعال؟** ✅  
**Properties در database؟** ✅  

**▶️ برو Telegram و @samanahmadi_Bot رو تست کن!**
