# گزارش مشکلات ربات تلگرام - 14 دسامبر 2025

## مشکلات شناسایی شده از گفتگوی واقعی

### ❌ مشکل 1: پیام "ملک نداری" در حالی که ملک دارد
**خط لاگ:**
```
TaranteenBot: 📋 الان ملک مشخصی در سیستم ندارم، اما taranteen متخصص پیدا کردن املاک خارج از بازاره!
```

**بعد از آن:**
```
TaranteenBot: 🏠 **2 ملک مناسب برای شما:**
1. **Sky Gardens - Off-Plan**
2. **Marina Heights Luxury Tower**
```

**علت:** تابع `get_property_recommendations()` در خط 1806 فایل `brain.py` این پیام را نشان می‌دهد حتی وقتی ملک وجود دارد.

**محل کد:**
```python
# Line 1806 - brain.py
if not properties and not projects:
    messages = {
        Language.FA: f"📋 الان ملک مشخصی در سیستم ندارم، اما {self.agent_name}..."
```

**راه حل:**
این پیام فقط باید زمانی نمایش داده شود که **هیچ ملکی** در سیستم نباشد، نه وقتی که املاک وجود دارند.

---

### ❌ مشکل 2: PDF گزارش ROI ارسال نمی‌شود
**گفتگوی کاربر:**
```
A.m: خب roi بذه
TaranteenBot: بله حتما! ROI در دبی بین 7 تا 10 درصد سالانه است...

A.m: قرار بود توی پی دی اف بنویسی بذی
A.m: قرار بود با ai انجام بدی و به من بدی
```

**مشکل:**
1. ربات فقط یک پیام متنی درباره ROI می‌فرستد
2. هیچ فایل PDF ارسال نمی‌شود
3. تابع `generate_roi_pdf()` هیچ‌جا صدا زده نمی‌شود

**کد مورد نیاز:**
```python
from roi_engine import generate_roi_pdf

# باید برای هر ملک یک PDF اختصاصی ساخته شود
pdf_buffer = await generate_roi_pdf(lead, property, tenant)
# سپس ارسال PDF از طریق تلگرام/واتساپ
```

**محل اضافه کردن:**
- وقتی کاربر روی یک ملک خاص کلیک می‌کند
- وقتی کاربر می‌گوید "roi بده" یا "pdf بده"
- در state `WARMUP` یا `VALUE_PROPOSITION`

---

### ❌ مشکل 3: تکرار مکرر لیست املاک
**گفتگو:**
```
[A.m می‌گوید: پیش خرید میخوام]
TaranteenBot: می‌بینم علاقه‌مندی! یه گزینه از بالا انتخاب کن

[A.m می‌گوید: چرا نوشتی ملک نداری...]
TaranteenBot: [دوباره همان 2 ملک را نشان می‌دهد]

[A.m می‌گوید: ای وای]
TaranteenBot: [بار سوم همان 2 ملک را نشان می‌دهد]
```

**علت:**
- هر بار که کاربر پیامی می‌فرستد، ربات لیست کامل املاک را دوباره می‌فرستد
- منطق `brain.py` به درستی context را حفظ نمی‌کند
- دکمه‌های تعاملی به درستی کار نمی‌کنند

**راه حل:**
```python
# چک کردن آیا املاک قبلاً نشان داده شده‌اند
conversation_data = lead.conversation_data or {}
if conversation_data.get("properties_shown"):
    # املاک را دوباره نشان نده
    # فقط به سوال کاربر پاسخ بده
    return await self.generate_ai_response(message, lead)
else:
    # اولین بار است - املاک را نشان بده
    conversation_data["properties_shown"] = True
```

---

### ❌ مشکل 4: عدم پاسخ به درخواست‌های خاص
**گفتگو:**
```
A.m: roi بذه
TaranteenBot: [پیام عمومی درباره ROI]

A.m: قرار بود با ai انجام بدی
TaranteenBot: [دوباره لیست املاک - بدون توجه به درخواست]
```

