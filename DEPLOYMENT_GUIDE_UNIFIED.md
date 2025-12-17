# 🚀 راهنمای استقرار سریع - سیستم یکپارچه ArtinSmartRealty

## مراحل نصب و راه‌اندازی

### 1️⃣ پیش‌نیازها

```bash
# Python 3.9+
python --version

# PostgreSQL 13+
psql --version

# Redis (اختیاری - برای کش)
redis-server --version
```

### 2️⃣ نصب Dependencies

```powershell
cd "i:\real state salesman\ArtinSmartRealty\backend"

# ایجاد محیط مجازی
python -m venv venv

# فعال‌سازی
.\venv\Scripts\Activate.ps1

# نصب پکیج‌ها
pip install -r requirements.txt

# پکیج‌های اضافی برای سیستم Follow-up
pip install apscheduler pandas openpyxl xlsxwriter
```

### 3️⃣ تنظیمات محیط (.env)

در `ArtinSmartRealty/backend/.env` این تنظیمات را اضافه کنید:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/artinrealty

# Gemini AI (for LinkedIn message generation)
GEMINI_API_KEY=your_gemini_api_key_here

# JWT
JWT_SECRET=your-super-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=720

# Super Admin
SUPER_ADMIN_EMAIL=admin@artinsmartrealty.com
SUPER_ADMIN_PASSWORD=YourSecurePassword123!

# Telegram (optional - برای هر tenant)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# WhatsApp (optional)
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
```

### 4️⃣ اجرای Migration

```powershell
# در پوشه backend
cd "i:\real state salesman\ArtinSmartRealty\backend"

# اجرای migration برای ایجاد جداول unified
python migrate_unified_leads.py
```

خروجی باید شبیه این باشد:

```
🚀 Creating Unified Lead System Tables...
✅ Tables created successfully!
   - unified_leads: ✅
   - lead_interactions: ✅
   - followup_campaigns: ✅
   - property_lead_matches: ✅

📦 Migrating LinkedIn Scraper Leads...
   Found 150 LinkedIn leads
   ✅ Migrated: 150 leads
   ⏭️  Skipped (duplicates): 0 leads

📦 Migrating Bot Leads...
   Found 75 bot leads
   ✅ Migrated: 75 leads
   ⏭️  Skipped (duplicates): 0 leads

✅ MIGRATION COMPLETED SUCCESSFULLY!
```

### 5️⃣ راه‌اندازی Backend

```powershell
# در پوشه backend
python main.py
```

یا با Uvicorn:

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

خروجی:

```
🚀 Starting ArtinSmartRealty V2 - Unified Platform...
✅ Database initialized
✅ Background scheduler started
✅ Morning Coffee Report scheduler started
✅ Unified Follow-up Engine started
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 6️⃣ تست API

#### الف) بررسی Health Check

```powershell
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "timestamp": "2025-12-10T10:30:00"
}
```

#### ب) مشاهده Swagger Docs

مرورگر را باز کنید و به این آدرس بروید:

```
http://localhost:8000/docs
```

### 7️⃣ اضافه کردن لید LinkedIn

از طریق Chrome Extension یا مستقیم API:

```powershell
curl -X POST "http://localhost:8000/api/unified/linkedin/add-lead" `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Ali Rezaei",
    "linkedin_url": "https://linkedin.com/in/alirezaei",
    "email": "ali@example.com",
    "phone": "+971501234567",
    "job_title": "CEO",
    "company": "Tech Startup Inc",
    "about": "Experienced entrepreneur looking for investment opportunities",
    "location": "Dubai",
    "generated_message": "Hi Ali! Saw your profile..."
  }'
```

Response:

```json
{
  "id": 1,
  "name": "Ali Rezaei",
  "source": "linkedin",
  "status": "new",
  "lead_score": 25,
  "grade": "D",
  "created_at": "2025-12-10T10:35:00",
  "next_followup_at": "2025-12-10T11:35:00",
  "followup_count": 0
}
```

**✨ سیستم خودکار:**
- لید ذخیره شد ✅
- امتیاز محاسبه شد ✅
- Follow-up در 1 ساعت آینده زمان‌بندی شد ✅

### 8️⃣ مشاهده آمار

```powershell
curl http://localhost:8000/api/unified/stats?tenant_id=1
```

```json
{
  "total_leads": 225,
  "by_source": {
    "linkedin": 150,
    "telegram": 60,
    "whatsapp": 15
  },
  "by_status": {
    "new": 80,
    "contacted": 65,
    "qualified": 50,
    "won": 30
  },
  "by_grade": {
    "A": 45,
    "B": 80,
    "C": 70,
    "D": 30
  },
  "pending_followups": 35
}
```

### 9️⃣ ایجاد کمپین Follow-up

```powershell
curl -X POST "http://localhost:8000/api/unified/campaigns" `
  -H "Content-Type: application/json" `
  -d '{
    "name": "LinkedIn Lead Warmup",
    "description": "Welcome new LinkedIn leads",
    "message_template": "Hi {name}! Saw your profile at {company}...",
    "target_status": ["new", "contacted"],
    "min_score": 0,
    "channels": ["telegram", "whatsapp"]
  }'
