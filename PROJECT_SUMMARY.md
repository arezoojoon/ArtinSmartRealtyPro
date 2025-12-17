# ✅ خلاصه پروژه: ادغام LinkedIn Scraper + Real Estate Bot

## 🎯 هدف

ادغام دو سیستم جداگانه به یک **پلتفرم واحد هوشمند**:

1. **AI Lead Scraper** (Chrome Extension) - جمع‌آوری لید از لینکدین
2. **ArtinSmartRealty Bot** (Telegram/WhatsApp) - کوالیفای و فالواپ لیدها

---

## ✨ قابلیت‌های جدید

### 1️⃣ سیستم مدیریت یکپارچه لیدها

**قبل از ادغام:**
- لیدهای لینکدین در SQLite ذخیره می‌شدند
- لیدهای ربات در PostgreSQL بودند
- هیچ ارتباطی بین دو سیستم نبود
- فالواپ دستی بود

**بعد از ادغام:**
- همه لیدها در یک جدول `unified_leads` ✅
- Duplicate Detection هوشمند (LinkedIn URL, Telegram ID, Phone) ✅
- امتیازدهی خودکار (Lead Scoring 0-100) ✅
- درجه‌بندی خودکار (A/B/C/D) ✅

### 2️⃣ سیستم Follow-up خودکار

**قابلیت‌ها:**
- لیدهای جدید لینکدین خودکار Follow-up می‌شوند ✅
- پیام‌های شخصی‌سازی شده با AI (Google Gemini) ✅
- 5 مرحله Follow-up (Introduction → Value → Urgency → Last Chance → Exit) ✅
- زمان‌بندی هوشمند (هر 3 روز یک بار) ✅
- Multi-channel (Telegram + WhatsApp) ✅

### 3️⃣ سیستم Property Matching

**قابلیت‌ها:**
- وقتی ملک جدید اضافه می‌شود، لیدهای مرتبط پیدا می‌شوند ✅
- نوتیفیکیشن خودکار به لیدها ✅
- پیام شخصی‌سازی شده برای هر لید ✅
- Track املاکی که دیده شده‌اند ✅

### 4️⃣ گزارش‌دهی جامع

**Dashboard متریک‌ها:**
- تعداد کل لیدها (بر اساس منبع: LinkedIn/Telegram/WhatsApp)
- تعداد لیدها بر اساس وضعیت (New/Contacted/Qualified/Won)
- تعداد لیدها بر اساس درجه (A/B/C/D)
- لیدهای در انتظار Follow-up

---

## 📁 فایل‌های ایجاد شده

### Backend Files

```
ArtinSmartRealty/backend/
├── unified_database.py              # 🆕 مدل‌های دیتابیس یکپارچه
├── migrate_unified_leads.py         # 🆕 اسکریپت migration
├── followup_engine.py               # 🆕 موتور Follow-up خودکار
├── api/
│   └── unified_routes.py            # 🆕 API Routes یکپارچه
└── main.py                          # ✏️  آپدیت شده (Follow-up Engine)
```

### Documentation

```
i:\real state salesman/
├── UNIFIED_PLATFORM_ARCHITECTURE.md  # 🆕 معماری سیستم یکپارچه
├── DEPLOYMENT_GUIDE_UNIFIED.md       # 🆕 راهنمای نصب و استقرار
└── PROJECT_SUMMARY.md                # 🆕 این فایل
```

---

## 🗄️ ساختار دیتابیس

### جداول جدید

#### 1. `unified_leads`
- ذخیره همه لیدها از همه منابع
- فیلدهای کلیدی: LinkedIn URL, Telegram ID, WhatsApp Number
- Lead Scoring & Grading
- تاریخچه Follow-up

#### 2. `lead_interactions`
- ذخیره همه تعاملات با لیدها
- Channel (LinkedIn/Telegram/WhatsApp/Email)
- Direction (Inbound/Outbound)
- AI Generated Flag

#### 3. `followup_campaigns`
- مدیریت کمپین‌های Follow-up
- Target Filters (Status, Score, Source)
- آمار (Sent, Delivered, Replied)

#### 4. `property_lead_matches`
- کش املاک-لید برای جستجوی سریع
- Match Score
- Notification Status

---

## 🔄 جریان کار (Workflow)

### Scenario 1: لید جدید از LinkedIn

