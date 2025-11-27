# راهنمای سریع راه‌اندازی (Quick Setup Guide)

## مشکلات رایج و راه‌حل‌ها

### 1️⃣ پیام "Properties module coming soon!"

**علت**: هیچ ملکی در دیتابیس وجود ندارد

**راه‌حل**:
```bash
# روی سرور اجرا کنید:
cd /opt/ArtinSmartRealty
docker compose exec backend python /app/setup_sample_data.py
```

یا از داشبورد:
1. به `https://realty.artinsmartagent.com` بروید
2. لاگین کنید
3. Settings → Properties → Add Property

---

### 2️⃣ Webhook از IP استفاده می‌کند نه دامنه

**مشکل فعلی**:
```
http://72.60.196.192/webhook/telegram/...
```

**باید باشد**:
```
https://realty.artinsmartagent.com/webhook/telegram/...
```

**راه‌حل**:
```bash
# روی سرور:
cd /opt/ArtinSmartRealty
docker compose exec backend python /app/setup_telegram_webhook.py
```

یا دستی:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://realty.artinsmartagent.com/webhook/telegram/<YOUR_BOT_TOKEN>"}'
```

---

### 3️⃣ سوپرادمین کار نمی‌کند

**اطلاعات لاگین**:
```
Email: admin@artinsmartrealty.com
Password: SuperARTIN2588357!
```

اگر کار نمی‌کند:
```bash
# چک کنید که سرویس‌ها در حال اجرا هستند:
docker compose ps

# لاگ‌های backend را ببینید:
docker compose logs backend -f

# سرویس‌ها را ری‌استارت کنید:
docker compose restart backend
```

---

### 4️⃣ تلگرام برای یوزر جدید کار نمی‌کند

**چک‌لیست**:
- [ ] Webhook با دامنه صحیح ست شده؟
- [ ] Bot token در Settings تنظیم شده؟
- [ ] Backend در حال اجرا است؟
- [ ] SSL/HTTPS فعال است؟

**بررسی وضعیت Webhook**:
```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
```

**خروجی صحیح**:
```json
{
  "ok": true,
  "result": {
    "url": "https://realty.artinsmartagent.com/webhook/telegram/...",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

---

## دستورات مفید

### مدیریت Docker

```bash
# مشاهده وضعیت
docker compose ps

# مشاهده لاگ‌ها
docker compose logs backend -f

# ری‌استارت سرویس
docker compose restart backend

# دانلود و اجرای مجدد
docker compose down
docker compose up -d

# پاک کردن همه چیز (احتیاط!)
docker compose down -v
```

### مدیریت دیتابیس

```bash
# اتصال به PostgreSQL
docker compose exec db psql -U postgres -d artinrealty

# بررسی تعداد tenants
docker compose exec db psql -U postgres -d artinrealty -c "SELECT id, name, email FROM tenants;"

# بررسی تعداد properties
docker compose exec db psql -U postgres -d artinrealty -c "SELECT COUNT(*) FROM tenant_properties;"

# بررسی leads
docker compose exec db psql -U postgres -d artinrealty -c "SELECT COUNT(*) FROM leads;"
```

### اضافه کردن دیتای نمونه

```bash
# کپی اسکریپت‌ها به container
docker cp setup_sample_data.py artinrealty-backend:/app/
docker cp setup_telegram_webhook.py artinrealty-backend:/app/

# اجرا
docker compose exec backend python /app/setup_sample_data.py
docker compose exec backend python /app/setup_telegram_webhook.py
```

---

## تست کردن سیستم

### 1. تست API

```bash
# Health check
curl https://realty.artinsmartagent.com/health

# Login (Super Admin)
curl -X POST https://realty.artinsmartagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@artinsmartrealty.com","password":"SuperARTIN2588357!"}'
```

### 2. تست Telegram Bot

1. Bot خود را در Telegram پیدا کنید
2. دستور `/start` را بزنید
3. باید پیام خوش‌آمدگویی دریافت کنید

### 3. تست Dashboard

1. به `https://realty.artinsmartagent.com` بروید
2. با سوپرادمین لاگین کنید
3. لیست tenants را ببینید

---

## مراحل اولیه راه‌اندازی

### برای اولین بار:

```bash
# 1. کلون و تنظیم
git clone https://github.com/arezoojoon/ArtinSmartRealty.git
cd ArtinSmartRealty
cp .env.example .env
nano .env  # تنظیمات را پر کنید

# 2. اجرا
docker compose up -d

# 3. اضافه کردن دیتای نمونه
docker cp setup_sample_data.py artinrealty-backend:/app/
docker compose exec backend python /app/setup_sample_data.py

# 4. تنظیم Webhook
docker cp setup_telegram_webhook.py artinrealty-backend:/app/
docker compose exec backend python /app/setup_telegram_webhook.py

# 5. تست
curl https://realty.artinsmartagent.com/health
```

---

## پشتیبانی

برای مشکلات:
1. لاگ‌های backend را چک کنید: `docker compose logs backend -f`
2. وضعیت سرویس‌ها را ببینید: `docker compose ps`
3. دیتابیس را بررسی کنید
4. Webhook را تست کنید

---

**دامنه شما**: `realty.artinsmartagent.com`  
**سوپرادمین**: `admin@artinsmartrealty.com` / `SuperARTIN2588357!`
