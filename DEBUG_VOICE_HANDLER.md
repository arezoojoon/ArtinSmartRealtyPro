# 🚨 CRITICAL DEBUG: Voice Handler Not Running

## واقعیت
```
✅ Audio conversion کار میکنه
✅ Transcript ذخیره میشه  
❌ handle_voice به خط 519 نمیرسه
❌ هیچ "Voice response ready" لاگ نیست
```

## این یعنی چی؟

Voice handler زودتر return میشه یا exception می‌خوره **بدون log**.

---

## دستورات Debug روی VPS

### 1️⃣ ببین voice handler اصلاً صدا زده میشه یا نه
```bash
docker-compose logs backend | grep "handle_voice\|Refreshed lead"
```

**اگه میبینی:** `🔄 Refreshed lead 1, state=...`  
یعنی handler اجرا شده ولی جایی return کرده.

---

### 2️⃣ ببین کجا return میشه
```bash
docker-compose logs backend | grep -A 5 "voice redirect\|Voice message too long\|No voice message"
```

شاید توی یکی از این condition‌ها گیر کرده:
- Line 475: SLOT_FILLING protection
- Line 483: No voice check
- Line 488: Duration check

---

### 3️⃣ چک کن state چیه
```bash
docker-compose exec backend python -c "
import asyncio
from database import async_session, Lead
from sqlalchemy import select

async def check():
    async with async_session() as session:
        result = await session.execute(select(Lead).where(Lead.id == 1))
        lead = result.scalars().first()
        print(f'Lead 1: state={lead.conversation_state}, pending_slot={lead.pending_slot}')

asyncio.run(check())
"
```

---

### 4️⃣ لاگ کامل voice message آخری
```bash
docker-compose logs backend | tail -300 | grep -B 10 -A 20 "voice.*file_"
```

---

## احتمالات

### احتمال #1: SLOT_FILLING State
اگه lead در state `SLOT_FILLING` با `pending_slot` باشه، خط 475 message میده و return میکنه.

**Fix موقت:**
```bash
# Reset state
docker-compose exec backend python -c "
import asyncio
from database import async_session, Lead, ConversationState, update_lead
from sqlalchemy import select

async def fix():
    await update_lead(1, conversation_state=ConversationState.LANGUAGE_SELECT, pending_slot=None)
    print('✅ State reset')

asyncio.run(fix())
"
```

بعد دوباره voice بفرست.

---

### احتمال #2: Exception بدون Log
شاید `process_voice_message` exception می‌خوره ولی catch میشه.

**چک:**
```bash
docker-compose logs backend | grep -i "process_voice_message\|ERROR\|Exception" | tail -50
```

---

### احتمال #3: Response خالیه
شاید `response.message` خالیه و Telegram API error میده.

**چک:**
```bash
docker-compose logs backend | grep "telegram.*error\|Bad Request" | tail -20
```

---

## لاگ رو بفرست

این دستور رو بزن و کل خروجی رو بفرست:

```bash
docker-compose logs backend | tail -400 | grep -v "sqlalchemy.engine.Engine - INFO - SELECT" | grep -E "voice|Voice|VOICE|state=|Exception|ERROR"
```

یا ساده‌تر، **فقط آخرین voice message:**

```bash
# یه voice جدید بفرست، بعد بلافاصله این رو بزن:
docker-compose logs backend --tail 100 | grep -v "SELECT leads"
```
