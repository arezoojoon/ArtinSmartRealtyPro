# 🚨 URGENT: رفع باگ حلقه بی‌نهایت در ارسال املاک

## مشکل (Problem)
ربات وقتی کاربر "yes" می‌نویسد (به جای کلیک دکمه)، در حلقه بی‌نهایت می‌افتاد و همان پیام financing را تکرار می‌کرد. هیچ وقت املاک با عکس و PDF فرستاده نمی‌شدند.

**مثال از لاگ شما:**
```
User: yes
Bot: می‌خواهید ماشین‌حساب تامین مالی شخصی‌سازی شده؟
User: yes
Bot: می‌خواهید ماشین‌حساب تامین مالی شخصی‌سازی شده؟
[تکرار بی‌نهایت...]
```

## راه‌حل (Solution)
افزودن تشخیص متنی `yes/بله/نعم/да` و `no/نه/لا/нет` در بالاترین اولویت `VALUE_PROPOSITION` state.

### تغییرات کد (Code Changes)

**فایل:** `backend/brain.py`  
**تابع:** `_handle_value_proposition()`  
**خطوط:** 3436-3570 (115 خط اضافه شده)

**منطق جدید:**
1. ✅ **تشخیص Affirmative:** اگر کاربر `yes/yeah/sure/ok/بله/آره/باشه/نعم/да` بنویسد:
   - Query به `TenantProperty` با فیلتر `tenant_id`, `budget`, `property_type`
   - تبدیل نتایج به dict
   - **SET** `brain.current_properties` (این trigger می‌کند property_presenter)
   - برگرداندن پیام تایید: "Perfect! Let me send you properties with photos..."
   
2. ✅ **تشخیص Negative:** اگر کاربر `no/nope/نه/لا/нет` بنویسد:
   - انتقال به `ENGAGEMENT` state (حالت سوال و جواب)
   - پیام: "No problem! Do you have any questions?"

3. ✅ **Integration با property_presenter:**
   - در `telegram_bot.py` خط 706-716، بعد از ارسال response، چک می‌کند آیا `brain.current_properties` است
   - اگر هست، `present_all_properties()` را صدا می‌زند که:
     - املاک را با **Media Group** (تا 10 عکس) می‌فرستد
     - **PDF ROI report** اگر `brochure_pdf` باشد می‌فرستد
     - اگر PDF نباشد، با `roi_engine.py` یک PDF حرفه‌ای generate می‌کند

## دستورات Deployment (بدون پایین رفتن سرویس)

### گام 1: Pull کد جدید
```bash
cd /opt/ArtinSmartRealtyPro
git pull origin main
cd ArtinSmartRealty
git pull origin main
```

**خروجی مورد انتظار:**
```
From https://github.com/arezoojoon/ArtinSmartRealtyPro
   bbbf6b0..599091c  main       -> origin/main
Updating bbbf6b0..599091c
Fast-forward
 backend/brain.py | 116 +++++++++++++++++++++++++++++++++++++++++++++++++++++++-
 1 file changed, 115 insertions(+), 1 deletion(-)
```

### گام 2: بررسی تغییرات (اختیاری)
```bash
git log --oneline -3
git diff bbbf6b0..599091c backend/brain.py | head -50
```

### گام 3: Rebuild و Restart Backend (بدون توقف frontend/nginx)
```bash
docker-compose build --no-cache backend
docker-compose up -d backend
```

**توضیحات:**
- `--no-cache`: اطمینان از build کامل با کد جدید
- `up -d backend`: فقط backend restart می‌شود، سرویس‌های دیگر بدون تاثیر

### گام 4: بررسی لاگ (Real-time monitoring)
```bash
docker-compose logs -f backend | grep -E "AFFIRMATIVE|current_properties|property_presenter"
```

**لاگ‌های مورد انتظار بعد از test:**
```
✅ AFFIRMATIVE RESPONSE detected from lead 123 - Triggering property presentation with photos+PDFs
✅ Found 3 properties in database for lead 123
🏠 Brain has 3 properties to present - using property_presenter
✅ Professional property presentation complete for lead 123
```