```
1. کاربر LinkedIn Profile را Scrape می‌کند
   ↓
2. Chrome Extension به API می‌فرستد
   POST /api/unified/linkedin/add-lead
   ↓
3. Backend:
   - چک می‌کند لید قبلا وجود دارد؟
   - اگر نه → ایجاد می‌کند
   - امتیاز محاسبه می‌شود → Grade تعیین می‌شود
   - Follow-up زمان‌بندی می‌شود (1 ساعت بعد)
   ↓
4. بعد از 1 ساعت:
   - Follow-up Engine فعال می‌شود
   - پیام شخصی‌سازی شده تولید می‌شود (AI)
   - ارسال به Telegram یا WhatsApp
   - Interaction ثبت می‌شود
   ↓
5. اگر پاسخ داد:
   - امتیاز افزایش می‌یابد
   - Grade ارتقا می‌یابد (D → C → B → A)
   - Follow-up بعدی زمان‌بندی می‌شود
```

### Scenario 2: ملک جدید اضافه شد

```
1. Agent ملک جدید را اضافه می‌کند
   ↓
2. Backend:
   POST /api/unified/properties/{id}/notify-matches
   ↓
3. Property Matching Engine:
   - Query: لیدهایی که بودجه/نوع/لوکیشن مچ می‌کند
   - پیدا کردن 50 لید مرتبط
   ↓
4. برای هر لید:
   - پیام شخصی‌سازی شده تولید می‌شود
   - ارسال به Telegram/WhatsApp
   - matched_properties آپدیت می‌شود
   ↓
5. لید پاسخ می‌دهد:
   - "می‌خوام ببینم"
   → Status: viewing_scheduled
   → امتیاز +15
   → Grade: B → A
```

### Scenario 3: لید از Telegram پیام می‌دهد

```
1. کاربر به ربات پیام می‌فرستد
   ↓
2. Backend:
   - چک می‌کند لید با این Telegram ID وجود دارد؟
   - اگر بله → Merge با لید لینکدین (اگر LinkedIn URL داشته باشد)
   - اگه نه → ایجاد لید جدید
   ↓
3. AI Conversation:
   - استخراج: Budget, Property Type, Location
   - شناسایی: Pain Points, Purpose
   - محاسبه: Lead Score
   ↓
4. Property Matching:
   - پیدا کردن املاک مچ
   - ارسال توصیه‌ها
   ↓
5. Lead Status Update:
   - new → contacted → qualified → viewing_scheduled → won
```

---

## 🎯 Lead Scoring System

### محاسبه امتیاز (0-100)

```python
# 1. اطلاعات تماس (20 امتیاز)
if phone: +5
if email: +5
if linkedin_url: +5
if job_title: +5

# 2. تعامل (30 امتیاز)
if followup_count > 0: +5
if total_messages_received > 0: +10
if total_messages_received >= 3: +10
if active_in_last_7_days: +5

# 3. کوالیفیکیشن (30 امتیاز)
if has_budget: +10
if has_property_type: +5
if has_preferred_locations: +5
if has_transaction_type: +5
if has_purpose: +5

# 4. اقدام (20 امتیاز)
if viewed_properties: +5
if favorited_properties: +5
if scheduled_viewing: +10
```

### درجه‌بندی

- **A (80-100)**: Hot Lead - باید فورا پیگیری شود
- **B (60-79)**: Warm Lead - احتمال تبدیل بالا
- **C (40-59)**: Cold Lead - نیاز به nurturing
- **D (0-39)**: Very Cold - پیگیری کم‌اولویت

---

## 📊 API Endpoints جدید

### Lead Management

```http
GET    /api/unified/leads                    # لیست همه لیدها
GET    /api/unified/leads/{id}               # جزئیات یک لید
POST   /api/unified/linkedin/add-lead        # افزودن لید LinkedIn
PUT    /api/unified/leads/{id}/status        # تغییر وضعیت
POST   /api/unified/leads/{id}/note          # افزودن یادداشت
GET    /api/unified/stats                    # آمار Dashboard
```

### Property Matching

```http
POST   /api/unified/properties/{id}/notify-matches    # نوتیف لیدهای مچ
GET    /api/unified/leads/{id}/matched-properties     # املاک مچ شده
```

### Follow-up Campaigns

```http
POST   /api/unified/campaigns                # ایجاد کمپین
GET    /api/unified/campaigns                # لیست کمپین‌ها
```

