# تست Deployment Waha + Deep Links

## قدم‌های Deployment

```bash
# SSH به سرور
ssh root@srv1151343.hstgr.io
cd /opt/ArtinSmartRealty

# Pull آخرین تغییرات
git pull origin main

# Build و Start Waha
docker-compose build --no-cache backend
docker-compose up -d waha

# چک کردن لاگ‌ها
docker-compose logs -f waha
```

## QR Code Scanning

### روش 1: Dashboard (توصیه می‌شود)

```
http://SERVER_IP:3001/api/dashboard
```

### روش 2: Terminal

```bash
docker-compose logs waha | grep -A 20 "QR"
```

## تست Deep Links

### Test 1: Deep Link Detection

```bash
# فرستادن پیام تست با curl
curl -X POST http://localhost:8000/api/webhook/waha \
  -H "Content-Type: application/json" \
  -d '{
    "event": "message",
    "session": "default",
    "payload": {
      "from": "971505037158@c.us",
      "body": "start_realty",
      "hasMedia": false,
      "_data": {
        "notifyName": "Test User"
      }
    }
  }'

# چک کردن لاگ backend
docker-compose logs backend | grep "Deep link"
# باید ببینید: "Deep link detected: realty"
```

### Test 2: Redis Session Storage

```bash
# وارد Redis شوید
docker-compose exec redis redis-cli

# چک کردن session
KEYS user:*:mode
GET user:971505037158:mode
# باید برگردونه: "realty"

# چک کردن TTL (باید ~86400 باشه = 24h)
TTL user:971505037158:mode
```

### Test 3: Multiple Verticals

```bash
# Test Expo vertical
curl -X POST http://localhost:8000/api/webhook/waha \
  -H "Content-Type: application/json" \
  -d '{
    "event": "message",
    "session": "default",
    "payload": {
      "from": "971501234567@c.us",
      "body": "start_expo",
      "hasMedia": false,
      "_data": {"notifyName": "Expo User"}
    }
  }'

# Check Redis
docker-compose exec redis redis-cli GET user:971501234567:mode
# Should return: "expo"
```

## واقعی Testing (از واتساپ)

### مرحله 1: Scan QR Code

1. برو به: `http://YOUR_SERVER_IP:3001/api/dashboard`
2. QR Code رو اسکن کن با گوشیت
3. منتظر بمون تا Connected بشه

### مرحله 2: فرستادن Deep Link

از واتساپ به شماره‌ای که اسکن کردی پیام بفرست:

```
start_realty
```

### مرحله 3: چک کردن Backend Logs

```bash
docker-compose logs -f backend | grep -E "Deep link|Vertical|mode"
```

باید ببینی:
```
INFO - Deep link detected: realty (pattern: start_realty)
INFO - Set user 971505037158 to mode: realty
INFO - Using Waha WhatsApp provider for tenant X
INFO - [Waha] Message sent to 971505037158
```

### مرحله 4: Test Session Persistence

1. پیام عادی بفرست (بدون deep link):
   ```
   سلام، قیمت آپارتمان چنده؟
   ```

2. چک کن که همچنان به realty vertical route میشه:
   ```bash
   docker-compose logs backend | tail -20
   ```

## Deep Links برای Production

### لینک‌های نهایی (جایگزین کردن شماره)

```
🏠 Realty: https://wa.me/YOUR_NUMBER?text=start_realty
✈️ Travel: https://wa.me/YOUR_NUMBER?text=start_travel  
🎪 Expo: https://wa.me/YOUR_NUMBER?text=start_expo
🏥 Clinic: https://wa.me/YOUR_NUMBER?text=start_clinic
```

این لینک‌ها رو بذار توی:
- Instagram Bio
- Website Footer
- Email Signatures
- Marketing Materials

## Monitoring

### چک کردن Health

```bash
# Backend health
curl http://localhost:8000/health

# Waha health
curl http://localhost:3001/health
```

### آمار استفاده

```bash
# تعداد active sessions
docker-compose exec redis redis-cli KEYS "user:*:mode" | wc -l

# لیست تمام verticals فعال
docker-compose exec redis redis-cli --scan --pattern "user:*:mode" | \
  xargs docker-compose exec redis redis-cli MGET
```

## عیب‌یابی

### مشکل 1: Webhook نمی‌خوره

```bash
# چک کردن connectivity از Waha به Backend
docker-compose exec waha curl http://backend:8000/health

# باید 200 OK برگردونه
```

### مشکل 2: پیام‌ها Forward نمیشن

```bash
# چک کردن whatsapp_bot_manager
docker-compose logs backend | grep "WhatsAppBotManager"

# باید ببینی: "WhatsAppBotManager initialized with X tenants"
```

### مشکل 3: Deep Link تشخیص داده نمیشه

```bash
# چک کردن regex patterns
docker-compose logs backend | grep "detect_deep_link"

# اگر خطا دیدی، چک کن vertical_router.py
```

## Rollback Plan

اگر مشکلی پیش اومد:

```bash
# Stop Waha
docker-compose stop waha

# Revert to Meta/Twilio
# در .env ست کن:
# USE_WAHA_WHATSAPP=false

# Restart backend
docker-compose restart backend
```

## Success Criteria

✅ Waha container اجرا شده و healthy است
✅ QR Code اسکن شده و Connected است  
✅ Deep links تشخیص داده میشن
✅ Redis sessions ذخیره میشن
✅ پیام‌ها به vertical درست route میشن
✅ Voice/Image messages کار می‌کنن

---

**زمان تخمینی**: 15-20 دقیقه
**نیاز به Downtime**: خیر (zero-downtime deployment)
