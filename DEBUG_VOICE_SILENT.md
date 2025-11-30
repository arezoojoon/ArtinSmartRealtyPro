# 🔍 Debug: Voice Processing Silent (No Response)

## مشکل
- ✅ Audio conversion موفق: `✅ Audio converted successfully to MP3`
- ✅ Transcript ذخیره شد: `UPDATE leads SET voice_transcript=...`
- ✅ Entities استخراج شد: `voice_entities=...`
- ❌ **ولی بات هیچ جوابی نداد**

---

## چک کردن لاگ‌ها روی VPS

### 1. لاگ کامل Voice Processing
```bash
docker-compose logs backend --tail 200 | grep -A 20 -B 5 "Converting audio"
```

این نشون میده:
- آیا Gemini جواب داد؟
- آیا `process_message` اجرا شد؟
- آیا پیام به Telegram فرستاده شد؟

---

### 2. چک کردن Exception‌ها
```bash
docker-compose logs backend --tail 100 | grep -i -E "error|exception|traceback"
```

ببین آیا exception خورده که جلوی ارسال پیام رو گرفته.

---

### 3. چک کردن Telegram Send
```bash
docker-compose logs backend --tail 150 | grep -E "Sending message|reply_text|send_message"
```

ببین آیا `reply_text` یا `send_message` صدا زده شده یا نه.

---

### 4. لاگ کامل از اولین Voice Message
```bash
docker-compose logs backend --since 5m > /tmp/voice_debug.log
cat /tmp/voice_debug.log | grep -A 50 "21:28:47"
```

(21:28:47 زمان اولین voice موفق بود)

---

## احتمالات

### احتمال 1: `process_message` Exception خورد
اگه `process_message` error داد، response ساخته نشد.

**چک:**
```bash
docker-compose logs backend | grep "process_message"
```

---

### احتمال 2: Template Formatting Issue
شاید `ack_msg` ساخته نشد و exception رو catch کردیم ولی `response.message` خالی شد.

**چک کن آیا این warning هست:**
```bash
docker-compose logs backend | grep "Voice acknowledgment formatting failed"
```

---

### احتمال 3: Telegram API Timeout
شاید پیام ساخته شد ولی فرستادن timeout خورد.

**چک:**
```bash
docker-compose logs backend | grep -i "timeout"
```

---

## Fix موقت: افزودن Logging

بیا logging بیشتر اضافه کنیم تا ببینیم دقیقاً کجا میمونه.

این رو به VPS بفرست:

```bash
# Pull آخرین کد
cd /opt/ArtinSmartRealty
git pull origin main

# Restart
docker-compose restart backend

# لاگ با جزئیات بیشتر
docker-compose logs -f backend 2>&1 | grep -v "SELECT leads" | grep -E "voice|Voice|process_message|Sending|reply"
```

---

## Debug Commands

### کامل‌ترین لاگ (بدون SQL noise):
```bash
docker-compose logs backend --tail 300 | grep -v "SELECT leads" | grep -v "sqlalchemy.engine.Engine" | tail -100
```

### فقط voice processing flow:
```bash
docker-compose logs backend | grep -E "🔄 Converting|✅ Audio converted|process_voice|process_message|voice_acknowledged|reply_text" | tail -50
```

### چک database update موفق:
```bash
docker-compose logs backend | grep "UPDATE leads SET voice_transcript"
```

---

## اگه لاگ خاصی پیدا نشد

یعنی احتمالاً `process_message` یا `reply_text` بدون error سکوت کرده.

**راه حل:** باید کد `telegram_bot.py` رو چک کنیم که چطور voice message handle میشه.

این دستور رو بزن:
```bash
docker-compose exec backend grep -A 30 "async def handle_voice" /app/telegram_bot.py
```

یا اگه نیست:
```bash
docker-compose exec backend grep -n "process_voice_message" /app/telegram_bot.py
```

---

## نتیجه لاگ‌ها رو بفرست

لطفاً خروجی این دستور رو بفرست:

```bash
docker-compose logs backend --tail 200 | grep -v "SELECT leads" | grep -E "21:28:|21:29:|Converting|process|voice|reply|Sending"
```

تا ببینیم دقیقاً flow کجا قطع شده.