```

### 🔟 اضافه کردن ملک جدید و نوتیفیکیشن

```powershell
# اول ملک را اضافه کنید (از API موجود)
# سپس نوتیفیکیشن را فعال کنید:

curl -X POST "http://localhost:8000/api/unified/properties/123/notify-matches"
```

سیستم:
1. لیدهای مچ را پیدا می‌کند ✅
2. به آن‌ها پیام شخصی‌سازی شده می‌فرستد ✅
3. در تاریخچه تعاملات ثبت می‌کند ✅

---

## 📊 مانیتورینگ Follow-up Engine

### چک کردن لاگ‌ها

```powershell
# در ترمینالی که backend اجرا شده:
```

هر ساعت خواهید دید:

```
🔄 [2025-12-10 14:00] Processing Follow-ups...
   Found 12 leads needing follow-up
   ✅ Sent follow-up to Ali Rezaei via telegram
   ✅ Sent follow-up to Sara Mohammadi via whatsapp
   ...
```

### دستی اجرای Follow-up (برای تست)

```python
# در Python console:
import asyncio
from backend.followup_engine import followup_engine

async def test_followup():
    await followup_engine.process_scheduled_followups()

asyncio.run(test_followup())
```

---

## 🔧 عیب‌یابی

### مشکل: Follow-up Engine شروع نمی‌شود

```powershell
# چک کنید که تمام dependencies نصب شده باشند:
pip list | grep -i apscheduler
pip list | grep -i pandas
```

### مشکل: Migration فیل می‌کند

```powershell
# دیتابیس را ریست کنید (احتیاط!):
psql -U postgres -d artinrealty -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# دوباره migration را اجرا کنید:
python migrate_unified_leads.py
```

### مشکل: لیدهای LinkedIn مایگریت نشدند

```powershell
# مسیر دیتابیس SQLite را چک کنید:
ls "i:\real state salesman\AI Lead Scraper & Personalize\backend\leads_database.db"

# اگر وجود ندارد، مسیر را در migrate_unified_leads.py تغییر دهید
```

---

## ✅ چک‌لیست بعد از نصب

- [ ] Backend روی `http://localhost:8000` اجرا می‌شود
- [ ] Swagger Docs در `http://localhost:8000/docs` قابل دسترس است
- [ ] جداول `unified_leads`, `lead_interactions` در دیتابیس وجود دارند
- [ ] Follow-up Engine شروع شده (لاگ می‌بینید)
- [ ] لیدهای LinkedIn مایگریت شده‌اند
- [ ] لیدهای Bot مایگریت شده‌اند
- [ ] API `/api/unified/stats` آمار را برمی‌گرداند
- [ ] کمپین Follow-up ایجاد می‌شود

---

## 📱 مرحله بعدی: اتصال LinkedIn Scraper

در `AI Lead Scraper & Personalize/backend/main.py`، endpoint قدیمی را تغییر دهید:

```python
# قبلی:
@app.post("/api/save-lead")
async def save_lead(lead_data: dict):
    # Old SQLite code
    ...

# جدید:
@app.post("/api/save-lead")
async def save_lead(lead_data: dict):
    # Forward to unified system
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/unified/linkedin/add-lead",
            json=lead_data
        )
        return response.json()
```

---

## 🎯 تست کامل End-to-End

### Scenario: لید جدید از LinkedIn

1. کاربر از Chrome Extension لید را Scrape می‌کند
2. لید در `unified_leads` ذخیره می‌شود
3. امتیاز محاسبه می‌شود → Grade: D
4. Follow-up در 1 ساعت بعد زمان‌بندی می‌شود
5. بعد از 1 ساعت، پیام خودکار ارسال می‌شود (Telegram/WhatsApp)
6. اگر جواب بدهد → امتیاز افزایش می‌یابد → Grade: C
7. اگر بودجه بگوید → Status: Qualified → Grade: B
8. وقتی ملک جدید اضافه شود → نوتیفیکیشن اتوماتیک ارسال می‌شود

همه اینها **کاملا خودکار** است! 🎉

---

**سوالات؟** به `UNIFIED_PLATFORM_ARCHITECTURE.md` مراجعه کنید یا در Issues گیتهاب سوال بپرسید.
