# 📱 Waha WhatsApp Setup - دستورات سرور

## مرحله 1: دیپلوی کد جدید

```bash
cd /opt/ArtinSmartRealty
git pull origin main
chmod +x deploy_waha_fix.sh
./deploy_waha_fix.sh
```

## مرحله 2: شروع Session واتساپ

```bash
# شروع session با نام "default"
curl -X POST http://localhost:3001/api/sessions/start \
  -H "Content-Type: application/json" \
  -d '{
    "name": "default",
    "config": {
      "proxy": null,
      "webhooks": [
        {
          "url": "http://backend:8000/api/webhook/waha",
          "events": ["message"]
        }
      ]
    }
  }'
```

## مرحله 3: دریافت QR Code

### روش 1: مشاهده در مرورگر (توصیه می‌شود)

به این آدرس در مرورگر برو:
```
http://srv1151343.hstgr.io:3001/api/sessions/default/auth/qr
```

یک تصویر QR code نمایش داده می‌شود.

### روش 2: Terminal

```bash
curl http://localhost:3001/api/sessions/default/auth/qr
```

این یک تصویر PNG برمی‌گرداند که می‌تونی با ابزار مثل `imgcat` یا `chafa` نمایش بدی، یا توی مرورگر باز کنی.

## مرحله 4: اسکن QR Code

1. گوشیت رو بردار
2. واتساپ رو باز کن
3. Settings → Linked Devices
4. "Link a Device" رو بزن
5. QR Code رو اسکن کن

## مرحله 5: بررسی وضعیت

```bash
# چک کن session متصل شد یا نه
curl http://localhost:3001/api/sessions/default
```

باید ببینی:
```json
{
  "name": "default",
  "status": "WORKING"
}
```

## تست Deep Link

بعد از اتصال موفق، این تست رو انجام بده:

```bash
# تست deep link از طریق webhook
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
```

## بررسی Redis

```bash
docker-compose exec redis redis-cli

# در Redis CLI:
KEYS user:*:mode
GET user:971505037158:mode
```

باید "realty" رو ببینی.

## مانیتورینگ

```bash
# لاگ‌های Waha
docker-compose logs -f waha

# لاگ‌های Backend (برای دیدن webhook calls)
docker-compose logs -f backend | grep "waha"
```

## لینک‌های Deep Link برای کاربران

بعد از راه‌اندازی، این لینک‌ها رو به کاربرات بده:

🏠 **املاک:**
```
https://wa.me/971505037158?text=start_realty
```

✈️ **تور:**
```
https://wa.me/971505037158?text=start_travel
```

🎪 **نمایشگاه:**
```
https://wa.me/971505037158?text=start_expo
```

🏥 **کلینیک:**
```
https://wa.me/971505037158?text=start_clinic
```

## Troubleshooting

### مشکل: QR Code نمایش نمی‌شود

```bash
# Restart Waha
docker-compose restart waha

# چک لاگ‌ها
docker-compose logs waha | tail -50
```

### مشکل: Session disconnect می‌شود

```bash
# Stop session
curl -X POST http://localhost:3001/api/sessions/default/stop

# Restart session
curl -X POST http://localhost:3001/api/sessions/default/start
```

### مشکل: Webhook کار نمی‌کند

```bash
# چک کن backend در شبکه Docker در دسترس هست
docker-compose exec waha ping backend

# چک کن webhook URL درست set شده
curl http://localhost:3001/api/sessions/default | grep webhook
```

## Commands Reference

```bash
# List all sessions
curl http://localhost:3001/api/sessions

# Get session status
curl http://localhost:3001/api/sessions/default

# Stop session
curl -X POST http://localhost:3001/api/sessions/default/stop

# Restart session
curl -X POST http://localhost:3001/api/sessions/default/restart

# Get QR code
curl http://localhost:3001/api/sessions/default/auth/qr

# Send test message
curl -X POST http://localhost:3001/api/sendText \
  -H "Content-Type: application/json" \
  -d '{
    "session": "default",
    "chatId": "971505037158@c.us",
    "text": "سلام! این یک پیام تست از Waha است"
  }'
```
