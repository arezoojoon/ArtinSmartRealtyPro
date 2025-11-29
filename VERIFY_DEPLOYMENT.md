# ✅ VPS Verification Commands

Run these commands to verify the deployment:

## 1. Check All Services Status
```bash
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

## 2. Verify Environment Variable
```bash
docker-compose exec backend python -c "import os; print(f\"VERIFY_TOKEN: '{os.getenv('WHATSAPP_VERIFY_TOKEN')}'\")"
```

**Expected:**
```
VERIFY_TOKEN: 'ArtinSmartRealty2024SecureWebhookToken9876543210'
```

**If you see:**
```
VERIFY_TOKEN: 'EAAT58VLIlCc...'
```

**Then fix .env:**
```bash
nano .env
# Change WHATSAPP_VERIFY_TOKEN to: ArtinSmartRealty2024SecureWebhookToken9876543210
docker-compose restart backend
sleep 30
```

---

## 3. Test Webhook Verification
```bash
curl "https://realty.artinsmartagent.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=ArtinSmartRealty2024SecureWebhookToken9876543210&hub.challenge=SUCCESS123"
```

**Expected:**
```
SUCCESS123
```

---

## 4. Check Backend Logs
```bash
docker-compose logs backend | tail -30
```

**Look for:**
- ✅ `Application startup complete`
- ✅ `Bot started for tenant:`
- ✅ `✅ Background scheduler started`
- ❌ No `ERROR` or `CRITICAL` messages

---

## 5. Test Telegram Bot

### Send /start to your bot

**Expected behavior:**
1. ✅ Bot responds with welcome message
2. ✅ Shows 4 language buttons:
   - 🇬🇧 English
   - 🇮🇷 فارسی
   - 🇸🇦 العربية
   - 🇷🇺 Русский

### Click a language button (e.g., فارسی)

**Expected behavior:**
1. ✅ Bot greets in selected language
2. ✅ Asks questions about property search
3. ✅ Shows inline buttons for budget/location

### When bot asks for phone number

**Expected behavior:**
1. ✅ Bot sends: "📱 عالی! برای ارتباط با مشاور..."
2. ✅ Shows button: **"📱 اشتراک‌گذاری شماره تلفن"**
3. ✅ Clicking button automatically shares contact
4. ✅ Bot confirms: "عالی! مشاور ما با شما تماس خواهد گرفت"

---

## 6. Meta Webhook Configuration

### In Meta Business Manager:

1. Go to: https://developers.facebook.com/apps
2. Select your app → WhatsApp → Configuration
3. Under "Webhook", click "Edit"

**Callback URL:**
```
https://realty.artinsmartagent.com/webhook/whatsapp
```

**Verify Token:**
```
ArtinSmartRealty2024SecureWebhookToken9876543210
```

4. Click "Verify and Save"

**Expected:** ✅ "Success" or "Webhook verified"

---

## 7. Test Live WhatsApp Message

### Send a message to your WhatsApp number:

```
Hi
```

**Expected:**
1. ✅ Bot responds within 2-3 seconds
2. ✅ Shows main menu or welcomes you
3. ✅ Conversation flows smoothly

---

## 🚨 If Something Fails

### Backend not healthy after 60 seconds:
```bash
docker-compose logs backend | grep -i error
docker-compose restart backend
sleep 30
```

### Webhook returns 403 Forbidden:
```bash
# Check token
docker-compose exec backend python -c "import os; print(os.getenv('WHATSAPP_VERIFY_TOKEN'))"
# If wrong, fix .env and restart
```

### Telegram buttons not showing:
```bash
# Check if code is up to date
git log --oneline -5
# Should show: a5b5adb, 5a3dde1, 8b4205c

# If not, pull again:
git pull origin main
docker-compose restart backend
```

### WhatsApp not responding:
```bash
# Check webhook is registered in Meta
# Check backend logs for incoming messages
docker-compose logs -f backend | grep -i whatsapp
```

---

## ✅ All Good Checklist

- [ ] All 5 containers running
- [ ] Backend shows "Up (healthy)"
- [ ] Verify token is correct (not EAAT...)
- [ ] Webhook test returns SUCCESS123
- [ ] Telegram /start shows language buttons
- [ ] Telegram shows contact request button
- [ ] No errors in backend logs
- [ ] Meta webhook verified successfully
- [ ] WhatsApp messages get responses

---

**Run all checks:**
```bash
echo "=== Services Status ==="
docker-compose ps

echo -e "\n=== Verify Token ==="
docker-compose exec backend python -c "import os; print(os.getenv('WHATSAPP_VERIFY_TOKEN'))"

echo -e "\n=== Webhook Test ==="
curl "https://realty.artinsmartagent.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=ArtinSmartRealty2024SecureWebhookToken9876543210&hub.challenge=SUCCESS123"

echo -e "\n=== Backend Health ==="
docker-compose logs backend | tail -5 | grep -E "startup|healthy|Bot started"

echo -e "\n=== Latest Commit ==="
git log --oneline -1
```

---

**Status:** Ready for final verification  
**Date:** November 29, 2025
