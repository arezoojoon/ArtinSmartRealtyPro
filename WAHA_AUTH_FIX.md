# 🚨 Waha Authentication راه‌حل سریع

## مشکل
Waha به صورت پیش‌فرض authentication دارد و تنظیمات environment variable در docker-compose اعمال نشده.

## راه‌حل 1: استفاده از API Key پیش‌فرض (سریع‌ترین)

Waha یک API key پیش‌فرض دارد که باید در header ارسال شود.

### دستورات روی سرور:

```bash
cd /opt/ArtinSmartRealty

# 1. شروع session با API key
curl -X POST http://localhost:3001/api/sessions/start \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your-secret-api-key" \
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

# 2. دریافت QR Code
curl -H "X-Api-Key: your-secret-api-key" \
  http://localhost:3001/api/sessions/default/auth/qr > qr.png

# یا در مرورگر:
# http://72.60.196.192:3001/api/sessions/default/auth/qr?api_key=your-secret-api-key
```

---

## راه‌حل 2: غیرفعال کردن Authentication (امن‌تر در production)

### مرحله 1: ویرایش docker-compose.yml

```bash
nano docker-compose.yml
```

در بخش `waha` این خطوط را اضافه کن:

```yaml
environment:
  - WHATSAPP_DEFAULT_ENGINE=WEBJS
  - WHATSAPP_RESTART_ON_FAIL=True
  - WHATSAPP_AUTOREFRESH_QR=True
  - WHATSAPP_HOOK_EVENTS=message,message.any
  - WHATSAPP_HOOK_URL=http://backend:8000/api/webhook/waha
  - WHATSAPP_API_KEY=                    # ← این خط را اضافه کن (خالی)
  - WHATSAPP_SWAGGER_ENABLED=false       # ← غیرفعال کردن Swagger
```

### مرحله 2: Restart Waha

```bash
docker-compose down waha
docker-compose up -d waha

# صبر کن 10 ثانیه
sleep 10

# تست بدون API key
curl -X POST http://localhost:3001/api/sessions/start \
  -H "Content-Type: application/json" \
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

---

## راه‌حل 3: استفاده از waha_quick_fix.sh (اتوماتیک)

```bash
cd /opt/ArtinSmartRealty
git pull origin main
chmod +x waha_quick_fix.sh
./waha_quick_fix.sh
```

این اسکریپت:
1. Waha را متوقف می‌کند
2. Volume قدیمی را پاک می‌کند
3. Waha را با تنظیمات جدید راه‌اندازی می‌کند

---

## تست سریع

```bash
# چک کردن وضعیت Waha
docker-compose ps waha

# دیدن لاگ‌ها
docker-compose logs waha | tail -30

# چک environment variables
docker-compose exec waha env | grep WHATSAPP
```

---

## اگر همه‌چی fail شد - Plan B: استفاده از Image دیگر

```bash
# ویرایش docker-compose.yml
nano docker-compose.yml

# تغییر image از:
image: devlikeapro/waha:latest

# به:
image: devlikeapro/waha:noweb

# سپس:
docker-compose pull waha
docker-compose up -d waha
```

`waha:noweb` نسخه‌ای بدون authentication پیش‌فرض است.

---

## بعد از راه‌اندازی موفق

```bash
# شروع session
curl -X POST http://localhost:3001/api/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"name":"default","config":{"webhooks":[{"url":"http://backend:8000/api/webhook/waha","events":["message"]}]}}'

# QR Code در مرورگر:
http://72.60.196.192:3001/api/sessions/default/auth/qr

# چک وضعیت
curl http://localhost:3001/api/sessions/default

# باید ببینی:
# {"name":"default","status":"STARTING"} 
# بعد از اسکن QR:
# {"name":"default","status":"WORKING"}
```

---

## پیشنهاد نهایی (ساده‌ترین)

روی سرور این را اجرا کن:

```bash
cd /opt/ArtinSmartRealty

# Stop و remove کردن Waha
docker-compose down waha

# استفاده از noweb image (بدون auth)
sed -i 's|devlikeapro/waha:latest|devlikeapro/waha:noweb|' docker-compose.yml

# شروع دوباره
docker-compose up -d waha

# صبر 10 ثانیه
sleep 10

# تست
curl -X POST http://localhost:3001/api/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"name":"default"}'
```

این باید کار کند! 🎯
