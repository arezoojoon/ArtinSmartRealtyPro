# ⚠️ CRITICAL VPS FIX - Voice Handler Crash

## 🔴 PROBLEM IDENTIFIED

**Voice messages are crashing due to missing message key**

```python
KeyError: 'voice_acknowledged' at brain.py line 2524
```

**Root Cause:** VPS is running OLD code from before commit c00ec42. The Docker image wasn't rebuilt after pulling new code.

---

## ✅ SOLUTION: Rebuild Docker Image

### Step 1: Pull Latest Code (Already Done)
```bash
cd /opt/ArtinSmartRealty
git pull origin main  # ✅ You already did this - shows commit 1c70ea0
```

### Step 2: **REBUILD DOCKER IMAGE** (CRITICAL - You MUST do this)
```bash
# Stop containers
docker-compose down

# Rebuild backend image (forces Python to load new brain.py)
docker-compose build --no-cache backend

# Start containers
docker-compose up -d
```

**Why this is needed:** Docker caches the old `brain.py` inside the image. Even though you pulled new code, the container is still running the old cached version.

---

## 🧪 VERIFICATION AFTER REBUILD

### 1. Check Scheduler Jobs Are Active
```bash
# Wait 5 minutes after restart, then check:
docker-compose logs backend | grep "Ghost Protocol"
```

**Expected Output:**
```
👻 Ghost Protocol: Checking for inactive users...
👻 Scanned 5 leads, found 2 inactive users
📧 Sending follow-up to lead 1 (inactive for 16 min)
```

**If you see nothing:** Scheduler is running but jobs are empty (old code still cached).

---

### 2. Verify VALUE_PROPOSITION Fix Deployed
```bash
# Check if new routing keywords exist in running container
docker-compose exec backend grep -n "DETECT CONSULTATION REQUEST" /app/brain.py
```

**Expected Output:**
```
1724:        # 1. DETECT CONSULTATION REQUEST
```

**If "No such file":** File path is `/app/backend/brain.py` (add `/backend/`)

**If no matches:** Old code still running - rebuild Docker image.

---

### 3. Test Voice Handler Fix
Send a voice message to bot after rebuild.

**Expected:** Bot responds with transcript acknowledgment
**Broken:** Bot crashes with KeyError (old code)

---

## 🐛 ADDITIONAL ISSUES FOUND

### Issue 1: Scheduler Running But Empty
**Symptoms:**
```bash
Running job "ghost_protocol_job" ... executed successfully
# Completes in 0.05 seconds (should take ~1-2 seconds with DB queries)
```

**Diagnosis:** Old `timeout_scheduler.py` with empty job implementations

**Fix:** Rebuilding Docker image will load new scheduler code

---

### Issue 2: Docker File Path Confusion
Your verification script used `/app/backend/brain.py` but actual path might be `/app/brain.py`

**Find correct path:**
```bash
docker-compose exec backend find /app -name "brain.py" -type f
```

---

## 📋 COMPLETE FIX CHECKLIST

Run these commands **IN ORDER** on VPS:

```bash
# 1. Navigate to project
cd /opt/ArtinSmartRealty

# 2. Confirm latest code pulled (should show 1c70ea0)
git log --oneline -1

# 3. Stop containers
docker-compose down

# 4. REBUILD backend image (CRITICAL STEP)
docker-compose build --no-cache backend

# 5. Start containers
docker-compose up -d

# 6. Wait 30 seconds for startup
sleep 30

# 7. Check logs for errors
docker-compose logs --tail=50 backend

# 8. Verify voice_acknowledged key exists
docker-compose exec backend grep -n "voice_acknowledged" /app/brain.py

# 9. Wait 5 minutes, then check Ghost Protocol
sleep 300
docker-compose logs backend | grep "Ghost Protocol"

# 10. Test voice message in bot
```

---

## 🎯 EXPECTED RESULTS AFTER FIX

### ✅ Scheduler Logs (Every 5 minutes):
```
2025-11-30 12:00:00 - 👻 Ghost Protocol: Checking for inactive users...
2025-11-30 12:00:00 - 👻 Scanned 3 leads, found 1 inactive
2025-11-30 12:00:01 - 📧 Sending follow-up to lead 1 (inactive for 17 min)
```

### ✅ Voice Message Response:
```
User: [sends voice message "سلام"]
Bot: 🎤 گرفتم! شما گفتید:
     "سلام"
     
     بذارید پردازش کنم...
Bot: [follows up with AI response]
```

### ✅ VALUE_PROPOSITION Fix:
```
User: "Is the house furnished?"
Logs: ❓ Question detected from lead 1
Bot: [Answers specific question - NOT "Great! Here are properties..."]
```

---

## 🚨 IF REBUILD FAILS

### Error: "Cannot remove running container"
```bash
docker-compose down --remove-orphans
docker system prune -f
docker-compose build --no-cache backend
docker-compose up -d
```

### Error: "No space left on device"
```bash
# Clean old Docker images
docker system prune -a -f
docker-compose build --no-cache backend
docker-compose up -d
```

### Error: "Port already in use"
```bash
# Find and kill process using port
lsof -ti:8000 | xargs kill -9
docker-compose up -d
```

---

## 📊 COMMIT TIMELINE (For Reference)

```
1c70ea0 (VPS HEAD) - docs: Add VPS deployment verification guide  ← YOU ARE HERE
b42444a - docs: Add deployment guides                              ← Same code as c00ec42
c00ec42 - fix: CRITICAL - VALUE_PROPOSITION + Ghost Protocol      ← THE FIX
86e2d07 - fix: Voice response safety check                         ← OLD CODE (VPS running this)
```

**Your VPS pulled commit 1c70ea0 but Docker is running cached code from 86e2d07**

---

## 🔧 DEBUGGING COMMANDS

### Check which code version is actually running:
```bash
# Look for new VALUE_PROPOSITION routing
docker-compose exec backend grep -A5 "DETECT CONSULTATION REQUEST" /app/brain.py

# Check Ghost Protocol implementation
docker-compose exec backend grep -A10 "_check_ghost_users" /app/timeout_scheduler.py

# Check voice_acknowledged message
docker-compose exec backend grep -B2 -A4 "voice_acknowledged" /app/brain.py
```

### Monitor real-time logs:
```bash
# Watch for voice errors
docker-compose logs -f backend 2>&1 | grep -i "voice"

# Watch for Ghost Protocol activity
docker-compose logs -f backend 2>&1 | grep -i "ghost"

# Watch for VALUE_PROPOSITION routing
docker-compose logs -f backend 2>&1 | grep -E "Question detected|Consultation request|Photo request"
```

---

## 💡 KEY INSIGHT

**Git pull updates CODE on disk, but Docker runs CODE inside IMAGE.**

**You need to:**
1. ✅ Pull code (you did this)
2. ❌ **Rebuild Docker image** ← YOU MUST DO THIS
3. ❌ Restart containers with new image

**Without step 2, your containers keep running old cached code!**

---

## 📞 NEXT STEPS

1. **Run the rebuild commands above**
2. **Wait 5 minutes**
3. **Test voice message in bot**
4. **Check logs for Ghost Protocol activity**
5. **Report back with results**

If rebuilding doesn't fix it, we may need to check:
- Docker volume mounts (old code persisting)
- ENV variables pointing to wrong Python files
- Multiple Python installations in container
