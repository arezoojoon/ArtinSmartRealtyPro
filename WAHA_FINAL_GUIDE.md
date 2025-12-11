# 🎯 دستورات نهایی - استفاده از API Key موجود

## مشکل چیه؟
Waha یک API key تولید کرده و از `WAHA_API_KEY_STRATEGY=NONE` پشتیبانی نمی‌کنه. پس باید از همون API key استفاده کنیم.

---

## راه‌حل: استفاده از API Key تولید شده

### مرحله 1: دریافت کد جدید

```bash
cd /opt/ArtinSmartRealty
git pull origin main
chmod +x waha_use_generated_key.sh
```

### مرحله 2: اجرای اسکریپت استخراج API Key

```bash
./waha_use_generated_key.sh
```

این اسکریپت:
- API key را از لاگ Waha می‌گیره
- Session را شروع می‌کنه
- لینک QR Code را می‌دهد

---

## مرحله 3: استفاده Manual (اگر اسکریپت کار نکرد)

### 3.1 استخراج API Key از لاگ

```bash
docker-compose logs waha | grep "WAHA_API_KEY="
```

خروجی شبیه این:
```
WAHA_API_KEY=a256115929d94c448f1a402f8cdde888
```

API Key رو کپی کن (مثلاً: `a256115929d94c448f1a402f8cdde888`)

### 3.2 شروع Session با API Key

```bash
# جایگزین کن YOUR_API_KEY را با API key واقعی
API_KEY="a256115929d94c448f1a402f8cdde888"

curl -X POST http://localhost:3001/api/sessions/start \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: $API_KEY" \
  -d '{
    "name": "default",
    "config": {
      "webhooks": [
        {
          "url": "http://backend:8000/api/webhook/waha",
          "events": ["message"]
        }
      ]
    }
  }'
```

خروجی:
```json
{"name":"default","status":"STARTING"}
```

### 3.3 دریافت QR Code

در مرورگر این آدرس را باز کن (API key را جایگزین کن):

```
http://72.60.196.192:3001/api/sessions/default/auth/qr?api_key=YOUR_API_KEY
```

مثال واقعی:
```
http://72.60.196.192:3001/api/sessions/default/auth/qr?api_key=a256115929d94c448f1a402f8cdde888
```

### 3.4 اسکن QR Code

1. گوشیت رو بردار
2. واتساپ → Settings → Linked Devices
3. Link a Device
4. QR Code رو اسکن کن

### 3.5 چک وضعیت

```bash
curl -H "X-Api-Key: $API_KEY" http://localhost:3001/api/sessions/default
```

خروجی بعد از اسکن:
```json
{"name":"default","status":"WORKING"}
```

---

## مرحله 4: ذخیره API Key در .env

بعد از اینکه همه چیز کار کرد، API key را در `.env` ذخیره کن:

```bash
# ویرایش .env
nano .env

# این خط را اضافه کن (با API key واقعی)
WAHA_API_KEY=a256115929d94c448f1a402f8cdde888

# ذخیره و خروج (Ctrl+O, Enter, Ctrl+X)
```

### Restart Backend

```bash
docker-compose restart backend
```

حالا backend هم می‌تونه با Waha ارتباط بگیره.

---

## مرحله 5: تست Deep Link

```bash
# ارسال پیام تست
curl -X POST http://localhost:8000/api/webhook/waha \
  -H "Content-Type: application/json" \
  -d '{
    "event": "message",
    "session": "default",
    "payload": {
      "from": "971505037158@c.us",
      "body": "start_realty"
    }
  }'

# چک Redis
docker-compose exec redis redis-cli
> GET user:971505037158:mode
```

باید `"realty"` را ببینی.

---

## تست ارسال پیام از Backend

```bash
# تست ارسال پیام از طریق Waha
curl -H "X-Api-Key: $API_KEY" \
  -X POST http://localhost:3001/api/sendText \
  -H "Content-Type: application/json" \
  -d '{
    "session": "default",
    "chatId": "971505037158@c.us",
    "text": "سلام! این یک پیام تست از ArtinSmartRealty است 🏠"
  }'
```

---

## لینک‌های نهایی برای کاربران

🏠 **املاک:** `https://wa.me/971505037158?text=start_realty`  
✈️ **تور:** `https://wa.me/971505037158?text=start_travel`  
🎪 **نمایشگاه:** `https://wa.me/971505037158?text=start_expo`  
🏥 **کلینیک:** `https://wa.me/971505037158?text=start_clinic`

---

## Commands Quick Reference

```bash
# API Key از لاگ
docker-compose logs waha | grep "WAHA_API_KEY="

# شروع session
curl -X POST http://localhost:3001/api/sessions/start \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: YOUR_KEY" \
  -d '{"name":"default","config":{"webhooks":[{"url":"http://backend:8000/api/webhook/waha","events":["message"]}]}}'

# QR Code در مرورگر
http://72.60.196.192:3001/api/sessions/default/auth/qr?api_key=YOUR_KEY

# وضعیت session
curl -H "X-Api-Key: YOUR_KEY" http://localhost:3001/api/sessions/default

# ارسال تست
curl -H "X-Api-Key: YOUR_KEY" -X POST http://localhost:3001/api/sendText \
  -H "Content-Type: application/json" \
  -d '{"session":"default","chatId":"971505037158@c.us","text":"Test"}'
```

---

## Troubleshooting

### مشکل: Session شروع نمی‌شه

```bash
# Stop session
curl -H "X-Api-Key: YOUR_KEY" -X POST http://localhost:3001/api/sessions/default/stop

# Start again
curl -H "X-Api-Key: YOUR_KEY" -X POST http://localhost:3001/api/sessions/default/start
```

### مشکل: QR Code نمایش نمی‌شه

```bash
# Restart Waha
docker-compose restart waha

# دوباره شروع session
```

### مشکل: Webhook کار نمی‌کنه

```bash
# چک کن backend در شبکه در دسترسه
docker-compose exec waha ping backend

# چک لاگ‌های backend
docker-compose logs -f backend | grep waha
```
