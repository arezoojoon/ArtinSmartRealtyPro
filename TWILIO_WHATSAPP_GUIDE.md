# 🚀 Twilio WhatsApp - راهنمای سریع Setup

## چرا Twilio؟
- ✅ Setup خیلی سریع (5 دقیقه!)
- ✅ Sandbox برای تست رایگان
- ✅ بدون نیاز به تایید Meta
- ✅ Documentation عالی

---

## مرحله 1: Twilio Account

1. برو به https://www.twilio.com/console
2. Sign Up (رایگان)
3. Console → Messaging → Try WhatsApp

---

## مرحله 2: دریافت Credentials

از Twilio Console کپی کنید:

```
Account SID: AC1234567890abcdef...
Auth Token: your_auth_token_here
WhatsApp Sandbox Number: whatsapp:+14155238886
```

---

## مرحله 3: افزودن به .env (VPS)

```bash
ssh root@srv1151343
nano /opt/ArtinSmartRealty/.env
```

اضافه کنید:

```bash
# Twilio WhatsApp (auto-detected، priority over Meta)
TWILIO_ACCOUNT_SID=AC1234567890abcdef...
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

Save و exit (Ctrl+X, Y, Enter)

---

## مرحله 4: Restart Backend

```bash
cd /opt/ArtinSmartRealty
docker-compose restart backend
docker-compose logs backend | grep "Twilio"
```

**باید ببینید:**
```
INFO - Using Twilio WhatsApp provider for tenant 1
```

---

## مرحله 5: Join Sandbox

روی گوشی خودتون:

1. Save کنید: `+1 (415) 523-8886`
2. WhatsApp باز کنید
3. پیام بفرستید: `join <your-sandbox-code>`

کد sandbox از Twilio Console → Messaging → Try WhatsApp

---

## مرحله 6: تست

بعد از join کردن، پیام بفرستید:

```
سلام
```

Bot باید جواب بده! ✅

---

## 📊 Webhook Configuration

Twilio خودش webhook رو handle می‌کنه در sandbox mode.

برای Production:

1. Twilio Console → Messaging → Settings
2. Webhook URL:
   ```
   https://realty.artinsmartagent.com/webhook/whatsapp
   ```
3. Method: POST
4. Save

---

## 🔄 تفاوت با Meta

| Feature | Twilio | Meta |
|---------|--------|------|
| Setup Time | 5 دقیقه | 2-7 روز |
| Approval | ندارد | دارد |
| Interactive Buttons | ❌ (text only) | ✅ |
| Cost | از پیام 1 | 1000 رایگان |
| Sandbox | ✅ | ❌ |

**نکته:** Twilio دکمه‌های interactive نداره، بات بجاش دکمه‌ها رو به صورت numbered list می‌فرسته:

```
1. سرمایه‌گذاری
2. زندگی
3. اقامت
```

---

## 🐛 Troubleshooting

### ❌ "No WhatsApp provider configured"

**چک کنید:**
```bash
docker-compose exec backend python -c "
import os
print('TWILIO_ACCOUNT_SID:', os.getenv('TWILIO_ACCOUNT_SID')[:10] if os.getenv('TWILIO_ACCOUNT_SID') else 'NOT SET')
print('TWILIO_AUTH_TOKEN:', 'SET' if os.getenv('TWILIO_AUTH_TOKEN') else 'NOT SET')
"
```

اگه NOT SET بود، .env رو چک کنید و restart کنید.

---

### ❌ "Failed to send message"

**چک کنید:**
1. Sandbox join کردید؟
2. Auth Token درسته؟
3. Phone number فرمت `whatsapp:+1415...` داره؟

**لاگ ببینید:**
```bash
docker-compose logs backend | grep -i twilio
```

---

## 💰 قیمت‌گذاری Twilio

- **Sandbox:** رایگان برای تست
- **Production:**
  - Conversation-based pricing
  - ~$0.005 per message
  - Free trial: $15 credit

**مقایسه:**
- 1000 پیام/ماه: ~$5 (Twilio) vs رایگان (Meta)
- 10,000 پیام/ماه: ~$50 (Twilio) vs ~$20 (Meta)

---

## ✅ خلاصه

**برای تست سریع:** Twilio Sandbox (همین الان!)
**برای Production:** Meta WhatsApp Cloud API (بعد از تایید)

**Auto-switching:** کد خودش تشخیص می‌ده کدوم credentials داری و از همون استفاده می‌کنه! 🎯
