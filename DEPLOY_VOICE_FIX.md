# 🚀 Deploy Voice Fix to VPS

## Issue Fixed
- ❌ **BEFORE**: `ValueError: Unknown mime type: Could not determine the mimetype for your file`
- ✅ **AFTER**: Telegram voice messages (OGA format) converted to MP3 before Gemini upload

## Changes Deployed
1. **Async Compatibility** (Commit 4e3a60c) - Fixed event loop blocking
2. **Audio Format Conversion** (Commit 52f99fc) - OGA → MP3 conversion using pydub

---

## 📋 Deployment Steps

### 1️⃣ SSH into VPS
```bash
ssh root@srv1151343.main-hosting.eu
```

### 2️⃣ Navigate to Project Directory
```bash
cd /opt/ArtinSmartRealty
```

### 3️⃣ Pull Latest Code
```bash
git pull origin main
```

**Expected Output:**
```
remote: Counting objects: X, done.
Updating 4e3a60c..52f99fc
Fast-forward
 backend/brain.py | 32 +++++++++++++++++++++++++++-----
 1 file changed, 32 insertions(+), 2 deletions(-)
```

### 4️⃣ Install FFmpeg in Backend Container
FFmpeg is **REQUIRED** for pydub to work:

```bash
docker-compose exec backend apt-get update
docker-compose exec backend apt-get install -y ffmpeg
```

**Verify Installation:**
```bash
docker-compose exec backend ffmpeg -version
```

**Expected Output:**
```
ffmpeg version 4.x.x-X
built with gcc X.X.X
```

### 5️⃣ Restart Backend Service
```bash
docker-compose restart backend
```

**Wait 10-15 seconds for restart:**
```bash
docker-compose ps backend
```

**Expected Output:**
```
NAME                    STATUS
artinrealty-backend     Up X seconds
```

---

## 🧪 Testing Voice Messages

### Test 1: Send Persian Voice Message
Send a voice message in Telegram:
> "سلام، دنبال یه آپارتمان ۲ خوابه تو دبی هستم با بودجه ۵۰۰ هزار درهم"

**Expected Logs:**
```bash
docker-compose logs -f backend | grep -E "🔄|✅|🎤|Transcript"
```

**Look for:**
```
🔄 Converting audio from ogg to mp3 for Gemini compatibility
✅ Audio converted successfully to MP3
✅ Transcript: سلام، دنبال یه آپارتمان ۲ خوابه تو دبی هستم با بودجه ۵۰۰ هزار درهم
🎤 Entities extracted: {'bedrooms': 2, 'location': 'Dubai', 'budget_max': 500000}
```

### Test 2: Send English Voice Message
Send:
> "Hi, I'm looking for a 3-bedroom villa in Palm Jumeirah"

**Expected Logs:**
```
✅ Transcript: Hi, I'm looking for a 3-bedroom villa in Palm Jumeirah
🎤 Entities extracted: {'bedrooms': 3, 'property_type': 'villa', 'location': 'Palm Jumeirah'}
```

### Test 3: Check Telegram Response
Bot should respond with:
> "🎤 I heard: [transcript]
> 
> Great! I found you're interested in..."

---

## ❌ Troubleshooting

### Problem: Still Getting MIME Type Error

**Check if FFmpeg is installed:**
```bash
docker-compose exec backend which ffmpeg
```

**If empty**, FFmpeg is not installed. Re-run:
```bash
docker-compose exec backend apt-get update
docker-compose exec backend apt-get install -y ffmpeg
docker-compose restart backend
```

---

### Problem: "⚠️ pydub not available"

**Check if pydub is installed:**
```bash
docker-compose exec backend pip list | grep pydub
```

**Expected:**
```
pydub    0.25.1
```

**If missing:**
```bash
docker-compose exec backend pip install pydub==0.25.1
docker-compose restart backend
```

---

### Problem: "Audio conversion failed"

**Check FFmpeg version inside container:**
```bash
docker-compose exec backend ffmpeg -version
```

**Check pydub can import:**
```bash
docker-compose exec backend python -c "from pydub import AudioSegment; print('✅ pydub working')"
```

**If fails**, reinstall both:
```bash
docker-compose exec backend apt-get install -y ffmpeg
docker-compose exec backend pip install --upgrade pydub
docker-compose restart backend
```

---

## 🔍 Monitoring Voice Processing

### Watch Voice Processing Logs
```bash
docker-compose logs -f backend | grep -E "voice|Voice|VOICE|🎤|🔄|✅|❌"
```

### Check for Errors
```bash
docker-compose logs backend | grep "VOICE PROCESSING ERROR"
```

**Should be EMPTY** after fix.

### Verify No MIME Type Errors
```bash
docker-compose logs backend | grep "Unknown mime type"
```

**Should be EMPTY** after fix.

---

## 📊 Success Criteria

✅ **FFmpeg installed** in backend container  
✅ **pydub working** (no import errors)  
✅ **Audio conversion logs** appear: `🔄 Converting audio...`  
✅ **Successful conversion**: `✅ Audio converted successfully`  
✅ **Transcripts appearing**: `✅ Transcript: ...`  
✅ **Entity extraction**: `🎤 Entities extracted: {...}`  
✅ **No MIME type errors** in logs  
✅ **Bot responds** with transcript to user  

---

## 📝 Post-Deployment Verification

After deployment, verify:

```bash
# 1. Check backend is running
docker-compose ps backend

# 2. Send test voice message in Telegram

# 3. Check logs for conversion
docker-compose logs backend --tail 50 | grep -E "Converting|converted|Transcript"

# 4. Verify no errors
docker-compose logs backend --tail 100 | grep ERROR
```

---

## 🎯 Next Steps After Voice Fix

Once voice is working:

1. ✅ **Voice messages working** (this deployment)
2. ⏳ **WhatsApp webhook** - Configure in Meta Business Manager
3. ⏳ **WhatsApp message testing** - Send "سلام" to WhatsApp number
4. ⏳ **End-to-end lead flow** - Verify full conversation works

---

## 🆘 Emergency Rollback

If deployment breaks something:

```bash
cd /opt/ArtinSmartRealty
git log --oneline -5
git reset --hard 4e3a60c  # Previous working commit
docker-compose restart backend
```

Then report the issue with logs:
```bash
docker-compose logs backend --tail 200 > /tmp/error_logs.txt
```
