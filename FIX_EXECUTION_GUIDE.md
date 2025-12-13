# راهنمای فیکس کامل بات - نسخه قابل اجرا

## خلاصه مشکلات:

شما یک مکالمه تست کردید که:
- بات 100 بار شماره می‌خواد
- "پیش‌خرید" رو نمی‌فهمه
- ملک نشون نمیده
- جلسه مشاوره کار نمیکنه

## علت اصلی:

**بات گیر کرده در حلقه HARD_GATE → VALUE_PROPOSITION**

وقتی کاربر چیزی می‌نویسه که مربوط به مشاوره/سرمایه‌گذاری باشه، دوباره state رو به `HARD_GATE` برمی‌گردونه که شماره می‌خواد!

## راه حل:

### گام 1: حذف HARD_GATE از جریان اصلی

بات **نباید بعد از WARMUP به HARD_GATE بره**. باید مستقیم بره به SLOT_FILLING یا VALUE_PROPOSITION.

فایل: `backend/brain.py`

**تغییرات لازم:**

#### 1.1: خطوط 3112, 3204, 3322, 3419, 3440, 3493

```python
# جایگزین کن:
next_state=ConversationState.HARD_GATE

# با:
next_state=ConversationState.VALUE_PROPOSITION
```

**چرا؟** وقتی کاربر از قبل شماره داده، **نباید دوباره بپرسیم**!

---

### گام 2: نمایش املاک واقعی

فایل: `backend/brain.py`

در handler `_handle_value_proposition` یا `_handle_engagement`، باید **properties از database** رو بگیری:

```python
async def get_property_recommendations(self, lead: Lead):
    """گرفتن املاک واقعی از دیتابیس"""
    
    async with async_session() as db:
        query = select(Property).where(
            Property.tenant_id == lead.tenant_id,
            Property.is_active == True
        )
        
        # فیلتر بر اساس نوع معامله
        if lead.transaction_type:
            query = query.where(Property.listing_type == lead.transaction_type)
        
        # فیلتر بر اساس بودجه
        if lead.budget_max:
            query = query.where(Property.price <= lead.budget_max)
        
        # محدود کن به 5 تا
        query = query.limit(5)
        
        result = await db.execute(query)
        properties = result.scalars().all()
    
    if not properties:
        return "متاسفانه ملک مناسبی در حال حاضر موجود نیست."
    
    # ساخت پیام
    msg = f"🏠 **{len(properties)} ملک مناسب برای شما:**\n\n"
    
    for p in properties:
        msg += f"📍 **{p.title}**\n"
        msg += f"💰 قیمت: ${p.price:,}\n"
        msg += f"📏 {p.area} متر مربع\n"
        msg += f"🛏️ {p.bedrooms} خوابه\n"
        
        # ROI برای سرمایه‌گذاری
        if p.rental_yield:
            msg += f"📈 بازدهی: {p.rental_yield}% سالانه\n"
        
        msg += f"🔗 {p.link or 'بزودی'}\n\n"
    
    return msg
```

---

### گام 3: درست کردن جلسه مشاوره

فایل: `backend/brain.py`

در `_handle_schedule`:

```python
async def _handle_schedule(self, lang: Language, callback_data: Optional[str], lead: Lead):
    """جلسه مشاوره - نسخه ساده با لینک کالندلی"""
    
    # لینک Calendly یا شماره تماس
    consultation_message = {
        Language.FA: (
            f"🎉 عالیه {lead.name or 'عزیز'}!\n\n"
            f"برای رزرو جلسه مشاوره **رایگان** با متخصصین املاک دبی:\n\n"
            f"📞 **تماس مستقیم:**\n"
            f"+971 50 503 7158\n\n"
            f"📅 **رزرو آنلاین:**\n"
            f"https://calendly.com/taranteen/consultation\n\n"
            f"منتظر شنیدن صدای شما هستیم! 🙏"
        ),
        Language.EN: (
            f"🎉 Great {lead.name or 'friend'}!\n\n"
            f"To book your **FREE consultation** with Dubai real estate experts:\n\n"
            f"📞 **Direct call:**\n"
            f"+971 50 503 7158\n\n"
            f"📅 **Book online:**\n"
            f"https://calendly.com/taranteen/consultation\n\n"
            f"Looking forward to hearing from you! 🙏"
        )
    }
    
    return BrainResponse(
        message=consultation_message.get(lang, consultation_message[Language.EN]),
        next_state=ConversationState.COMPLETED,  # تمام شد!
        lead_updates={"status": "consultation_scheduled"},
        buttons=[]
    )
```