**علت:**
ربات AI intent detection ضعیفی دارد. وقتی کاربر چیز خاصی می‌خواهد (مثل PDF، ROI، جزئیات ملک)، ربات به جای پاسخ مستقیم، flow عمومی را دنبال می‌کند.

**راه حل:**
افزودن Intent Detection بهتر:

```python
# Check for specific intents
intents = {
    "roi_request": r'roi|بازده|سود|بازگشت|درآمد',
    "pdf_request": r'pdf|پی دی اف|فایل|گزارش|ریپورت',
    "property_details": r'جزئیات|مشخصات|اطلاعات|detail',
    "price_info": r'قیمت|price|هزینه|cost',
}

for intent, pattern in intents.items():
    if re.search(pattern, message, re.IGNORECASE):
        return await self._handle_intent(intent, lead, property_id)
```

---

## اقدامات اصلاحی پیشنهادی

### Fix #1: حذف پیام گمراه‌کننده "ملک نداری"
**فایل:** `backend/brain.py` خط 1806

```python
# BEFORE:
if not properties and not projects:
    messages = {
        Language.FA: f"📋 الان ملک مشخصی در سیستم ندارم، اما {self.agent_name}..."
    }
    return messages.get(lang, messages[Language.EN])

# بعد از این، املاک را نشان می‌دهد - تناقض!

# AFTER:
if not properties and not projects:
    # فقط اگر واقعاً ملکی نیست
    return messages.get(lang, messages[Language.EN])

# اگر ملک دارد، مستقیماً لیست را نشان بده بدون پیام منفی
```

### Fix #2: افزودن قابلیت ارسال PDF
**فایل:** `backend/brain.py` + `backend/telegram_bot.py`

**مرحله 1:** تشخیص درخواست ROI/PDF
```python
# در تابع process_message
if re.search(r'roi|pdf|گزارش|ریپورت|بازده', message, re.IGNORECASE):
    # کاربر می‌خواهد PDF بگیرد
    if lead.phone and properties:
        # ارسال PDF برای ملک اول
        await self._send_roi_pdf(lead, properties[0])
        return "✅ گزارش ROI ارسال شد!"
    else:
        return "برای دریافت گزارش، ابتدا شماره تماستون رو به اشتراک بگذارید."
```

**مرحله 2:** تابع ارسال PDF
```python
async def _send_roi_pdf(self, lead: Lead, property_data: dict):
    """Generate and send ROI PDF to lead via Telegram/WhatsApp"""
    from roi_engine import generate_roi_pdf
    
    # ساخت PDF
    pdf_buffer = await generate_roi_pdf(lead, property_data, self.tenant)
    
    # ارسال از طریق تلگرام
    if lead.telegram_chat_id:
        await telegram_bot.send_document(
            chat_id=lead.telegram_chat_id,
            document=pdf_buffer,
            filename=f"ROI_Report_{property_data['name']}.pdf",
            caption=f"📊 گزارش ROI اختصاصی برای {property_data['name']}"
        )
    
    # ارسال از طریق واتساپ
    if lead.whatsapp_phone:
        await whatsapp_bot.send_document(...)
```

### Fix #3: جلوگیری از تکرار لیست املاک
**فایل:** `backend/brain.py`

```python
async def _handle_warmup(self, lang, message, callback_data, lead, lead_updates):
    conversation_data = lead.conversation_data or {}
    
    # چک کردن آیا املاک قبلاً نشان داده شده
    if conversation_data.get("properties_shown"):
        # املاک قبلاً نمایش داده شده - فقط به سوال پاسخ بده
        if message and not callback_data:
            ai_response = await self.generate_ai_response(message, lead)
            return BrainResponse(
                message=ai_response,
                next_state=ConversationState.WARMUP,
                lead_updates=lead_updates
            )
    
    # اولین بار است - املاک را نشان بده
    properties_msg = await self.get_property_recommendations(lead)
    conversation_data["properties_shown"] = True
    
    return BrainResponse(
        message=properties_msg,
        next_state=ConversationState.VALUE_PROPOSITION,
        lead_updates={**lead_updates, "conversation_data": conversation_data}
    )
```

