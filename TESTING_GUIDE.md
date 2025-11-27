# 🧪 Testing Guide - Before Server Deployment

## ✅ Checklist قبل از Deploy

### 1. Voice Processing (پردازش صدا)
**Telegram:**
- [ ] ارسال پیام صوتی فارسی: "من می‌خواهم یک آپارتمان سه خوابه در دبی مارینا با بودجه 500 هزار درهم بخرم"
- [ ] انتظار: نمایش transcript + استخراج (budget=500k, location=Dubai Marina, bedrooms=3)
- [ ] بررسی: Lead profile باید update شود

**WhatsApp:**
- [ ] ارسال voice note
- [ ] انتظار: دانلود، transcribe، و پاسخ

### 2. Image Processing (پردازش عکس)
**Telegram:**
- [ ] ارسال عکس یک ویلا لوکس
- [ ] انتظار: "🔍 در حال تحلیل عکس شما..."
- [ ] انتظار: نمایش 1-3 ملک مشابه از database
- [ ] بررسی: Properties باید match شوند (type, style, features)

**WhatsApp:**
- [ ] ارسال تصویر ملک
- [ ] انتظار: پیدا کردن املاک مشابه

### 3. ROI PDF Generation
**Telegram:**
- [ ] مسیر کامل conversation تا phone gate
- [ ] وارد کردن شماره موبایل
- [ ] انتظار: دریافت فایل PDF با نام `ROI_Analysis_[tenant_name].pdf`
- [ ] بررسی PDF:
  - [ ] Header با logo tenant
  - [ ] محاسبات ROI صحیح
  - [ ] Golden Visa info
  - [ ] Branding مناسب

**API Test:**
```bash
# Test ROI PDF endpoint
curl -X GET "https://realty.artinsmartagent.com/api/tenants/1/leads/1/roi-pdf" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output roi_test.pdf
```

### 4. WhatsApp Integration
**Webhook Verification:**
```bash
# Check if webhook is registered
curl "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID?fields=webhooks&access_token=YOUR_ACCESS_TOKEN"
```

**Message Test:**
- [ ] ارسال پیام text به WhatsApp Business number
- [ ] انتظار: دریافت پاسخ با 4 زبان
- [ ] تست button interaction
- [ ] تست list interaction (بیش از 3 گزینه)

**Media Test:**
- [ ] ارسال voice note
- [ ] ارسال image
- [ ] ارسال location

### 5. Language Selection (انتخاب زبان)
- [ ] /start → نمایش 4 دکمه: 🇬🇧 English | 🇮🇷 فارسی | 🇦🇪 العربية | 🇷🇺 Русский
- [ ] انتخاب فارسی → تمام پیام‌ها به فارسی
- [ ] انتخاب عربی → تمام پیام‌ها به عربی
- [ ] بررسی: `lead.language` در database update شود

### 6. Phone Format Example
- [ ] رسیدن به Phone Gate
- [ ] انتظار پیام شامل: "Example: +971501234567 or +989121234567"
- [ ] تست فرمت‌های مختلف:
  - [ ] +971501234567 ✅
  - [ ] 00971501234567 ✅
  - [ ] 0501234567 ❌ (باید خطا دهد)

### 7. Conversation Warmth (گرمی مکالمه)
- [ ] بررسی welcome message: باید enthusiastic و warm باشد
- [ ] بررسی استفاده از emoji
- [ ] بررسی personalization با نام agent

---

## 🐛 مشکلات شناخته شده

### ⚠️ Gemini API Key
- Voice و Image processing نیاز به `GOOGLE_API_KEY` در `.env` دارند
- بدون API key → پیام خطا: "Voice/Image processing unavailable"

### ⚠️ WhatsApp Media Upload
- ROI PDF در WhatsApp فعلاً فقط log می‌شود
- نیاز به implement کردن WhatsApp Media Upload API
- راه حل موقت: ارسال link به PDF در server

### ⚠️ Properties در Database
- Image matching نیاز به sample properties دارد
- اگر `tenant.properties` خالی باشد → "no results" message
- حل: اجرای `setup_sample_data.py`

---

## 🚀 Pre-Deployment Commands

```bash
# 1. Pull آخرین کد
git pull origin copilot/build-multi-tenant-saas-architecture

# 2. Check environment variables
cat .env | grep -E "GOOGLE_API_KEY|WHATSAPP|DATABASE_URL"

# 3. Build frontend (برای Properties module)
docker compose build frontend

# 4. Restart backend
docker compose restart backend

# 5. Check logs
docker compose logs -f backend

# 6. Test Telegram bot
# ارسال /start به @Taranteenproperties_bot

# 7. Setup WhatsApp webhook (اگر هنوز نشده)
python setup_whatsapp_webhook.py
```

---

## 📊 Expected Results

### Voice Message Test
```
User: [ویس: من یک آپارتمان دو خوابه می‌خواهم]
Bot: 🎤 گرفتم! شما گفتید:
     "من یک آپارتمان دو خوابه می‌خواهم"
     
     بذارید پردازش کنم...
     
     عالی! دو خوابه آپارتمان، درسته؟ [buttons]
```

### Image Message Test
```
User: [عکس ویلا مدرن]
Bot: 🔍 در حال تحلیل عکس شما... بذارید املاک مشابه رو پیدا کنم!

     ✨ 3 ملک مشابه پیدا کردم! اینم بهترینش:
     
     1. **Luxury Beach Villa**
        📍 Palm Jumeirah
        🏠 5BR Villa
        💰 AED 12,000,000 🛂 Golden Visa | ROI: 6.5%
        ✨ Private Beach, Modern Design, Pool
```

### ROI PDF Test
```
User: +971501234567
Bot: 📊 Here's your personalized ROI Analysis Report!
     [PDF attachment: ROI_Analysis_ArtinSmartRealty.pdf]
```

---

## 🎯 Success Criteria

- ✅ Voice → Transcript صحیح (95%+ accuracy)
- ✅ Image → 1-3 matching properties
- ✅ PDF → دانلود موفق در Telegram
- ✅ WhatsApp → دریافت و پاسخ به messages
- ✅ 4 زبان → کار می‌کنند
- ✅ Phone format → مثال نمایش داده می‌شود
- ✅ Conversation → warm و engaging

---

## 📞 Support

اگر مشکلی پیش آمد:
1. بررسی logs: `docker compose logs -f backend`
2. بررسی database: `docker compose exec db psql -U artinrealty -d artinrealty_db`
3. تست API: استفاده از Postman یا curl
4. بررسی Gemini API quota: https://aistudio.google.com/

---

**آماده deployment؟ اجرای دستورات بالا + تست همه features = 🚀 Go Live!**
