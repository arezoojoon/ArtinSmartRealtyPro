# 🚀 راهنمای Deploy روتر WhatsApp Gateway

## مرحله ۱: Build و Start کل سیستم

```bash
# در سرور
cd /opt/ArtinSmartRealtyPro/ArtinSmartRealty

# Build کل سیستم (شامل روتر)
docker-compose build

# Start همه سرویس‌ها
docker-compose up -d

# چک کردن وضعیت
docker-compose ps
```

**باید این سرویس‌ها running باشند:**
- ✅ `artinrealty-db`
- ✅ `artinrealty-redis`
- ✅ `artinrealty-backend`
- ✅ `artinrealty-frontend`
- ✅ `artinrealty-waha`
- ✅ `artinrealty-router` **(جدید!)**

---

## مرحله ۲: تنظیم Webhook WAHA

باید به WAHA بگیم که پیام‌ها رو به **Router** بفرسته (نه مستقیم به Backend):

```bash
curl -X POST \
  -H "X-Api-Key: waha_artinsmartrealty_secure_key_2024" \
  -H "Content-Type: application/json" \
  -d '{
    "webhooks": [
      {
        "url": "http://router:8001/webhook/waha",
        "events": ["message"]
      }
    ]
  }' \
  http://localhost:3001/api/sessions/default
```

**تایید:**
```bash
curl -H "X-Api-Key: waha_artinsmartrealty_secure_key_2024" \
  http://localhost:3001/api/sessions/default
```

باید `"webhooks"` شامل `"http://router:8001/webhook/waha"` باشد.

---

## مرحله ۳: تست سیستم روتینگ

### ۱. چک کردن Health روتر

```bash
curl http://localhost:8001/health
```

**خروجی موفق:**
```json
{
  "status": "healthy",
  "service": "whatsapp-gateway-router",
  "total_locked_users": 0,
  "unique_tenants": 0
}
```

### ۲. تست دیپ لینک (Deep Link)

#### لینک تنانت ۲ (سامان احمدی):
```
https://wa.me/971557357753?text=start_realty_2
```

**منطق:**
1. مشتری روی لینک کلیک می‌کنه
2. واتساپ باز میشه با متن: `start_realty_2`
3. مشتری Send می‌کنه
4. WAHA به Router می‌فرسته
5. Router شماره مشتری رو به Tenant 2 قفل می‌کنه
6. Router پیام رو با header `X-Tenant-ID: 2` به Backend می‌فرسته
7. Backend دیتابیس سامان احمدی رو لود می‌کنه و جواب میده

### ۳. چک کردن قفل شدن کاربر

```bash
# فرض کنیم شماره مشتری: 971501234567
curl http://localhost:8001/router/user/971501234567
```

**خروجی موفق:**
```json
{
  "phone": "971501234567",
  "locked_to_tenant": 2,
  "status": "active_session"
}
```

### ۴. تست پیام معمولی (بعد از قفل شدن)

حالا اگر همون مشتری یه پیام عادی بفرسته (مثلاً "سلام"):
```
Customer: سلام
```

روتر خودکار می‌فهمه که این کاربر قبلاً به Tenant 2 قفل شده و پیام رو به اون تنانت می‌فرسته.

---

## مرحله ۴: مانیتورینگ

### چک کردن Logs

```bash
# Logs روتر
docker logs artinrealty-router -f

# دنبال این پیام‌ها بگرد:
# 🔒 LOCKED: User 971501234567 → Tenant 2
# 🔀 Routing 971501234567 → Tenant 2 (existing session)
# ✅ Forwarded to Tenant 2
```

```bash
# Logs بک‌اند
docker logs artinrealty-backend -f

# دنبال این پیام‌ها بگرد:
# 🔀 Routed message for Tenant 2
```

```bash
# Logs WAHA
docker logs artinrealty-waha -f
```

### آمار روتینگ

```bash
curl http://localhost:8001/router/stats
```

**خروجی نمونه:**
```json
{
  "total_locked_users": 15,
  "unique_tenants": 3,
  "mappings": {
    "971501234567": "2",
    "971502345678": "5",
    "971503456789": "2"
  }
}
```

---

## مرحله ۵: ساخت Deep Link برای هر Tenant

### فرمول:
```
https://wa.me/971557357753?text=start_realty_{TENANT_ID}
```