### Fix #4: Intent Detection بهتر
**فایل:** `backend/brain.py`

```python
async def _detect_user_intent(self, message: str, lang: Language) -> Optional[str]:
    """Detect user's intent from message"""
    
    intents = {
        "roi_request": {
            Language.FA: r'roi|بازده|سود|بازگشت|درآمد|سرمایه',
            Language.EN: r'roi|return|profit|yield|income',
            Language.AR: r'عائد|ربح|دخل',
            Language.RU: r'доход|прибыль|рентабельность'
        },
        "pdf_request": {
            Language.FA: r'pdf|پی دی اف|فایل|گزارش|ریپورت|مدرک',
            Language.EN: r'pdf|file|report|document|brochure',
            Language.AR: r'ملف|تقرير|وثيقة',
            Language.RU: r'файл|отчет|документ'
        },
        "property_details": {
            Language.FA: r'جزئیات|مشخصات|اطلاعات|توضیحات|ویژگی',
            Language.EN: r'detail|spec|info|feature|describe',
            Language.AR: r'تفاصيل|معلومات|مواصفات',
            Language.RU: r'детали|характеристики|информация'
        },
        "schedule_viewing": {
            Language.FA: r'بازدید|ویزیت|دیدن|ملاقات|قرار',
            Language.EN: r'view|visit|see|tour|appointment|schedule',
            Language.AR: r'زيارة|موعد|جولة',
            Language.RU: r'просмотр|визит|встреча'
        }
    }
    
    for intent, patterns in intents.items():
        pattern = patterns.get(lang, patterns[Language.EN])
        if re.search(pattern, message, re.IGNORECASE):
            return intent
    
    return None
```

---

## دستورات دیپلوی

```bash
# نویگیت به پروژه
cd I:\ArtinRealtySmartPro\ArtinSmartRealty

# ری‌استارت سرویس backend (اگر Docker Desktop روشن است)
docker-compose restart backend

# مشاهده لاگ‌ها
docker-compose logs -f backend

# اگر Docker Desktop خاموش است:
# 1. Docker Desktop را روشن کنید
# 2. دستورات بالا را اجرا کنید
```

---

## تست‌های مورد نیاز

### تست 1: عدم تکرار پیام "ملک نداری"
1. `/start` را بزنید
2. اطلاعات را وارد کنید
3. **انتظار:** اگر ملک دارد، بدون پیام منفی مستقیماً املاک را نشان دهد

### تست 2: ارسال PDF
1. به مرحله نمایش املاک برسید
2. تایپ کنید: "roi بده" یا "pdf میخوام"
3. **انتظار:** یک فایل PDF با جزئیات ROI ارسال شود

### تست 3: عدم تکرار املاک
1. املاک نمایش داده شوند
2. یک سوال بپرسید: "قیمت چنده؟"
3. **انتظار:** فقط پاسخ سوال، بدون تکرار لیست املاک

### تست 4: پاسخ به درخواست‌های خاص
1. بگویید: "جزئیات ملک اول رو بگو"
2. **انتظار:** جزئیات دقیق ملک، نه یک پیام عمومی

---

## اولویت‌بندی Fix‌ها

1. **🔴 اولویت بالا:** Fix #3 (تکرار املاک) - خیلی آزاردهنده
2. **🟡 اولویت متوسط:** Fix #2 (ارسال PDF) - ویژگی اصلی
3. **🟢 اولویت پایین:** Fix #1 (پیام ملک نداری) - گمراه‌کننده اما غیرضروری
4. **🟢 اولویت پایین:** Fix #4 (Intent Detection) - بهبود کیفیت

---

**Developer:** Arezoo Mohammadzadegan  
**Date:** 14 دسامبر 2025  
**Status:** ⏳ منتظر اعمال تغییرات و دیپلوی
