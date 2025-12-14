# ✅ Checklist: راه‌اندازی سیستم یکپارچه

## 📋 قبل از شروع

- [ ] Python 3.9+ نصب شده
- [ ] PostgreSQL 13+ نصب و راه‌اندازی شده
- [ ] Git برای کلون کردن پروژه
- [ ] دسترسی به API Key گوگل Gemini (رایگان)

---

## 🔧 مرحله 1: نصب Dependencies

```powershell
cd "i:\real state salesman\ArtinSmartRealty\backend"

# فعال‌سازی venv (اگر دارید)
.\venv\Scripts\Activate.ps1

# نصب پکیج‌های جدید
pip install -r requirements_unified.txt
```

- [ ] همه پکیج‌ها بدون خطا نصب شدند

---

## ⚙️ مرحله 2: تنظیمات محیط

ویرایش فایل `.env` در `ArtinSmartRealty/backend/`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/artinrealty

# Gemini AI
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE

# JWT
JWT_SECRET=your-random-secret-key-min-32-chars
```

- [ ] DATABASE_URL صحیح است
- [ ] GEMINI_API_KEY از https://makersuite.google.com/app/apikey دریافت شد
- [ ] JWT_SECRET تنظیم شد

---

## 🗄️ مرحله 3: Migration دیتابیس

```powershell
cd "i:\real state salesman\ArtinSmartRealty\backend"
python migrate_unified_leads.py
```

**خروجی مورد انتظار:**

```
🚀 Creating Unified Lead System Tables...
✅ Tables created successfully!
📦 Migrating LinkedIn Scraper Leads...
   ✅ Migrated: X leads
📦 Migrating Bot Leads...
   ✅ Migrated: Y leads
