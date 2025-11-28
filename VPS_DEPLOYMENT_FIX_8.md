# 🚀 VPS Deployment Instructions - FIX #8

**Date:** November 28, 2025  
**Commits to Deploy:** `4d4a1ee` (FIX #8 - Redis method fix)  
**Previous Commits:** `aeb18fa`, `b424791` (FIX #7, FIX #1-6)  
**VPS:** srv1151343

---

## 📋 Overview

**Critical Issue Fixed:** RedisManager doesn't have `.set()` method - bot was crashing on every user interaction.

**Changes Made:**
- `telegram_bot.py`: Fixed handle_text() and handle_callback() to use `redis_manager.redis_client.set()` instead of `redis_manager.set()`
- `timeout_scheduler.py`: Needs same fix (line ~117) - MANUAL FIX REQUIRED ON VPS

---

## 🔧 Complete Deployment Steps

### Step 1: SSH to VPS
```bash
ssh root@srv1151343
cd /opt/ArtinSmartRealty
```

### Step 2: Pull Latest Code (Commit 4d4a1ee)
```bash
git pull origin main
git log --oneline -1  # Should show: 4d4a1ee FIX #8: Critical - RedisManager.set()
```

### Step 3: Fix timeout_scheduler.py (MANUAL FIX)
```bash
nano backend/timeout_scheduler.py
```

**Navigate to line 117 using CTRL+G (go to line)**

**Find this line:**
```python
await redis_manager.set(f"user:{lead.id}:last_interaction", now.isoformat())
```

**Replace with:**
```python
if redis_manager.redis_client:
    await redis_manager.redis_client.set(f"user:{lead.id}:last_interaction", now.isoformat())
```

**Save file:**
- Press: `CTRL+X`
- Confirm: `Y`
- Press: `ENTER`

### Step 4: Stop Old Containers
```bash
docker-compose down
sleep 2
```

### Step 5: Rebuild & Start
```bash
docker-compose up -d --build
sleep 10
```

### Step 6: Check Logs for Errors
```bash
docker-compose logs backend | tail -100
```

**Look for:**
- ✅ `✅ Database initialized`
- ✅ `✅ Redis connected`
- ✅ `✅ Bot started for tenant`
- ✅ `✅ Background scheduler started`
- ❌ **NO** `AttributeError: 'RedisManager' object has no attribute 'set'`

### Step 7: Test the Bot
Send a message or click a button on Telegram bot @TaranteenBot

**Should see in logs:**
- ✅ `🔄 Refreshed lead {id}`
- ✅ `⏰ Updated last_interaction for user {id}`
- ✅ `🔒 Lock acquired for user`
- ✅ Response sent without errors

---

## ❌ If Errors Still Occur

**Error 1: Still seeing `AttributeError: 'RedisManager' object has no attribute 'set'`**
- Make sure you edited timeout_scheduler.py correctly
- Rebuild: `docker-compose down && docker-compose up -d --build`

**Error 2: Container won't start**
```bash
docker-compose logs backend | grep ERROR
```

**Error 3: Redis connection failed**
```bash
docker-compose ps  # Should show redis container running
docker exec artinrealty-redis redis-cli ping  # Should return PONG
```

---

## ✅ Verification Checklist

After deployment, verify all 8 fixes are working:

- [ ] **FIX #1**: Send text mid-conversation → Bot doesn't reset to language select
- [ ] **FIX #2**: Ask for photos → Bot shows properties BEFORE asking for phone
- [ ] **FIX #3**: Voice/image processing works (no API errors)
- [ ] **FIX #4**: Ask "How much is 2-year visa?" → Bot responds "750,000 AED"
- [ ] **FIX #5**: See "📅 Book Consultation" button in property flow
- [ ] **FIX #6**: Stay silent for 15 min → Bot sends follow-up "Are you still there?"
- [ ] **FIX #7**: Send Persian text in LANGUAGE_SELECT → Bot detects language, moves to WARMUP
- [ ] **FIX #8**: Click buttons/send messages → NO errors in logs about RedisManager.set()

---

## 📊 Summary

| Component | Status | Notes |
|-----------|--------|-------|
| GitHub Code | ✅ Pushed | Commits aeb18fa, 4d4a1ee ready |
| telegram_bot.py | ✅ Fixed | Contains redis_client.set() calls |
| timeout_scheduler.py | ⏳ PENDING | Needs manual fix on VPS line 117 |
| VPS Deployment | ⏳ READY | Follow steps above |

---

## 🎯 Next Steps After Deployment

1. **Test bot functionality** with all 8 fixes
2. **Monitor logs** for 30 minutes: `docker-compose logs -f backend`
3. **Check Ghost Protocol** - send message, wait 15min, verify follow-up sent
4. **Report any issues** with specific error messages

---

**Questions?** Check commit `4d4a1ee` on GitHub for exact changes made.
