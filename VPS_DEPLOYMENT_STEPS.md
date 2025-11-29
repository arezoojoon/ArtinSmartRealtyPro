# 🚀 VPS Deployment Steps - Complete Guide

## Current Issue: Nginx Not Running

You only started the backend, but **nginx is needed** to handle HTTPS and proxy requests.

---

## ✅ Complete Deployment Process

### Step 1: Fix .env File (CRITICAL!)
```bash
cd /opt/ArtinSmartRealty
nano .env
```

**Find this line:**
```bash
WHATSAPP_VERIFY_TOKEN=EAAT58VLIlCcBQOcTWGz...  # WRONG!
```

**Change to:**
```bash
WHATSAPP_VERIFY_TOKEN=ArtinSmartRealty2024SecureWebhookToken9876543210
```

**Save:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

### Step 2: Pull Latest Code
```bash
cd /opt/ArtinSmartRealty
git pull origin main
```

**Expected output:**
```
From https://github.com/arezoojoon/ArtinSmartRealty
 * branch            main       -> FETCH_HEAD
Updating 8b4205c..5a3dde1
Fast-forward
 backend/brain.py          | 12 ++++--
 backend/telegram_bot.py   | 56 +++++++++++++++++++++---
 ...
```

---

### Step 3: Start ALL Services
```bash
docker-compose down
docker-compose up -d
```

**This will start:**
- ✅ artinrealty-db (PostgreSQL)
- ✅ artinrealty-redis (Redis)
- ✅ artinrealty-backend (FastAPI)
- ✅ artinrealty-frontend (Next.js)
- ✅ artinrealty-nginx (HTTPS proxy) ← **THIS WAS MISSING!**

---

### Step 4: Wait for Services to Be Healthy
```bash
sleep 45  # Backend needs time to initialize

# Check all services
docker-compose ps
```

**Expected output:**
```
NAME                   STATUS
artinrealty-backend    Up (healthy)
artinrealty-db         Up
artinrealty-frontend   Up
artinrealty-nginx      Up
artinrealty-redis      Up
```

---

### Step 5: Verify Environment Variable
```bash
docker-compose exec backend python -c "import os; print(f\"VERIFY_TOKEN: '{os.getenv('WHATSAPP_VERIFY_TOKEN')}'\")"
```

**Expected:**
```
VERIFY_TOKEN: 'ArtinSmartRealty2024SecureWebhookToken9876543210'
```

**NOT:**
```
VERIFY_TOKEN: 'EAAT58VLIlCc...'  # ❌ WRONG!
```

---

### Step 6: Test Webhook (HTTPS via Nginx)
```bash
curl "https://realty.artinsmartagent.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=ArtinSmartRealty2024SecureWebhookToken9876543210&hub.challenge=SUCCESS123"
```

**Expected:**
```
SUCCESS123
```

**If you get:**
- `Connection refused` → Nginx not running (go back to Step 3)
- `502 Bad Gateway` → Backend not ready (wait more, check logs)
- `403 Forbidden` → Wrong token in .env (go back to Step 1)

---

### Step 7: Check Backend Logs
```bash
docker-compose logs backend | tail -50
```

**Look for:**
- ✅ `✅ Background scheduler started`
- ✅ `Application startup complete`
- ❌ Any `ERROR` or `CRITICAL` messages

---

### Step 8: Test Telegram Bot
```bash
# Send /start to your Telegram bot
# You should see the welcome message

# Then request properties
# Bot should show: "📱 Share Phone Number" button ← NEW FEATURE!
```

---

## 🔍 Troubleshooting

### Issue 1: "Connection refused" on port 443
**Cause:** Nginx container not running

**Fix:**
```bash
docker-compose ps | grep nginx
# If not running:
docker-compose up -d nginx
```

---

### Issue 2: "502 Bad Gateway"
**Cause:** Backend not healthy yet

**Check:**
```bash
docker-compose ps | grep backend
# Should show: Up (healthy)

# If shows "Up (health: starting)", wait 30 more seconds
sleep 30
```

**View logs:**
```bash
docker-compose logs backend | grep -i error
```

---

### Issue 3: Webhook returns 403 Forbidden
**Cause:** Wrong verify token in `.env`

**Verify:**
```bash
docker-compose exec backend python -c "import os; print(os.getenv('WHATSAPP_VERIFY_TOKEN'))"
```

**Should be:** `ArtinSmartRealty2024SecureWebhookToken9876543210`

**If wrong, fix `.env` and restart:**
```bash
nano .env  # Fix the token
docker-compose restart backend
sleep 30
```

---

### Issue 4: Backend crashes on startup
**Check logs:**
```bash
docker-compose logs backend | tail -100
```

**Common causes:**
- Database connection failed (check DB password)
- Redis connection failed (check redis container)
- Missing environment variables
- Python syntax errors (check recent commits)

**Force rebuild:**
```bash
docker-compose down
docker-compose up -d --build backend
```

---

## 📊 Health Check Commands

### Quick Status Check
```bash
# All services running?
docker-compose ps

# Backend healthy?
docker-compose ps | grep backend | grep healthy

# Nginx responding?
curl -I https://realty.artinsmartagent.com/health

# Webhook working?
curl "https://realty.artinsmartagent.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=ArtinSmartRealty2024SecureWebhookToken9876543210&hub.challenge=TEST"
```

### Backend Logs (Live Tail)
```bash
docker-compose logs -f backend
```

### Nginx Logs
```bash
docker-compose logs nginx | tail -50
```

### Database Connection
```bash
docker-compose exec backend python -c "from database import engine; print('DB OK')"
```

### Redis Connection
```bash
docker-compose exec backend python -c "from redis_manager import redis_manager; print('Redis OK')"
```

---

## ✅ Success Checklist

- [ ] `.env` file has correct `WHATSAPP_VERIFY_TOKEN`
- [ ] All 5 containers running (`docker-compose ps`)
- [ ] Backend shows "Up (healthy)"
- [ ] Webhook returns `SUCCESS123`
- [ ] Telegram bot responds to `/start`
- [ ] Contact button appears when requesting phone
- [ ] No errors in backend logs

---

## 🎯 Final Verification

```bash
# Run all checks
echo "1. Services Status:"
docker-compose ps

echo -e "\n2. Verify Token:"
docker-compose exec backend python -c "import os; print(os.getenv('WHATSAPP_VERIFY_TOKEN'))"

echo -e "\n3. Webhook Test:"
curl "https://realty.artinsmartagent.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=ArtinSmartRealty2024SecureWebhookToken9876543210&hub.challenge=SUCCESS123"

echo -e "\n4. Health Check:"
curl https://realty.artinsmartagent.com/health
```

**All should return success!** ✅

---

**Last Updated:** November 29, 2025  
**Commit:** 5a3dde1  
**Status:** Ready for deployment
