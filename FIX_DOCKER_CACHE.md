# 🔍 Debug: Why Code Not Updating

## Check 1: Verify Current Commit on VPS

```bash
cd /opt/ArtinSmartRealty
git log --oneline -5
```

**Expected output (should include these 3 commits):**
```
71cc906 docs: Add deployment guide for voice processing fix
52f99fc fix: Convert Telegram audio (OGA) to MP3 for Gemini compatibility
4e3a60c fix: Make Gemini File API calls async-compatible for voice processing
```

---

## Check 2: Verify Code Inside Docker Container

```bash
docker-compose exec backend grep -B2 -A10 "Converting audio" /app/brain.py
```

**Expected output:**
```python
try:
    from pydub import AudioSegment
    logger.info(f"🔄 Converting audio from {file_extension} to mp3 for Gemini compatibility")
    
    # Load audio file
    audio = AudioSegment.from_file(temp_audio_path, format=file_extension)
```

**If empty or different**, Docker image is stale.

---

## ✅ Solution: Force Rebuild Docker Image

The issue is Docker is using **cached image** with old code.

### Step 1: Stop Everything
```bash
cd /opt/ArtinSmartRealty
docker-compose down
```

### Step 2: Remove Old Image
```bash
docker rmi artinsmartrealty-backend -f
```

### Step 3: Rebuild from Scratch
```bash
docker-compose build --no-cache backend
```

This will take 2-3 minutes. Watch for:
```
Step X/Y : COPY backend/ /app/
Step X/Y : RUN pip install -r requirements.txt
```

### Step 4: Start Fresh
```bash
docker-compose up -d
```

### Step 5: Verify Code is New
```bash
docker-compose exec backend grep "Converting audio" /app/brain.py
```

**Should output:**
```
logger.info(f"🔄 Converting audio from {file_extension} to mp3 for Gemini compatibility")
```

### Step 6: Test Voice Message
Send voice in Telegram, monitor logs:
```bash
docker-compose logs -f backend | grep -E "🔄 Converting|✅ Audio converted|Transcript"
```

---

## 🎯 Quick Fix (All-in-One Command)

Copy-paste this entire block:

```bash
cd /opt/ArtinSmartRealty && \
docker-compose down && \
docker rmi artinsmartrealty-backend -f && \
docker-compose build --no-cache backend && \
docker-compose up -d && \
sleep 10 && \
echo "✅ Checking if new code deployed..." && \
docker-compose exec backend grep "Converting audio" /app/brain.py && \
echo "✅ Rebuild complete! Now send a voice message and monitor:" && \
docker-compose logs -f backend | grep -E "Converting|Transcript|VOICE"
```

---

## 🔍 Alternative: Check Dockerfile

If rebuild fails, check your Dockerfile:

```bash
cat backend/Dockerfile
```

Make sure it has:
```dockerfile
COPY backend/ /app/
RUN pip install -r requirements.txt
```

If backend/Dockerfile doesn't exist, check docker-compose.yml for build context.
