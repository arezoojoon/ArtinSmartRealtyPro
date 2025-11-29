# WhatsApp Integration Debug Guide

## مشکل: واتساپ پیام دریافت نمیکنه

### ✅ چک‌لیست تشخیص مشکل

#### 1. بررسی Database
```sql
SELECT 
    id, 
    name,
    whatsapp_phone_number_id,
    LENGTH(whatsapp_access_token) as token_length,
    whatsapp_verify_token
FROM tenants 
WHERE id = 1;
```

**نتیجه باید:**
- `whatsapp_phone_number_id` = `909710645559652` ✅
- `token_length` ≈ 200 characters ✅
- `whatsapp_verify_token` = `ArtinSmartRealty2024SecureWebhookToken9876543210` ✅

---

#### 2. بررسی Meta Webhook Configuration

**مراحل:**
1. برو به: https://developers.facebook.com/apps
2. انتخاب App
3. WhatsApp → Configuration
4. بخش **Webhook**:

**تنظیمات صحیح:**
```
Callback URL: https://realty.artinsmartagent.com/webhook/whatsapp
Verify Token: ArtinSmartRealty2024SecureWebhookToken9876543210
```

5. کلیک **Verify and Save**
6. باید پیام **Webhook Verified** رو ببینی

---

#### 3. بررسی Webhook Subscriptions

**مهم:** باید subscribe شده باشه به **messages** field!

**چک کن:**
1. در صفحه **Webhook Configuration**
2. بخش **Webhook fields**
3. تیک بزن روی: ✅ **messages**

**فیلدهای مورد نیاز:**
- ✅ messages
- ✅ messaging_postbacks (اختیاری)
- ✅ message_echoes (اختیاری)

---

#### 4. تست Webhook با cURL

**از VPS تست کن:**
```bash
# SSH به VPS
ssh root@srv1151343.main-hosting.eu

# تست webhook verification
curl "https://realty.artinsmartagent.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=ArtinSmartRealty2024SecureWebhookToken9876543210&hub.challenge=TEST123"
```

**نتیجه باید:** `TEST123` برگردونه

---

#### 5. بررسی Logs در VPS

```bash
# لاگ‌های واتساپ
docker-compose logs backend | grep -i whatsapp

# لاگ‌های webhook
docker-compose logs backend | grep -E "POST.*webhook/whatsapp|📥 Incoming"
```

**لاگ‌های مورد انتظار وقتی پیام بیاد:**
```
📥 Incoming WhatsApp message from: 971XXXXXXXXX
Processing message for tenant: ArtinSmartRealty
✅ Response sent to 971XXXXXXXXX
```

---

#### 6. تست ارسال پیام واقعی

**مراحل:**
1. WhatsApp رو باز کن
2. پیام به شماره تجاری بفرست: **سلام**
3. چک کن لاگ‌های backend

**اگر کار کرد:**
```
2025-11-30 XX:XX:XX - whatsapp_bot - INFO - 📥 Incoming message from: 971XXX
2025-11-30 XX:XX:XX - brain - INFO - Processing message: سلام
2025-11-30 XX:XX:XX - whatsapp_bot - INFO - ✅ Response sent
```

**اگر کار نکرد:**
- هیچ لاگی نمیاد → Webhook ثبت نشده
- Error میاد → مشکل در کد

---

#### 7. مشکلات رایج و راه‌حل‌ها

**مشکل 1: "No tenant found for WhatsApp phone ID: XXX"**
```sql
-- چک کن phone_number_id توی Meta با دیتابیس یکیه
SELECT whatsapp_phone_number_id FROM tenants WHERE id = 1;
```

**مشکل 2: "WhatsApp provider not configured"**
- Access Token منقضی شده
- از Meta یه token جدید بگیر

**مشکل 3: Webhook verification failed**
- Verify token غلطه
- از دیتابیس whatsapp_verify_token رو چک کن

**مشکل 4: Messages نمیان**
- Webhook subscribe نشده به "messages"
- برو Meta → Webhook fields → تیک "messages" رو بزن

---

#### 8. Test با Meta Graph API Explorer

**ارسال پیام تستی:**
```bash
curl -X POST \
  'https://graph.facebook.com/v18.0/909710645559652/messages' \
  -H 'Authorization: Bearer EAAT58VLIlCcBQDvMnjN...' \
  -H 'Content-Type: application/json' \
  -d '{
    "messaging_product": "whatsapp",
    "to": "971XXXXXXXXX",
    "type": "text",
    "text": {
      "body": "Test message from API"
    }
  }'
```

---

## ✅ Success Criteria

وقتی همه چی درسته:

1. ✅ Webhook verified در Meta
2. ✅ Subscribed to "messages" field
3. ✅ Test cURL برمیگردونه challenge
4. ✅ پیام بفرستی → لاگ "📥 Incoming" میاد
5. ✅ Bot جواب میده در عرض 2-3 ثانیه
6. ✅ Lead در دیتابیس ذخیره میشه

---

## 🔧 Quick Fix Commands

```bash
# 1. بررسی سرویس‌ها
docker-compose ps

# 2. Restart backend
docker-compose restart backend

# 3. دیدن لاگ‌های زنده
docker-compose logs -f backend

# 4. چک کردن health
curl http://localhost:8000/health

# 5. چک کردن webhook از خارج
curl https://realty.artinsmartagent.com/health
```

---

## 📞 Meta Business Support

اگر همه کارها رو کردی و باز کار نکرد:

1. برو Meta Business Help Center
2. Case باز کن برای WhatsApp API
3. Screenshot از webhook config بگیر
4. لاگ‌های error رو بفرست
