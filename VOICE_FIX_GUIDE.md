# Telegram Voice Message Fix Guide

## مشکل: تلگرام ویس پلیر نمیده

### ❌ علت اصلی
**پکیج `pydub` نصب نیست!**

Gemini API مستقیماً فایل صوتی رو process میکنه، اما برای کانورت کردن فرمت‌های مختلف نیاز به `pydub` داریم.

---

## ✅ راه‌حل

### 1. اضافه کردن pydub به requirements.txt

**✅ DONE** - اضافه شد:
```
# Audio Processing (Voice Messages)
pydub==0.25.1
```

---

### 2. نصب در Local Environment

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install pydub
pip install pydub==0.25.1

# Verify installation
pip show pydub
```

---

### 3. نصب FFmpeg (ضروری برای pydub)

**Windows:**
```powershell
# با Chocolatey
choco install ffmpeg

# یا دانلود مستقیم از:
# https://www.gyan.dev/ffmpeg/builds/
```

**Linux (VPS):**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y ffmpeg

# Verify
ffmpeg -version
```

---

### 4. Deploy در VPS

```bash
# SSH to VPS
ssh root@srv1151343.main-hosting.eu

# Navigate to project
cd /home/artin/ArtinSmartRealty

# Pull latest changes
git pull origin main

# Rebuild backend with new dependencies
docker-compose down
docker-compose build backend
docker-compose up -d

# Check logs
docker-compose logs -f backend | grep -i voice
```

---

## 🎤 How Voice Processing Works

### Flow:
1. **User sends voice** → Telegram
2. **Bot downloads** `.ogg` file
3. **Gemini File API** uploads audio
4. **Gemini processes** → Transcript + Entities
5. **Bot responds** with extracted info

### Code Path:
```python
telegram_bot.handle_voice()
  ↓
brain.process_voice_message()
  ↓
brain.process_voice(audio_data, "ogg")
  ↓
genai.upload_file(temp_audio_path)
  ↓
model.generate_content([audio_file, prompt])
  ↓
Extract transcript + entities (budget, property_type, etc.)
  ↓
Update lead.voice_entities
  ↓
brain.process_message(transcript)
```

---

## 🧪 Testing Voice Messages

### 1. Local Test

```python
# test_voice.py
import asyncio
from brain import Brain
from database import get_tenant_by_id, get_lead_by_id

async def test_voice():
    tenant = await get_tenant_by_id(1)
    lead = await get_lead_by_id(1)
    
    # Read test audio file
    with open("test_voice.ogg", "rb") as f:
        audio_data = f.read()
    
    brain = Brain(tenant)
    transcript, entities = await brain.process_voice(audio_data, "ogg")
    
    print(f"Transcript: {transcript}")
    print(f"Entities: {entities}")

asyncio.run(test_voice())
```

### 2. Telegram Test

1. **ارسال پیام صوتی:**
   - فارسی: "سلام، دنبال یه آپارتمان ۲ خوابه تو دبی هستم، بودجه ۵۰۰ تا ۷۰۰ هزار دلار"
   - English: "Hi, I'm looking for a 2-bedroom apartment in Dubai, budget $500k to $700k"

2. **انتظار:**
   ```
   🎤 I heard: "سلام، دنبال یه آپارتمان ۲ خوابه تو دبی..."
   
   Great! I understood:
   - Property Type: Apartment
   - Bedrooms: 2
   - Budget: $500,000 - $700,000
   - Location: Dubai
   
   Let me find perfect matches for you! 🏡
   ```

---

## 📊 Expected Logs

**Success:**
```
2025-11-30 XX:XX:XX - telegram_bot - INFO - 🎤 Voice message received
2025-11-30 XX:XX:XX - brain - INFO - Processing voice (123KB, ogg)
2025-11-30 XX:XX:XX - brain - INFO - Gemini audio uploaded: files/abc123
2025-11-30 XX:XX:XX - brain - INFO - ✅ Transcript: "سلام، دنبال..."
2025-11-30 XX:XX:XX - brain - INFO - 🎤 Extracted entities: {budget_min: 500000, ...}
2025-11-30 XX:XX:XX - telegram_bot - INFO - ✅ Voice processed and responded
```

**Failure (Before Fix):**
```
❌ VOICE PROCESSING ERROR: ModuleNotFoundError: No module named 'pydub'
```

---

## 🔧 Troubleshooting

### Problem 1: "No module named 'pydub'"
```bash
# در VPS
docker-compose exec backend pip install pydub
docker-compose restart backend
```

### Problem 2: "FFmpeg not found"
```bash
# در VPS
docker-compose exec backend apt-get update
docker-compose exec backend apt-get install -y ffmpeg
```

### Problem 3: "Audio processing timeout"
- فایل بیش از حد بزرگه (>5MB)
- اینترنت VPS کنده
- Gemini API busy

**راه‌حل:**
```python
# در brain.py افزایش timeout
max_wait = 60  # از 30 به 60 ثانیه
```

### Problem 4: "Could not parse voice"
- Gemini JSON برنگردوند
- فایل صوتی خیلی noisy

**راه‌حل:**
- Check logs برای raw response
- کیفیت audio رو بهبود بده

---

## 🎯 Supported Audio Formats

✅ **Telegram:**
- `.ogg` (Opus codec) - default
- `.mp3`
- `.m4a`

✅ **WhatsApp:**
- `.ogg` (Opus codec)
- `.mp3`
- `.aac`

✅ **Gemini API:**
- All audio formats (converts automatically)
- Max file size: 20MB
- Max duration: 5 minutes (enforced in code)

---

## 📝 Voice Entity Extraction

**Entities که از صدا استخراج میشن:**

```json
{
  "transcript": "Full text",
  "language": "fa/en/ar/ru",
  "entities": {
    "budget_min": 500000,
    "budget_max": 700000,
    "location": "Dubai Marina",
    "property_type": "apartment",
    "transaction_type": "buy",
    "purpose": "investment",
    "bedrooms": 2,
    "phone_number": "+971501234567"
  }
}
```

**Storage:**
- `lead.voice_transcript` → متن کامل
- `lead.voice_entities` → JSON entities
- `lead.budget_min/max` → از entities
- `lead.property_type` → از entities
- etc.

---

## ✅ Verification Commands

```bash
# 1. Check if pydub installed
docker-compose exec backend pip show pydub

# 2. Check FFmpeg
docker-compose exec backend ffmpeg -version

# 3. Test Gemini API
docker-compose exec backend python -c "import google.generativeai as genai; print('OK')"

# 4. Send test voice
# از تلگرام یه پیام صوتی بفرست

# 5. Monitor logs
docker-compose logs -f backend | grep -E "voice|Voice|VOICE|🎤"
```

---

## 🚀 Deployment Checklist

- [x] Add pydub to requirements.txt
- [ ] Install FFmpeg in Docker image
- [ ] Git commit and push
- [ ] Deploy to VPS
- [ ] Rebuild backend container
- [ ] Test with real voice message
- [ ] Verify entity extraction
- [ ] Check lead updates in database

---

## 🐳 Docker Image Update (Optional)

اگه میخوای FFmpeg رو مستقیماً توی Docker image داشته باشی:

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Rest of Dockerfile...
```

---

## 📞 Support

اگه بعد از این کارها باز کار نکرد:

1. لاگ‌های کامل رو بفرست
2. Check Gemini API quota
3. Test با audio کوتاه‌تر (5 ثانیه)
