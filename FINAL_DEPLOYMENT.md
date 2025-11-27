# 🚀 دستورات نهایی برای فعال‌سازی کامل سیستم

## وضعیت فعلی:
✅ SSL Certificate گرفته شد
✅ Sample data اضافه شد
✅ Properties module ساخته شد
⚠️ HTTPS هنوز فعال نیست (nginx.conf بروز نشده روی سرور)
⚠️ Frontend باید rebuild شود

---

## دستورات روی سرور:

```bash
cd /opt/ArtinSmartRealty

# 1. دریافت آخرین تغییرات
git pull origin copilot/build-multi-tenant-saas-architecture

# 2. Rebuild frontend (برای Properties module)
docker compose build frontend

# 3. ری‌استارت همه سرویس‌ها
docker compose down
docker compose up -d

# 4. چک کردن HTTPS
curl -I https://realty.artinsmartagent.com/health

# 5. تنظیم مجدد Webhook با HTTPS
curl -X POST "https://api.telegram.org/bot7941411336:AAGpkPMhg5Wa5RkWDD06sM3UbJ5veWwVgSs/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://realty.artinsmartagent.com/webhook/telegram/7941411336:AAGpkPMhg5Wa5RkWDD06sM3UbJ5veWwVgSs","drop_pending_updates":true}'

# 6. چک کردن Webhook
curl "https://api.telegram.org/bot7941411336:AAGpkPMhg5Wa5RkWDD06sM3UbJ5veWwVgSs/getWebhookInfo"
```

---

## برای Bot دوم (ArtinSmartRealtyBot):

```bash
# ابتدا tenant جدید بسازید از Dashboard:
# 1. Login به https://realty.artinsmartagent.com
# 2. Register حساب جدید
# 3. Settings → Telegram Bot Token: 8479049340:AAFFzrA2lfL0m49E6Y9xjjU77NRmpw5gCEc

# سپس webhook را ست کنید:
curl -X POST "https://api.telegram.org/bot8479049340:AAFFzrA2lfL0m49E6Y9xjjU77NRmpw5gCEc/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://realty.artinsmartagent.com/webhook/telegram/8479049340:AAFFzrA2lfL0m49E6Y9xjjU77NRmpw5gCEc","drop_pending_updates":true}'
```

---

## تست نهایی:

### 1. تست HTTPS
```bash
curl https://realty.artinsmartagent.com/health
# باید برگرداند: {"status":"healthy","timestamp":"..."}
```

### 2. تست Dashboard
- به https://realty.artinsmartagent.com بروید
- Login کنید
- به Properties → Add Property بروید
- یک property اضافه کنید

### 3. تست Telegram Bot
- Bot را در تلگرام پیدا کنید: @Taranteenproperties_bot یا @ArtinSmartRealtyBot
- پیام /start بزنید
- باید پیام خوش‌آمدگویی دریافت کنید

---

## عیب‌یابی:

### اگر Webhook همچنان timeout می‌دهد:

```bash
# چک کنید nginx در حال استفاده از SSL است:
docker compose exec nginx cat /etc/nginx/nginx.conf | grep "listen 443"

# باید خط زیر را ببینید:
# listen 443 ssl http2;

# اگر ندیدید، یعنی nginx.conf بروز نشده. دوباره pull کنید:
git pull origin copilot/build-multi-tenant-saas-architecture
docker compose restart nginx
```

### اگر Properties در Dashboard نیست:

```bash
# Frontend را rebuild کنید:
docker compose build frontend
docker compose up -d frontend
```

### اگر Bot جواب نمی‌دهد:

```bash
# لاگ‌های backend را چک کنید:
docker compose logs backend -f

# باید ببینید:
# "Bot started for tenant: ..."

# اگر نبود، backend را ری‌استارت کنید:
docker compose restart backend
```

---

## چک‌لیست نهایی:

- [ ] `git pull` انجام شد
- [ ] Frontend rebuild شد (`docker compose build frontend`)
- [ ] HTTPS کار می‌کند (`curl https://realty.artinsmartagent.com/health`)
- [ ] Webhook با HTTPS ست شد
- [ ] Webhook بدون error است (`"last_error_message"` خالی است)
- [ ] Dashboard باز می‌شود (https://realty.artinsmartagent.com)
- [ ] Properties module در Dashboard است
- [ ] Bot تلگرام به `/start` جواب می‌دهد
- [ ] Sample properties در Dashboard نمایش داده می‌شود

---

## دستورات سریع:

```bash
# همه چیز را یکجا انجام بده:
cd /opt/ArtinSmartRealty && \
  git pull origin copilot/build-multi-tenant-saas-architecture && \
  docker compose build frontend && \
  docker compose down && \
  docker compose up -d && \
  sleep 10 && \
  curl -X POST "https://api.telegram.org/bot7941411336:AAGpkPMhg5Wa5RkWDD06sM3UbJ5veWwVgSs/setWebhook" \
    -H "Content-Type: application/json" \
    -d '{"url":"https://realty.artinsmartagent.com/webhook/telegram/7941411336:AAGpkPMhg5Wa5RkWDD06sM3UbJ5veWwVgSs","drop_pending_updates":true}' && \
  echo -e "\n\n✅ Done! Test your bot now in Telegram"
```

---

**دامنه**: realty.artinsmartagent.com  
**Bot 1**: @Taranteenproperties_bot (7941411336:AAGpkPMhg...)  
**Bot 2**: @ArtinSmartRealtyBot (8479049340:AAFFzrA2l...)  
**Super Admin**: admin@artinsmartrealty.com / SuperARTIN2588357!
