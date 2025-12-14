# معماری پلتفرم یکپارچه - ArtinSmartRealty Unified

## 🎯 هدف پروژه

ادغام دو سیستم:
1. **AI Lead Scraper** - جمع‌آوری لید از لینکدین
2. **ArtinSmartRealty Bot** - کوالیفای لیدها از طریق تلگرام/واتساپ

به یک **پلتفرم واحد هوشمند** با قابلیت Follow-up خودکار

---

## 📊 معماری کلی سیستم

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UNIFIED DASHBOARD (Frontend)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ LinkedIn     │  │ Bot Leads    │  │ Follow-up    │              │
│  │ Leads        │  │ (Telegram/   │  │ Campaigns    │              │
│  │              │  │  WhatsApp)   │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Lead Scoring │  │ Property     │  │ Analytics    │              │
│  │ & Grading    │  │ Matching     │  │ & Reports    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      UNIFIED BACKEND API                             │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │              LEAD MANAGEMENT SYSTEM                       │       │
│  │  • Unified Lead Database (LinkedIn + Bot)                │       │
│  │  • Lead Status Pipeline (New → Qualified → Won/Lost)     │       │
│  │  • Lead Scoring & Grading                                │       │
│  │  • Duplicate Detection                                   │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │           INTELLIGENT FOLLOW-UP SYSTEM                    │       │
│  │  • Auto-message LinkedIn leads via Telegram/WhatsApp     │       │
│  │  • Qualify leads through conversation                    │       │
│  │  • Property matching engine                              │       │
│  │  • Re-engagement when new properties added               │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │              AI BRAIN (Google Gemini)                     │       │
│  │  • Lead qualification                                     │       │
│  │  • Personalized messaging                                │       │
│  │  • Property recommendation                               │       │
│  │  • Re-engagement triggers                                │       │
│  └──────────────────────────────────────────────────────────┘       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  LinkedIn    │      │  Telegram    │      │  WhatsApp    │
│  Scraper     │      │  Bot         │      │  Bot         │
│  (Extension) │      │              │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
```

---

## 🗄️ ساختار دیتابیس یکپارچه

### جدول اصلی: `unified_leads`

```sql
CREATE TABLE unified_leads (
    -- شناسایی
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER,  -- برای multi-tenant
    
    -- اطلاعات تماس
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    linkedin_url VARCHAR(500) UNIQUE,
    telegram_user_id BIGINT UNIQUE,
    whatsapp_number VARCHAR(50) UNIQUE,
    
    -- منبع لید
    source VARCHAR(50), -- 'linkedin' | 'telegram' | 'whatsapp' | 'manual'
    
    -- وضعیت در پایپلاین
    status VARCHAR(50), -- 'new' | 'contacted' | 'qualified' | 'viewing_scheduled' | 'won' | 'lost'
    
    -- امتیاز و درجه‌بندی
    lead_score INTEGER DEFAULT 0,  -- 0-100
    grade VARCHAR(10),  -- 'A' | 'B' | 'C' | 'D'
    
    -- اطلاعات حرفه‌ای (از لینکدین)
    job_title VARCHAR(255),
    company VARCHAR(255),
    about TEXT,
    location VARCHAR(255),
    
    -- نیازها و علایق (از کوالیفیکیشن)
    transaction_type VARCHAR(20), -- 'buy' | 'rent'
    property_type VARCHAR(50),
    budget_min DECIMAL(15,2),
    budget_max DECIMAL(15,2),
    bedrooms INTEGER,
    preferred_locations JSON,
    purpose VARCHAR(50), -- 'investment' | 'living' | 'residency'
    pain_points JSON,
    
    -- Follow-up
    last_contacted_at TIMESTAMP,
    last_message TEXT,
    next_followup_at TIMESTAMP,
    followup_count INTEGER DEFAULT 0,
    conversation_state VARCHAR(50),
    
    -- Property Matching
    matched_properties JSON,  -- لیست IDهای املاکی که مچ شدند
    viewed_properties JSON,   -- لیست IDهای املاکی که دیده شدند
    
    -- زمان‌ها
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Index برای جستجوی سریع
CREATE INDEX idx_leads_status ON unified_leads(status);
CREATE INDEX idx_leads_score ON unified_leads(lead_score DESC);
CREATE INDEX idx_leads_source ON unified_leads(source);
CREATE INDEX idx_leads_next_followup ON unified_leads(next_followup_at);
```

### جدول تاریخچه تعاملات: `lead_interactions`

```sql
CREATE TABLE lead_interactions (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL,
    
    channel VARCHAR(50), -- 'linkedin' | 'telegram' | 'whatsapp' | 'email'
    direction VARCHAR(20), -- 'inbound' | 'outbound'
    message_text TEXT,
    ai_generated BOOLEAN DEFAULT FALSE,
    
    -- برای پیام‌های خودکار
    campaign_id INTEGER,  -- اگر بخشی از کمپین follow-up باشد
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (lead_id) REFERENCES unified_leads(id)
);
```

### جدول کمپین‌های Follow-up: `followup_campaigns`

```sql
CREATE TABLE followup_campaigns (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    
    name VARCHAR(255),
    description TEXT,
    
    -- تریگر کمپین
    trigger_type VARCHAR(50), -- 'new_property' | 'scheduled' | 'manual'
    
    -- فیلتر لیدها
    target_status VARCHAR(50),  -- فقط لیدهای با این status
    min_score INTEGER,          -- حداقل امتیاز
    
    -- محتوای پیام
    message_template TEXT,
    
    -- زمان‌بندی
    scheduled_at TIMESTAMP,
    executed_at TIMESTAMP,
    
    -- آمار
    total_sent INTEGER DEFAULT 0,
    total_replied INTEGER DEFAULT 0,
    
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
```

---

## 🔄 جریان کاری (Workflow)

### 1️⃣ جمع‌آوری لید از لینکدین

```
LinkedIn Profile
      │
      ▼
Chrome Extension Scrapes
      │
      ├─► Name, Job Title, Company
      ├─► About Section
      ├─► Recent Posts
      └─► Profile URL
      │
      ▼
Save to unified_leads
      │
      ├─► source = 'linkedin'
      ├─► status = 'new'
      └─► lead_score = Auto-calculate
      │
      ▼
Trigger Auto Follow-up Campaign
```

### 2️⃣ کوالیفای لید از طریق ربات

```
User Messages Bot (Telegram/WhatsApp)
      │
      ▼
Check if exists in unified_leads
      │
      ├─► YES: Update existing lead
      │         ├─► Merge data
      │         ├─► Update status
      │         └─► Increase lead_score
      │
      └─► NO:  Create new lead
                ├─► source = 'telegram' or 'whatsapp'
                └─► status = 'new'
      │
      ▼
AI Conversation (Gemini)
      │
      ├─► Extract: Budget, Property Type, Location
      ├─► Identify: Pain Points, Purpose
      └─► Calculate: Lead Score
      │
      ▼
Update unified_leads
      │
      └─► status = 'qualified'
      │
      ▼
Property Matching Engine
      │
      └─► Find properties matching criteria
      │
      ▼
Send Property Recommendations
```

### 3️⃣ سیستم Follow-up خودکار

```
Scheduler (Runs Every Hour)
      │
      ▼
Query unified_leads WHERE:
      │
      ├─► status = 'new' OR 'contacted'
      ├─► next_followup_at <= NOW()
      └─► followup_count < 5
      │
      ▼
For Each Lead:
      │
      ├─► Generate Personalized Message (AI)
      │         │
      │         └─► Use: name, job_title, about, pain_points
      │
      ├─► Send via Telegram/WhatsApp
      │
      ├─► Log in lead_interactions
      │
      └─► Update:
                ├─► last_contacted_at = NOW()
                ├─► followup_count += 1
                └─► next_followup_at = NOW() + 3 days
```

### 4️⃣ نوتیفیکیشن املاک جدید

```
New Property Added to Database
      │
      ▼
Property Matching Engine
      │
      ├─► Query unified_leads WHERE:
      │         │
      │         ├─► status != 'won' AND status != 'lost'
      │         ├─► budget_min <= property.price <= budget_max
      │         ├─► property_type = property.type
      │         └─► preferred_locations CONTAINS property.location
      │
      └─► For Each Matched Lead:
                │
                ├─► Generate Personalized Message
                │         │
                │         └─► "سلام {name}، ملک جدیدی مطابق با سلیقه شما..."
                │
                ├─► Send via Telegram/WhatsApp
                │
                └─► Update matched_properties JSON
```

---

## 🎯 سیستم Lead Scoring

### امتیازدهی خودکار (0-100)

```python
def calculate_lead_score(lead):
    score = 0
    
    # 1. کامل بودن اطلاعات (20 امتیاز)
    if lead.phone: score += 5
    if lead.email: score += 5
    if lead.linkedin_url: score += 5
    if lead.job_title: score += 5
    
    # 2. تعامل (30 امتیاز)
    if lead.followup_count > 0: score += 10
    if lead.replied_to_bot: score += 20
    
    # 3. کوالیفیکیشن (30 امتیاز)
    if lead.budget_min and lead.budget_max: score += 10
    if lead.property_type: score += 10
    if lead.preferred_locations: score += 10
    
    # 4. Engagement (20 امتیاز)
    if lead.viewed_properties: score += 10
    if lead.scheduled_viewing: score += 10
    
    return score

def assign_grade(score):
    if score >= 80: return 'A'  # Hot Lead
    if score >= 60: return 'B'  # Warm Lead
    if score >= 40: return 'C'  # Cold Lead
    return 'D'  # Very Cold
```

---

## 🤖 پیام‌رسانی هوشمند

### قالب پیام برای لیدهای لینکدین

```python
# پیام اول - معرفی
message_template = """
سلام {name} عزیز! 👋

از طریق لینکدین دیدم که در {company} به عنوان {job_title} فعالیت می‌کنید.

{personalized_hook}

من دستیار هوشمند {agent_name} هستم - مشاور املاک در دبی.

{pain_solution}

آیا وقت دارید که در مورد فرصت‌های سرمایه‌گذاری در دبی صحبت کنیم؟
"""

# پیام دوم - Follow-up (اگر جواب نداد)
followup_1 = """
سلام دوباره {name}! 🙂

می‌دونم شلوغ هستید، اما {urgency_trigger}

آیا علاقه‌مندید {specific_offer}؟
"""

# پیام سوم - آخرین تلاش
followup_2 = """
{name} عزیز،

این آخرین پیام منه. اگر الان مناسب نیست، مشکلی نیست!

اما اگر روزی {future_need}، حتما بهم پیام بده 😊
"""
```

---

## 📈 داشبورد یکپارچه

### KPIs اصلی

```
┌─────────────────────────────────────────────────────────┐
│  📊 LEAD OVERVIEW                                        │
│                                                          │
│  Total Leads: 1,250                                      │
│  ├─ LinkedIn: 800  (64%)                                │
│  ├─ Telegram: 350  (28%)                                │
│  └─ WhatsApp: 100  (8%)                                 │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ New      │  │ Qualified│  │ Won      │              │
│  │ 450      │  │ 320      │  │ 45       │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│                                                          │
│  Lead Grading:                                           │
│  🔥 A-Grade: 120 leads  (Hot)                           │
│  🌡️  B-Grade: 380 leads  (Warm)                          │
│  ❄️  C-Grade: 520 leads  (Cold)                          │
│  🧊 D-Grade: 230 leads  (Very Cold)                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  🤖 FOLLOW-UP AUTOMATION                                 │
│                                                          │
│  Active Campaigns: 3                                     │
│                                                          │
│  Campaign 1: "LinkedIn Lead Warmup"                      │
│  ├─ Target: LinkedIn leads, Score < 40                  │
│  ├─ Sent: 245 messages                                  │
│  └─ Replied: 67 (27% response rate)                     │
│                                                          │
│  Campaign 2: "New Property Alert"                        │
│  ├─ Trigger: New property added                         │
│  ├─ Matched: 89 leads                                   │
│  └─ Sent: 89 messages                                   │
│                                                          │
│  Next Scheduled Follow-ups:                              │
│  ├─ Today: 34 leads                                     │
│  ├─ This Week: 128 leads                                │
│  └─ This Month: 456 leads                               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  🏠 PROPERTY MATCHING                                    │
│                                                          │
│  Total Properties: 450                                   │
│                                                          │
│  Property #203: Luxury Villa, Palm Jumeirah              │
│  ├─ Price: $2.5M                                        │
│  ├─ Matched Leads: 12                                   │
│  ├─ Viewed: 5                                           │
│  └─ Scheduled Viewings: 2                               │
│                                                          │
│  Top Matched Properties:                                 │
│  1. Villa, Palm Jumeirah - 12 matches                   │
│  2. Apartment, Dubai Marina - 18 matches                │
│  3. Penthouse, Downtown - 8 matches                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ پیاده‌سازی گام به گام

### فاز 1: ادغام دیتابیس (1-2 روز)

1. ✅ ایجاد جدول `unified_leads`
2. ✅ Migrate داده‌های LinkedIn Scraper
3. ✅ Migrate داده‌های ArtinSmartRealty Bot
4. ✅ ایجاد Duplicate Detection Logic

### فاز 2: سیستم Follow-up (2-3 روز)

1. ✅ ایجاد `followup_campaigns` table
2. ✅ پیاده‌سازی Scheduler (Celery or APScheduler)
3. ✅ ایجاد AI Message Generator
4. ✅ اتصال به Telegram/WhatsApp

### فاز 3: Property Matching Engine (2-3 روز)

1. ✅ الگوریتم Matching (budget, type, location)
2. ✅ Auto-notify لیدها با املاک جدید
3. ✅ Track viewed properties
4. ✅ Smart Re-engagement

### فاز 4: Lead Scoring System (1-2 روز)

1. ✅ پیاده‌سازی Auto-scoring
2. ✅ Grade Assignment (A/B/C/D)
3. ✅ Re-calculate on every interaction

### فاز 5: Unified Dashboard (3-4 روز)

1. ✅ ادغام UI دو سیستم
2. ✅ Lead Pipeline View (Kanban)
3. ✅ Campaign Management UI
4. ✅ Analytics & Reports

---

## 🚀 نکات پیاده‌سازی

### 1. Duplicate Detection

```python
async def find_or_create_lead(data):
    # اول چک کن با لینکدین
    if data.get('linkedin_url'):
        lead = await db.query(UnifiedLead).filter(
            linkedin_url=data['linkedin_url']
        ).first()
        if lead:
            return lead, False  # Found, not created
    
    # اگر نبود، چک کن با تلگرام
    if data.get('telegram_user_id'):
        lead = await db.query(UnifiedLead).filter(
            telegram_user_id=data['telegram_user_id']
        ).first()
        if lead:
            return lead, False
    
    # اگر نبود، چک کن با شماره
    if data.get('phone'):
        lead = await db.query(UnifiedLead).filter(
            phone=data['phone']
        ).first()
        if lead:
            return lead, False
    
    # اگر هیچکدام نبود، بساز
    lead = UnifiedLead(**data)
    await db.add(lead)
    await db.commit()
    return lead, True  # Created
```

### 2. Smart Follow-up Scheduler

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', hours=1)
async def run_followup_campaigns():
    # پیدا کردن لیدهایی که نیاز به follow-up دارند
    leads = await db.query(UnifiedLead).filter(
        UnifiedLead.next_followup_at <= datetime.now(),
        UnifiedLead.status.in_(['new', 'contacted']),
        UnifiedLead.followup_count < 5
    ).all()
    
    for lead in leads:
        # تولید پیام شخصی‌سازی شده
        message = await generate_personalized_message(lead)
        
        # ارسال
        if lead.telegram_user_id:
            await send_telegram_message(lead.telegram_user_id, message)
        elif lead.whatsapp_number:
            await send_whatsapp_message(lead.whatsapp_number, message)
        
        # آپدیت لید
        lead.last_contacted_at = datetime.now()
        lead.followup_count += 1
        lead.next_followup_at = datetime.now() + timedelta(days=3)
        await db.commit()
```

### 3. Property Matching on New Property

```python
async def on_property_added(property_id):
    property = await db.query(Property).filter(id=property_id).first()
    
    # پیدا کردن لیدهای مچ
    matched_leads = await db.query(UnifiedLead).filter(
        UnifiedLead.status.not_in(['won', 'lost']),
        UnifiedLead.budget_min <= property.price,
        UnifiedLead.budget_max >= property.price,
        UnifiedLead.property_type == property.type
    ).all()
    
    for lead in matched_leads:
        # اگر لوکیشن هم مچ باشد
        if property.location in lead.preferred_locations:
            message = f"""
            🏠 ملک جدید مطابق سلیقه شما!
            
            سلام {lead.name}،
            
            ملک جدیدی اضافه شد که دقیقا با نیازهای شما مچ می‌کنه:
            
            📍 {property.location}
            💰 ${property.price:,.0f}
            🛏️ {property.bedrooms} خوابه
            
            آیا میخوای جزئیات بیشتر رو ببینی؟
            """
            
            await send_message_to_lead(lead, message)
            
            # آپدیت matched_properties
            if not lead.matched_properties:
                lead.matched_properties = []
            lead.matched_properties.append(property_id)
            await db.commit()
```

---

## ✅ نتیجه نهایی

با این معماری:

✅ **یک پلتفرم واحد** - همه لیدها در یک جا  
✅ **Follow-up خودکار** - لیدهای لینکدین به صورت اتوماتیک پیگیری می‌شوند  
✅ **کوالیفیکیشن هوشمند** - AI لیدها را درجه‌بندی می‌کند  
✅ **Property Matching** - لیدها اتوماتیک املاک مناسب دریافت می‌کنند  
✅ **Re-engagement** - وقتی ملک جدید اضافه شد، لیدهای مرتبط نوتیف می‌شوند  
✅ **Analytics** - داشبورد جامع با گزارش‌های کامل  

---

**زمان پیاده‌سازی تخمینی**: 10-12 روز کاری
