# 🚨 فیکس فوری بات - مشکلات اصلی

## مشکل 1: حلقه بی‌نهایت شماره تلفن ❌

**علت:** بعد از `CAPTURE_CONTACT`، بات به `HARD_GATE` می‌ره که **دوباره شماره می‌خواد**!

```python
# فلو فعلی (اشتباه):
CAPTURING_NAME → CAPTURE_CONTACT → **HARD_GATE** (دوباره شماره می‌خواد!)

# فلو درست:
COLLECTING_NAME → CAPTURE_CONTACT (شماره) → **WARMUP** (هدف چیه؟)
```

**راه حل:** در `_handle_capture_contact`، بعد از گرفتن شماره:
```python
# OLD:
next_state=ConversationState.WARMUP  # ✅ این درسته

# اما بات دوباره به HARD_GATE می‌ره چون جایی دیگه state رو عوض می‌کنه!
```

---

## مشکل 2: هیچ وقت ملک نشون نمیده ❌

**علت:** تابع `_handle_engagement` فقط سوال می‌پرسه، **هیچ وقت املاک database رو نمی‌خونه**!

```python
# کد فعلی در engagement:
async def _handle_engagement(...):
    # فقط سوال می‌پرسه
    # هیچ جایی query به properties table نزده!
```

**راه حل:** باید property search اضافه کنیم:
```python
async def show_properties(lead):
    # Query properties table
    properties = db.query(Property).filter(
        Property.tenant_id == lead.tenant_id,
        Property.price <= lead.budget_max  # if budget collected
    ).limit(5).all()
    
    # نمایش با عکس + ROI
    for prop in properties:
        send_property_card(prop)
```

---

## مشکل 3: جلسه مشاوره کار نمیکنه ❌

**پیام فعلی:**
```
⏰ در حال حاضر وقت خالی نداریم. لطفاً مستقیماً با ما تماس بگیرید یا بعداً تلاش کنید.
```

**علت:** جدول `agent_availability` خالیه!

```sql
SELECT * FROM agent_availability WHERE tenant_id = 1;
-- Result: 0 rows
```

**راه حل:**
1. یا پر کن جدول با availability واقعی
2. یا لینک Calendly بده:
   ```python
   "برای جلسه مشاوره رایگان، روی لینک زیر کلیک کنید:\n"
   "👉 https://calendly.com/taranteen/consultation"
   ```

---

## فیکس سریع - 3 تغییر اساسی:

### 1️⃣ حذف HARD_GATE از فلو

```python
# File: backend/brain.py
# در _handle_capture_contact (خط ~2390)

# BEFORE:
return BrainResponse(
    message=warmup_msg.get(lang, warmup_msg[Language.EN]),
    next_state=ConversationState.WARMUP,  # این درسته
    lead_updates=lead_updates,
    buttons=buttons.get(lang, buttons[Language.EN])
)

# هیچ تغییری نمی‌خواد! مشکل جای دیگه‌ست
```

**مشکل واقعی:** در `_handle_warmup` یا handlers دیگه، state به `HARD_GATE` set میشه.

**فیکس:** پیدا کن کجا `HARD_GATE` set میشه و حذفش کن!

```bash
# جستجو:
grep -r "HARD_GATE" backend/brain.py
```

---

### 2️⃣ اضافه کردن نمایش املاک