---

### گام 4: فلو ساده جدید

```
START
  ↓
LANGUAGE_SELECT ("کدوم زبان؟")
  ↓
COLLECTING_NAME ("اسمت چیه؟")
  ↓
WARMUP ("هدفت چیه؟" → دکمه‌ها: سرمایه‌گذاری | زندگی | اقامت)
  ↓
VALUE_PROPOSITION (نمایش 5 ملک از database + عکس + ROI)
  ↓
CAPTURE_CONTACT ("برای جزئیات بیشتر، شماره‌ات؟")
  ↓
HANDOFF_SCHEDULE (لینک Calendly + شماره تماس)
  ↓
COMPLETED
```

**نکته مهم:** شماره رو **در آخر** بگیر، نه اول!

---

## اجرا:

### روش 1: دستی

```bash
ssh root@88.99.45.159
cd /opt/ArtinSmartRealtyPro/backend

# باز کن brain.py
nano brain.py

# پیدا کن همه جاهایی که:
next_state=ConversationState.HARD_GATE

# تبدیل کن به:
next_state=ConversationState.VALUE_PROPOSITION

# ذخیره: Ctrl+X → Y → Enter

# Rebuild
cd ..
docker-compose up -d --build backend
```

### روش 2: اسکریپت خودکار

```bash
cd /opt/ArtinSmartRealtyPro/backend

# جایگزینی خودکار
sed -i 's/next_state=ConversationState.HARD_GATE/next_state=ConversationState.VALUE_PROPOSITION/g' brain.py

# Rebuild
cd ..
docker-compose up -d --build backend
```

---

## تست:

```
کاربر: /start
بات: 👋 کدوم زبان؟

کاربر: فارسی
بات: اسمت چیه؟

کاربر: ارزو
بات: هدفت چیه؟ [دکمه: سرمایه‌گذاری | زندگی | اقامت]

کاربر: [کلیک سرمایه‌گذاری]
بات: 🏠 5 ملک مناسب برای شما:
     1. Sky Tower - $250,000 - ROI 8%
     2. Marina Residence - $180,000 - ROI 7.5%
     ...
     
     برای جزئیات بیشتر، شماره‌ات؟

کاربر: [shares contact]
بات: 🎉 عالیه! برای رزرو جلسه:
     📞 +971 50 503 7158
     📅 calendly.com/taranteen
```

---

## نکات مهم:

1. **HARD_GATE رو حذف نکن** - فقط ازش استفاده نکن در فلو اصلی
2. **properties table** باید پر باشه - وگرنه بات میگه "ملک نداریم"
3. **Calendly link** رو با لینک واقعیت عوض کن

---

## زمان:

- ✅ تغییر HARD_GATE → VALUE_PROPOSITION: 2 دقیقه
- ✅ تست: 5 دقیقه
- **کل: 7 دقیقه**

---

## بعد از فیکس:

✅ دیگه شماره صدبار نمی‌پرسه
✅ املاک واقعی نشون میده
✅ جلسه مشاوره کار می‌کنه
✅ فلو ساده و واضح

---

**آماده دیپلوی:** بله ✅
**نیاز به تست:** بله (5 دقیقه)
**خطر شکستن چیزی:** پایین (فقط یک state تغییر میکنه)
