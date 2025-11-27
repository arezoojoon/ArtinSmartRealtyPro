# 📱 راهنمای سریع WhatsApp Setup

## مرحله 1: Meta Business Account
1. برو به https://business.facebook.com/
2. ساخت Business Account (اگر نداری)
3. Add Product → WhatsApp

## مرحله 2: دریافت Credentials
1. WhatsApp → Settings → API Setup
2. کپی کن:
   - **Phone Number ID**: `123456789012345`
   - **Access Token**: `EAAB...` (از Test/Permanent token)
   - **Business Account ID**: برای آینده

## مرحله 3: ثبت در Database
روش 1 - از Dashboard:
```
1. Login به https://realty.artinsmartagent.com/super-admin
2. Edit tenant
3. وارد کردن:
   - WhatsApp Phone Number ID
   - WhatsApp Access Token
   - WhatsApp Verify Token (generate شده توسط script)
```

روش 2 - از Server:
```bash
# اتصال به database
docker compose exec db psql -U artinrealty -d artinrealty_db

# Update tenant
UPDATE tenants 
SET whatsapp_phone_number_id = '123456789012345',
    whatsapp_access_token = 'YOUR_ACCESS_TOKEN',
    whatsapp_verify_token = 'your-random-token-123'
WHERE email = 'hr.damroodi@gmail.com';
```

## مرحله 4: Webhook Configuration
```bash
# Run setup script
cd /opt/ArtinSmartRealty
python setup_whatsapp_webhook.py
```

خروجی:
```
🌐 Enter your domain: realty.artinsmartagent.com

📋 WhatsApp Webhook Setup Instructions:
   Callback URL: https://realty.artinsmartagent.com/webhook/whatsapp
   Verify Token: abc123xyz789...
```

## مرحله 5: ثبت Webhook در Meta
1. برو به https://developers.facebook.com/apps
2. انتخاب App → WhatsApp → Configuration
3. Webhook → Edit:
   ```
   Callback URL: https://realty.artinsmartagent.com/webhook/whatsapp
   Verify Token: [از output اسکریپت]
   ```
4. Verify and Save
5. Subscribe to webhook fields:
   - ✅ messages
   - ✅ message_status

## مرحله 6: Test
```bash
# ارسال پیام تست به WhatsApp Business number
# مثال: +971 50 123 4567

# بررسی logs
docker compose logs -f backend | grep -i whatsapp
```

انتظار:
```
INFO - WhatsApp webhook verified
INFO - Message sent to +971501234567
```

---

## 🔍 Troubleshooting

### ❌ Webhook Verification Failed
**علت:** Verify token در database ≠ verify token در Meta

**حل:**
```bash
# چک کردن verify token در database
docker compose exec db psql -U artinrealty -d artinrealty_db \
  -c "SELECT email, whatsapp_verify_token FROM tenants WHERE whatsapp_phone_number_id IS NOT NULL;"

# اگر NULL بود، set کن:
UPDATE tenants SET whatsapp_verify_token = 'your-token' WHERE id = 1;
```

### ❌ No Response from Bot
**بررسی:**
1. Phone Number ID صحیح است؟
2. Access Token valid است؟
3. Webhook subscribed است؟

```bash
# تست webhook با curl
curl -X POST "https://realty.artinsmartagent.com/webhook/whatsapp" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "metadata": {"phone_number_id": "YOUR_PHONE_NUMBER_ID"},
          "messages": [{
            "from": "971501234567",
            "type": "text",
            "text": {"body": "test"}
          }]
        }
      }]
    }]
  }'

# Check logs
docker compose logs backend | tail -20
```

### ❌ Access Token Expired
Access tokens در Meta expire می‌شوند.

**حل:**
1. برو به Meta Business Settings
2. System Users → Create Permanent Token
3. Copy new token
4. Update در database یا dashboard

---

## 🎯 Quick Test Script

```bash
#!/bin/bash

# Test 1: Webhook verification
echo "🧪 Testing webhook verification..."
curl "https://realty.artinsmartagent.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=YOUR_VERIFY_TOKEN&hub.challenge=test123"

# Expected: test123

# Test 2: Send message via API
echo "📤 Sending test message..."
curl -X POST "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "971501234567",
    "type": "text",
    "text": {
      "body": "Hello from ArtinSmartRealty! 🏠"
    }
  }'

# Test 3: Check webhook registration
echo "🔍 Checking webhook..."
curl "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID?fields=webhooks&access_token=YOUR_ACCESS_TOKEN"
```

---

## 📊 Status Check

بعد از setup:

```bash
# 1. Database check
docker compose exec db psql -U artinrealty -d artinrealty_db \
  -c "SELECT name, whatsapp_phone_number_id IS NOT NULL as whatsapp_configured FROM tenants;"

# 2. Backend health
curl https://realty.artinsmartagent.com/api/health

# 3. Logs
docker compose logs backend | grep -i "whatsapp" | tail -10
```

---

## ✅ Success Checklist

- [ ] Phone Number ID در database ذخیره شد
- [ ] Access Token valid است
- [ ] Verify Token match می‌کند
- [ ] Webhook verified شد (green checkmark در Meta)
- [ ] Webhook fields subscribed: messages ✅
- [ ] Test message فرستادی → دریافت پاسخ ✅
- [ ] Image/Voice/Location کار می‌کنند ✅

---

**همه چیز درست کار کرد؟ WhatsApp bot آماده است! 🎉**

نکته: برای production، حتماً از Permanent Access Token استفاده کن، نه Test Token!