### Interactions

```http
GET    /api/unified/leads/{id}/interactions  # تاریخچه تعاملات
```

### Export

```http
GET    /api/unified/export/excel             # دانلود Excel
```

---

## 🚀 نحوه استفاده

### 1. نصب و راه‌اندازی

```powershell
# نصب dependencies
cd "i:\real state salesman\ArtinSmartRealty\backend"
pip install -r requirements.txt
pip install apscheduler pandas openpyxl xlsxwriter

# اجرای migration
python migrate_unified_leads.py

# راه‌اندازی backend
python main.py
```

### 2. تست Follow-up Engine

```python
# در Python console:
import asyncio
from backend.followup_engine import followup_engine

async def test():
    await followup_engine.process_scheduled_followups()

asyncio.run(test())
```

### 3. افزودن لید از LinkedIn

```bash
curl -X POST "http://localhost:8000/api/unified/linkedin/add-lead" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "job_title": "CEO",
    "company": "Tech Corp"
  }'
```

### 4. مشاهده Dashboard

```bash
curl http://localhost:8000/api/unified/stats?tenant_id=1
```

---

## 📈 نتایج مورد انتظار

### قبل از سیستم یکپارچه

- ❌ لیدهای لینکدین بدون پیگیری
- ❌ لیدهای ربات بدون لینکدین
- ❌ هیچ سیستم نوتیفیکیشن خودکار
- ❌ گزارش‌دهی جداگانه

### بعد از سیستم یکپارچه

- ✅ همه لیدها در یک جا
- ✅ Follow-up خودکار (5 مرحله)
- ✅ نوتیفیکیشن املاک جدید
- ✅ Lead Scoring & Grading
- ✅ Dashboard یکپارچه
- ✅ افزایش Conversion Rate (تخمین: 30-40%)

---

## 🎓 آموزش کار با سیستم

### برای Agent (مشاور املاک)

1. **صبح**: چک کردن Dashboard
   - چند لید جدید داریم؟
   - چند تا A-Grade هستند؟
   - چند follow-up امروز باید انجام شود؟

2. **افزودن ملک جدید**:
   - ملک را در سیستم اضافه کنید
   - سیستم خودکار لیدهای مچ را پیدا می‌کند
   - نوتیفیکیشن اتوماتیک ارسال می‌شود

3. **پاسخ به لیدها**:
   - لیدها از طریق Telegram/WhatsApp پاسخ می‌دهند
   - سیستم خودکار امتیاز را آپدیت می‌کند
   - شما فقط به A-Grade و B-Grade لیدها فوکس کنید

### برای توسعه‌دهنده

1. **خواندن معماری**: `UNIFIED_PLATFORM_ARCHITECTURE.md`
2. **نصب**: `DEPLOYMENT_GUIDE_UNIFIED.md`
3. **توسعه**: کد تمیز و مستند شده است

---

## 🔮 امکانات آینده (Roadmap)

### فاز 1 (فعلی) ✅
- [x] دیتابیس یکپارچه
- [x] Follow-up Engine
- [x] Property Matching
- [x] Lead Scoring

### فاز 2 (2 هفته آینده)
- [ ] Dashboard یکپارچه (React)
- [ ] Kanban Board برای لیدها
- [ ] Calendar Integration
- [ ] SMS Notifications

### فاز 3 (1 ماه آینده)
- [ ] AI Voice Calls
- [ ] Sentiment Analysis
- [ ] Predictive Lead Scoring (ML)
- [ ] A/B Testing برای پیام‌ها

---

## 🙏 سپاسگزاری

این سیستم با استفاده از:
- **FastAPI** - Backend Framework
- **PostgreSQL** - Database
- **Google Gemini** - AI للتولید الرسائل
- **APScheduler** - Background Jobs
- **SQLAlchemy** - ORM

---

## 📞 پشتیبانی

سوالات؟ مشکلی پیش آمد؟

📧 Email: info@artinsmartagent.com  
🌐 Website: https://www.artinsmartagent.com

---

**تاریخ تکمیل**: 10 دسامبر 2025  
**نسخه**: 1.0.0  
**وضعیت**: ✅ آماده برای استفاده

🎉 **سیستم یکپارچه ArtinSmartRealty با موفقیت پیاده‌سازی شد!**