### گام 5: اگر املاک در دیتابیس نیست (برای tenant_id=2)
```bash
# بررسی املاک موجود
docker exec -i artinrealty-db psql -U postgres -d artinrealty -c "SELECT id, name, price, tenant_id FROM tenant_properties WHERE tenant_id = 2;"

# اگر خالی بود، اضافه کردن 6 ملک sample
cat add_sample_properties_tenant2.sql | docker exec -i artinrealty-db psql -U postgres -d artinrealty

# تایید
docker exec -i artinrealty-db psql -U postgres -d artinrealty -c "SELECT COUNT(*) FROM tenant_properties WHERE tenant_id = 2;"
```

**خروجی مورد انتظار:**
```
 count 
-------
     6
(1 row)
```

## تست (Testing)

### تست 1: Conversation Flow کامل
```
1. باز کردن @samanahmadi_Bot در Telegram
2. /start
3. وارد کردن نام (مثلا: arezoo)
4. اشتراک شماره تماس (از دکمه یا manual)
5. پاسخ به سوالات qualification:
   - Goal: investment
   - Budget: 1M-2M
   - Property Type: apartment
6. وقتی ربات financing info رو فرستاد و پرسید: "می‌خواهید ماشین‌حساب تامین مالی؟"
7. تایپ کردن: "yes" یا "بله" (نه دکمه!)
```

**نتیجه مورد انتظار:**
```
✅ Bot: "عالی! بذار براتون املاک رو با عکس و تحلیل ROI کامل بفرستم..."
✅ 3 property با Media Group (عکس‌های واقعی)
✅ PDF ROI برای هر ملک یا PDF brochure اگر موجود باشد
✅ پیام‌های بین هر ملک: 5 ثانیه تاخیر (برای جلوگیری از spam)
```

### تست 2: Negative Response
```
1. در همان مرحله financing info
2. تایپ کردن: "no" یا "نه"
```

**نتیجه مورد انتظار:**
```
✅ Bot: "مشکلی نیست! سوالی درباره این ملک‌ها یا املاک دبی دارید؟"
✅ State تغییر به ENGAGEMENT
✅ کاربر می‌تونه سوال بپرسه
```

### تست 3: Button Click (روش قدیمی که قبلا کار می‌کرد)
```
1. کلیک دکمه "✅ بله" به جای تایپ
```

**نتیجه مورد انتظار:**
```
✅ باید همان نتیجه تست 1 را بدهد
✅ callback_data="details_yes" هنوز کار می‌کند
```

## Rollback Plan (در صورت مشکل)

اگر مشکلی پیش آمد، برگرداندن به commit قبلی:

```bash
cd /opt/ArtinSmartRealtyPro/ArtinSmartRealty
git reset --hard bbbf6b0  # Commit قبل از این fix
docker-compose build --no-cache backend
docker-compose up -d backend
```

## Technical Details

### Commit Information
- **Commit Hash:** `599091c`
- **Previous Commit:** `bbbf6b0` (smart_upload fix)
- **Files Changed:** 1 (`backend/brain.py`)
- **Lines Changed:** +115, -1
- **Date:** December 14, 2025

### کد اضافه شده (Simplified)
```python
# در _handle_value_proposition() - خط 3445
if message and not callback_data:
    message_lower = message.lower().strip()
    
    # 0. DETECT YES/NO (بالاترین اولویت)
    affirmative_keywords = ["yes", "yeah", "sure", "ok", "بله", "آره", "باشه", ...]
    negative_keywords = ["no", "nope", "نه", "نخیر", "لا", ...]
    
    if is_pure_affirmative:
        # Query properties from database
        properties_db = await session.execute(
            select(TenantProperty).where(
                TenantProperty.tenant_id == lead.tenant_id,
                TenantProperty.is_active == True,
                # Filters: budget, property_type...
            ).limit(5)
        )
        
        # Convert to dict
        properties_list = [...]
        
        # SET for property_presenter
        self.current_properties = properties_list[:3]
        
        return BrainResponse(
            message="Perfect! Let me send you properties...",
            next_state=ConversationState.VALUE_PROPOSITION,
            lead_updates={"properties_sent": True}
        )
    
    elif is_pure_negative:
        return BrainResponse(
            message="No problem! Any questions?",
            next_state=ConversationState.ENGAGEMENT
        )
```