```python
# File: backend/brain.py
# در _handle_slot_filling یا _handle_engagement

async def _show_properties(self, lead: Lead, lang: Language):
    """نمایش املاک مناسب از database"""
    
    # Query properties
    async with async_session() as db:
        query = select(Property).where(
            Property.tenant_id == lead.tenant_id
        )
        
        # فیلتر بر اساس budget
        if lead.budget_max:
            query = query.where(Property.price <= lead.budget_max)
        
        # فیلتر بر اساس نوع معامله
        if lead.transaction_type:
            query = query.where(Property.transaction_type == lead.transaction_type)
        
        result = await db.execute(query.limit(5))
        properties = result.scalars().all()
    
    if not properties:
        return "متاسفانه ملک مناسبی در database نیست"
    
    # ساخت پیام با املاک
    message = f"🏠 **{len(properties)} ملک مناسب برای شما:**\n\n"
    
    media_files = []
    for prop in properties:
        message += f"📍 **{prop.name}**\n"
        message += f"💰 قیمت: ${prop.price:,}\n"
        message += f"📏 متراژ: {prop.area} متر\n"
        message += f"🛏️ {prop.bedrooms} خواب\n"
        
        # محاسبه ROI
        if prop.annual_rental_income:
            roi = (prop.annual_rental_income / prop.price) * 100
            message += f"📈 ROI: {roi:.1f}%\n"
        
        message += "\n"
        
        # اضافه کردن عکس
        if prop.image_url:
            media_files.append({
                "type": "photo",
                "url": prop.image_url,
                "caption": f"{prop.name} - ${prop.price:,}"
            })
    
    return BrainResponse(
        message=message,
        next_state=ConversationState.VALUE_PROPOSITION,
        lead_updates={},
        media_files=media_files,
        buttons=[
            {"text": "📅 رزرو مشاوره", "callback_data": "schedule_consultation"},
            {"text": "🔍 جزئیات بیشتر", "callback_data": "more_details"}
        ]
    )
```

---

### 3️⃣ فیکس جلسه مشاوره

```python
# File: backend/brain.py
# در _handle_schedule

async def _handle_schedule(self, lang: Language, callback_data: Optional[str], lead: Lead):
    """Book consultation - simple version with Calendly link"""
    
    calendly_link = "https://calendly.com/taranteen-realty/30min"
    
    messages = {
        Language.FA: (
            f"🎉 عالیه {lead.name}!\n\n"
            f"برای رزرو جلسه مشاوره **رایگان 30 دقیقه‌ای** با متخصصین ما،\n"
            f"روی لینک زیر کلیک کنید:\n\n"
            f"👉 {calendly_link}\n\n"
            f"یا اگر ترجیح میدید، مستقیماً با ما تماس بگیرید:\n"
            f"📞 **+971 50 503 7158**\n\n"
            f"منتظر شنیدن صدای شما هستیم! 🙏"
        ),
        Language.EN: (
            f"🎉 Great {lead.name}!\n\n"
            f"To book your **FREE 30-minute consultation** with our experts,\n"
            f"click the link below:\n\n"
            f"👉 {calendly_link}\n\n"
            f"Or if you prefer, call us directly:\n"
            f"📞 **+971 50 503 7158**\n\n"
            f"Looking forward to hearing from you! 🙏"
        )
    }
    
    return BrainResponse(
        message=messages.get(lang, messages[Language.EN]),
        next_state=ConversationState.HANDOFF_SCHEDULE,
        lead_updates={"status": LeadStatus.CONSULTATION_SCHEDULED},
        buttons=[]
    )
```

---

## اجرای فیکس:

```bash
# 1. پیدا کردن جایی که HARD_GATE set میشه
cd /opt/ArtinSmartRealtyPro/backend
grep -n "HARD_GATE" brain.py

# 2. اضافه کردن property search
# (کد بالا رو به brain.py اضافه کن)

# 3. آپدیت جلسه مشاوره با Calendly
# (جایگزین کد _handle_schedule)

# 4. Rebuild
docker-compose up -d --build backend
```

---

## تست فلو جدید:

```
کاربر: /start
بات: اسمت چیه؟

کاربر: علی
بات: شماره‌ات؟

کاربر: [shares contact]
بات: هدفت چیه؟ [دکمه‌ها: سرمایه‌گذاری | زندگی | اقامت]

کاربر: [کلیک سرمایه‌گذاری]
بات: 🏠 **5 ملک مناسب برای شما:**
     [عکس‌ها + قیمت + ROI]
     دکمه: 📅 رزرو مشاوره

کاربر: [کلیک رزرو مشاوره]
بات: لینک Calendly + شماره تماس
```

---

## اولویت‌بندی:

1. **CRITICAL:** حذف حلقه HARD_GATE (5 دقیقه)
2. **HIGH:** نمایش املاک از database (30 دقیقه)
3. **MEDIUM:** فیکس جلسه مشاوره با Calendly (10 دقیقه)

**زمان تخمینی کل:** 45 دقیقه
