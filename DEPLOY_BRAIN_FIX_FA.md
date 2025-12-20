# 🔧 راهنمای سریع رفع مشکل ربات

## مشکل چی بود؟
ربات وقتی کاربر سوال میپرسید، به جای جواب دادن، همش میگفت "اسمت چیه؟" و در یک loop میافتاد.

## چی درست شد؟
✅ حالا اگه کاربر موقع گرفتن اسم سوال بپرسه، ربات:
1. جواب سوال رو میده (با Gemini AI)
2. بعد دوباره اسم رو میپرسه

✅ دیگه تکراری و احمقانه جواب نمیده

## چطوری deploy کنیم؟

### روش 1: SSH به سرور (بهترین)

```bash
# 1. از لوکال به سرور وصل شو
ssh root@72.62.93.116

# 2. وارد پوشه پروژه شو
cd /opt/ArtinSmartRealty

# 3. فایل brain.py رو جایگزین کن
# (اول فایل جدید رو upload کن با scp یا از طریق git pull)

# 4. Backend رو rebuild کن
chmod +x quick_fix_brain.sh
./quick_fix_brain.sh
```

### روش 2: Manual (اگه SSH نداری)

#### 2.1. Upload فایل جدید
```bash
# از کامپیوتر خودت:
scp i:\ArtinRealtySmartPro\ArtinSmartRealty\backend\brain.py root@72.62.93.116:/opt/ArtinSmartRealty/backend/brain.py
```

#### 2.2. Rebuild کردن از طریق Hostinger Panel
1. به Hostinger panel وارد شو
2. برو به Server Management → Docker
3. پیدا کن `artinrealty-backend` container
4. کلیک کن **Rebuild**
5. بعد **Restart**

### روش 3: Git Pull (اگه git داری)

```bash
ssh root@72.62.93.116

cd /opt/ArtinSmartRealty

# Pull کردن آخرین تغییرات
git pull origin main

# Rebuild backend
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d

# چک کردن logs
docker-compose logs -f backend
```

## تست کردن

بعد از deploy:

1. به تلگرام برو: [@TaranteenBot](https://t.me/TaranteenBot)
2. دستور `/start` رو بفرست
3. زبان فارسی رو انتخاب کن: 🇮🇷
4. وقتی ازت اسم میخواد، یه سوال بپرس:
   ```
   ببین من چطوری میتونم اقامت بگیرم؟
   ```
5. حالا باید ربات:
   - جواب سوال رو بده
   - دوباره اسم رو بپرسه

## اگه باز مشکل داشت چی کار کنیم؟

### چک کردن logs:
```bash
docker-compose logs -f backend | grep -E "❓|❌|GEMINI|ERROR"
```

### اگه Gemini API کار نمیکنه:
```bash
# تست Gemini API
docker-compose exec backend python -c "
import os
import google.generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content('سلام بگو')
print(response.text)
"
```

اگه این خطا داد:
```
InvalidArgument: 400 API key not valid
```
یعنی API key معتبر نیست. باید تو `.env` تصحیح کنی.

### اگه loop باز برگشت:
احتمالاً backend rebuild نشده. این دستورات رو بزن:

```bash
docker-compose down
docker volume rm artinsmartrealty_backend_cache  # پاک کردن cache
docker-compose build --no-cache backend
docker-compose up -d
docker-compose logs -f backend
```

## لاگ های مهم

✅ **موفقیت آمیز:**
```
✅ Database initialized
✅ Bot started successfully
INFO: Uvicorn running on http://0.0.0.0:8000
❓ User asked question during name collection
```

❌ **خطا:**
```
❌ GEMINI_API_KEY not set!
❌ AI answer failed during name collection
asyncpg.exceptions.InvalidPasswordError
```

## سوالات متداول

**Q: چرا ربات باز همش تکرار میکنه؟**
A: Backend rebuild نشده. دستور `docker-compose build --no-cache backend` رو بزن.

**Q: Gemini API خطا میده چی کار کنم؟**
A: API key تو `.env` فایل رو چک کن. باید دقیقاً همین باشه:
```
GEMINI_API_KEY=AIzaSyCVFV1O16B-ByDargD7LzLt2Y6LLpDqqeQ
```

**Q: چطوری بفهمم brain.py جدید load شده؟**
A: تو logs باید ببینی:
```
❓ User asked question during name collection: ببین من چطوری میتونم اقامت بگیرم؟
```
اگه این خط رو دیدی، یعنی کد جدید load شده ✅

---

**✅ پس از deploy موفق، ربات دیگه "احمق" نیست! 🎉**