✅ MIGRATION COMPLETED SUCCESSFULLY!
```

- [ ] Migration بدون خطا اجرا شد
- [ ] جداول `unified_leads`, `lead_interactions`, `followup_campaigns` ایجاد شدند
- [ ] لیدهای LinkedIn مایگریت شدند (اگر موجود بود)
- [ ] لیدهای Bot مایگریت شدند

---

## 🚀 مرحله 4: راه‌اندازی Backend

```powershell
cd "i:\real state salesman\ArtinSmartRealty\backend"
python main.py
```

**خروجی مورد انتظار:**

```
🚀 Starting ArtinSmartRealty V2 - Unified Platform...
✅ Database initialized
✅ Background scheduler started
✅ Morning Coffee Report scheduler started
✅ Unified Follow-up Engine started
INFO:     Uvicorn running on http://0.0.0.0:8000
```

- [ ] Backend بدون خطا شروع شد
- [ ] Follow-up Engine راه‌اندازی شد
- [ ] Server روی پورت 8000 در دسترس است

---

## 🧪 مرحله 5: تست API

### الف) Health Check

```powershell
curl http://localhost:8000/health
```

- [ ] Response: `{"status": "healthy", ...}`

### ب) Swagger Documentation

مرورگر: http://localhost:8000/docs

- [ ] Swagger UI لود شد
- [ ] Endpoint های `/api/unified/*` نمایش داده می‌شوند

### ج) تست افزودن لید

```powershell
curl -X POST "http://localhost:8000/api/unified/linkedin/add-lead" `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Test User",
    "linkedin_url": "https://linkedin.com/in/testuser",
    "job_title": "CEO",
    "company": "Test Corp"
  }'
```

- [ ] Response موفق (status 200)
- [ ] لید در دیتابیس ایجاد شد
- [ ] `lead_score` محاسبه شد
- [ ] `next_followup_at` تنظیم شد

### د) تست آمار

```powershell
curl "http://localhost:8000/api/unified/stats?tenant_id=1"
```

- [ ] آمار نمایش داده می‌شود
- [ ] تعداد لیدها صحیح است

---

## 📊 مرحله 6: مانیتورینگ Follow-up Engine

بعد از 1 ساعت، در لاگ‌های Backend باید ببینید:

```
🔄 [2025-12-10 15:00] Processing Follow-ups...
   Found 1 leads needing follow-up
   ✅ Sent follow-up to Test User via telegram
```

- [ ] Follow-up Engine هر ساعت اجرا می‌شود
- [ ] پیام‌های خودکار ارسال می‌شوند
- [ ] تعاملات در `lead_interactions` ثبت می‌شوند

---

## 🔗 مرحله 7: اتصال LinkedIn Scraper (اختیاری)

در `AI Lead Scraper & Personalize/backend/main.py`:

```python
# Update the /api/save-lead endpoint to forward to unified system
import httpx

@app.post("/api/save-lead")
async def save_lead(lead_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/unified/linkedin/add-lead",
            json=lead_data
        )
        return response.json()
```

- [ ] LinkedIn Scraper به سیستم یکپارچه متصل شد
- [ ] لیدهای جدید از LinkedIn در `unified_leads` ذخیره می‌شوند

---

## 🎯 مرحله 8: تست Property Matching

### الف) اضافه کردن ملک

از API موجود یک ملک اضافه کنید

### ب) نوتیفیکیشن لیدهای مچ

```powershell
curl -X POST "http://localhost:8000/api/unified/properties/PROPERTY_ID/notify-matches"
```

- [ ] لیدهای مچ پیدا شدند
- [ ] پیام‌های شخصی‌سازی شده ارسال شدند
- [ ] `matched_properties` در لیدها آپدیت شد

---

## 📤 مرحله 9: تست Export

```powershell
curl "http://localhost:8000/api/unified/export/excel?tenant_id=1" --output leads.xlsx
```

- [ ] فایل Excel دانلود شد
- [ ] همه لیدها در Excel موجود هستند
- [ ] ستون‌ها صحیح هستند (Name, Phone, Email, Score, Grade, ...)

---

## 🎓 مرحله 10: آموزش تیم

- [ ] تیم با Dashboard آشنا شدند
- [ ] نحوه افزودن لید از LinkedIn آموزش داده شد
- [ ] نحوه مشاهده آمار و گزارش‌ها توضیح داده شد
- [ ] سیستم Follow-up خودکار توضیح داده شد

---

## 🐛 عیب‌یابی

### مشکل: Migration فیل می‌کند

```powershell
# چک کردن اتصال به دیتابیس
psql -U postgres -d artinrealty -c "SELECT version();"
```

### مشکل: Follow-up Engine شروع نمی‌شود

```powershell
# چک کردن نصب apscheduler
pip show apscheduler
```

### مشکل: لیدهای LinkedIn مایگریت نشدند

```powershell
# چک کردن مسیر دیتابیس SQLite
ls "i:\real state salesman\AI Lead Scraper & Personalize\backend\leads_database.db"
```

---

## ✅ وضعیت نهایی

پس از تکمیل همه موارد بالا، سیستم شما:

- ✅ لیدهای LinkedIn و Bot را در یک جا مدیریت می‌کند
- ✅ Follow-up خودکار انجام می‌دهد
- ✅ نوتیفیکیشن املاک جدید می‌فرستد
- ✅ Lead Scoring خودکار دارد
- ✅ گزارش‌دهی جامع دارد
- ✅ آماده برای استفاده در تولید است

---

## 📞 پشتیبانی

مشکلی پیش آمد؟

1. بررسی فایل‌های راهنما:
   - `UNIFIED_PLATFORM_ARCHITECTURE.md`
   - `DEPLOYMENT_GUIDE_UNIFIED.md`
   - `PROJECT_SUMMARY.md`

2. چک کردن لاگ‌های Backend

3. تماس با پشتیبانی:
   - Email: info@artinsmartagent.com

---

**تاریخ**: 10 دسامبر 2025  
**وضعیت**: ✅ آماده برای استقرار