### Integration Points

1. **brain.py → telegram_bot.py**
   - `brain.current_properties` SET در brain.py خط 3495
   - `telegram_bot.py` خط 706 CHECK می‌کند
   - اگر موجود باشد، `present_all_properties()` صدا می‌زند

2. **property_presenter.py**
   - تابع `present_all_properties()` خط 43
   - برای Telegram: Media Groups (تا 10 عکس)
   - برای WhatsApp: تک تک عکس‌ها
   - ارسال PDF با caption کامل

3. **database.py**
   - Model: `TenantProperty` خط 429
   - فیلدها: `image_urls` (JSON array), `brochure_pdf` (String URL)
   - فیلترها: `tenant_id`, `is_active`, `price`, `property_type`

## Environment Variables مورد نیاز

اطمینان حاصل کنید که در `.env` موجود باشند:

```dotenv
# CRITICAL - برای generate کردن URLهای کامل در smart_upload
BASE_URL=https://realty.artinsmartagent.com

# یا برای تست local:
BASE_URL=http://localhost:8000
```

**توضیح:** بدون `BASE_URL`، فایل‌های آپلود شده به صورت relative path ذخیره می‌شوند و ربات نمی‌تواند به آن‌ها دسترسی داشته باشد.

## Success Criteria

✅ **قبل از fix:**
- کاربر "yes" می‌نوشت → ربات همان پیام financing را تکرار می‌کرد
- هیچ عکسی فرستاده نمی‌شد
- هیچ PDF ROI فرستاده نمی‌شد

✅ **بعد از fix:**
- کاربر "yes" می‌نویسد → ربات 3 ملک با Media Groups می‌فرستد
- هر ملک شامل: 
  - 📸 عکس‌های واقعی از `image_urls`
  - 📄 PDF ROI یا brochure از `brochure_pdf`
  - 💰 تحلیل کامل سرمایه‌گذاری
  - 🛂 وضعیت Golden Visa
- زمان بین املاک: 5 ثانیه (anti-spam)
- لاگ کامل برای monitoring

## مشکلات احتمالی و راه‌حل

### مشکل 1: "No properties found in database"
**علت:** دیتابیس خالی برای tenant  
**راه‌حل:** اجرای `add_sample_properties_tenant2.sql` (گام 5)

### مشکل 2: "عکس‌ها نشون داده نمیشن"
**علت:** `image_urls` خالی یا URLهای معتبر نیست  
**بررسی:**
```sql
SELECT id, name, image_urls FROM tenant_properties WHERE tenant_id = 2;
```
**راه‌حل:** استفاده از smart upload از dashboard یا اصلاح manual در SQL

### مشکل 3: "PDF فرستاده نمیشه"
**علت:** `brochure_pdf` NULL  
**راه‌حل:** آپلود PDF از dashboard smart upload یا set کردن URL:
```sql
UPDATE tenant_properties 
SET brochure_pdf = 'https://example.com/brochure.pdf' 
WHERE id = 1;
```

### مشکل 4: "ربات هنوز در loop هست"
**بررسی:** آیا backend rebuild شده؟
```bash
docker-compose ps backend
# اگر "Up X minutes" نشان می‌دهد، یعنی restart شده
```

**راه‌حل:**
```bash
docker-compose restart backend
docker-compose logs -f backend | head -20
```

## Support & Contact

**مشکل در deployment؟**
- لاگ کامل: `docker-compose logs backend > backend.log`
- بررسی لاگ: `grep -i error backend.log`

**تست موفق شد؟**
✅ یک تست واقعی انجام دهید و نتیجه را بررسی کنید
✅ اگر املاک با عکس و PDF فرستاده شد، fix کامل است!

---

**تاریخ:** دسامبر 14, 2025  
**توسعه‌دهنده:** GitHub Copilot + Arezoo Mohammadzadegan  
**Commit:** 599091c  
**شدت:** 🚨 CRITICAL - باگ core conversation flow
