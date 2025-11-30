# 🚨 URGENT: VPS Deployment Commands

## ❌ Problem
Voice messages still failing - **new code not deployed to VPS yet**

Logs show NO `🔄 Converting audio` which means commit `52f99fc` wasn't pulled.

---

## ✅ Solution: Deploy Now

### Copy-paste these commands on VPS:

```bash
ssh root@srv1151343.main-hosting.eu

cd /opt/ArtinSmartRealty

# Pull latest code (commits 4e3a60c, 52f99fc, 71cc906)
git pull origin main

# Restart backend
docker-compose restart backend

# Wait 15 seconds
sleep 15

# Monitor logs
docker-compose logs -f backend | grep -E "🔄|✅|❌|Converting|Transcript|VOICE"
```

---

## 🧪 Test After Deployment

1. **Send voice message in Telegram** (any language)

2. **Look for these logs:**
```
🔄 Converting audio from ogg to mp3 for Gemini compatibility
✅ Audio converted successfully to MP3
✅ Transcript: [your voice content]
🎤 Entities extracted: {...}
```

3. **Bot should respond with transcript**

---

## ❌ If Still Failing

Check if pull worked:
```bash
cd /opt/ArtinSmartRealty
git log --oneline -3
```

**Should show:**
```
71cc906 docs: Add deployment guide for voice processing fix
52f99fc fix: Convert Telegram audio (OGA) to MP3 for Gemini compatibility
4e3a60c fix: Make Gemini File API calls async-compatible for voice processing
```

If these commits are missing, run:
```bash
git fetch origin
git reset --hard origin/main
docker-compose restart backend
```

---

## 🔍 Debug Commands

**Check current code version on VPS:**
```bash
docker-compose exec backend grep -A 5 "Converting audio" /app/brain.py
```

**Should output:**
```python
logger.info(f"🔄 Converting audio from {file_extension} to mp3 for Gemini compatibility")
```

**If empty**, code wasn't deployed. Force update:
```bash
git pull --rebase origin main
docker-compose down
docker-compose up -d
```