### مثال‌ها:

**Tenant 1:**
```
https://wa.me/971557357753?text=start_realty_1
```

**Tenant 2 (سامان احمدی):**
```
https://wa.me/971557357753?text=start_realty_2
```

**Tenant 55:**
```
https://wa.me/971557357753?text=start_realty_55
```

### اضافه کردن به Dashboard

در Dashboard، برای هر تنانت:
1. برو به صفحه تنانت
2. Deep Link رو کپی کن
3. به تنانت بده تا به مشتری‌هاش بفرسته

---

## 🐛 عیب‌یابی (Troubleshooting)

### مشکل: روتر start نمیشه

```bash
# چک کردن logs
docker logs artinrealty-router

# Rebuild
docker-compose build router
docker-compose up -d router
```

### مشکل: پیام‌ها به روتر نمیرسه

```bash
# چک کردن webhook WAHA
curl -H "X-Api-Key: waha_artinsmartrealty_secure_key_2024" \
  http://localhost:3001/api/sessions/default | grep webhook

# اگر نبود، دوباره تنظیمش کن (مرحله ۲)
```

### مشکل: پیام‌ها به بک‌اند نمیرسه

```bash
# چک کردن شبکه داکر
docker network inspect artinrealty-network | grep router

# اگر router در شبکه نیست:
docker-compose down
docker-compose up -d
```

### مشکل: کاربر قفل نمیشه

```bash
# چک کردن فایل دیتابیس
docker exec artinrealty-router cat /app/data/user_tenant_map.json

# اگر خالی بود یا خطا داشت:
docker exec artinrealty-router rm /app/data/user_tenant_map.json
docker-compose restart router
```

### باز کردن قفل یک کاربر (Manual Unlock)

```bash
curl -X POST http://localhost:8001/router/unlock/971501234567
```

---

## 📊 Checklist نهایی

- [ ] همه containerها running هستند (`docker-compose ps`)
- [ ] WAHA webhook به router اشاره می‌کنه
- [ ] Router health check موفق (`curl localhost:8001/health`)
- [ ] تست دیپ لینک انجام شد (start_realty_2)
- [ ] کاربر قفل شد (`/router/user/{phone}` چک کردی)
- [ ] پیام معمولی به تنانت درست روت شد
- [ ] Logs روتر و بک‌اند بدون خطا هستند

---

## 🎯 سناریوی تست کامل

### سناریو: مشتری از طریق لینک سامان احمدی (Tenant 2) وصل میشه

1. **سامان احمدی لینک رو به مشتری میده:**
   ```
   https://wa.me/971557357753?text=start_realty_2
   ```

2. **مشتری کلیک می‌کنه و پیام میفرسته:**
   - متن پیام: `start_realty_2`

3. **Router:**
   ```
   🔒 LOCKED: User 971501234567 → Tenant 2
   ✅ Forwarded to Tenant 2
   ```

4. **Backend:**
   ```
   🔀 Routed message for Tenant 2
   📩 Processing message for tenant: saman ahmadi
   ```

5. **مشتری جواب می‌گیره:**
   ```
   👋 سلام! من دستیار هوشمند سامان احمدی هستم...
   ```

6. **مشتری پیام بعدی رو میفرسته:**
   ```
   من دنبال آپارتمان ۲ خوابه تا ۵۰۰ هزار درهم می‌گردم
   ```

7. **Router خودکار میفهمه:**
   ```
   🔀 Routing 971501234567 → Tenant 2 (existing session)
   ```

8. **Backend پاسخ میده:**
   ```
   عالیه! چند ملک فوق‌العاده برات پیدا کردم...
   ```

---

## ✅ تایید نهایی

بعد از انجام تمام مراحل:

```bash
# ۱. همه سرویس‌ها آپ باشند
docker-compose ps | grep Up

# ۲. روتر سالم باشد
curl http://localhost:8001/health

# ۳. لاگ‌ها بدون خطا
docker logs artinrealty-router --tail 20

# ۴. تست واقعی با موبایل
# لینک رو روی واتساپ بزن و تست کن!
```

---

**🎉 سیستم آماده Scale-Up به ۱۰۰۰+ تنانت است!**

هر تنانت فقط باید `https://wa.me/971557357753?text=start_realty_{ID}` خودش رو به مشتری‌هاش بفرسته و تمام! 🚀
