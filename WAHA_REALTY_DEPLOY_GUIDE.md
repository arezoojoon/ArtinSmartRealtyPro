# 🚀 راهنمای سریع Deploy کردن Waha برای Realty

## ✅ چیزهایی که آماده شده:

1. **Waha Container**: پورت 3002 (جدا از Expo که روی 3001 هست)
2. **Backend Webhook**: `/api/webhook/waha` آماده دریافت پیام‌ها
3. **Waha Provider**: کد پشتیبانی کامل در `backend/whatsapp_providers.py`
4. **Deep Link Routing**: مثل Expo، بدون نیاز به Router جداگانه

---

## 📋 مراحل Deploy روی سرور (72.60.196.192)

### مرحله 1: وصول به سرور
```bash
ssh root@72.60.196.192
cd /opt/ArtinSmartRealty
```

### مرحله 2: اجرای اسکریپت Deploy
```bash
# دسترسی اجرایی به اسکریپت
chmod +x deploy_waha_realty.sh

# اجرا
./deploy_waha_realty.sh
```

این اسکریپت این کارها رو انجام می‌ده:
- ✅ Pull کردن آخرین کد از GitHub
- ✅ Build کردن Waha container با پورت 3002
- ✅ استخراج API Key از logs
- ✅ ذخیره API Key در `.env`
- ✅ Restart کردن backend
- ✅ ساخت session با webhook config
- ✅ نمایش لینک QR Code

---

## 📱 مرحله 3: Scan کردن QR Code

بعد از اجرای اسکریپت، یه لینک مثل این می‌بینی:

```
http://72.60.196.192:3002/api/sessions/default/auth/qr?api_key=XXXXXXXX
```

**توی مرورگر باز کن و QR Code رو Scan کن:**
1. WhatsApp باز کن
2. Settings → Linked Devices
3. Link a Device
4. QR Code رو Scan کن

---

## 🔍 چک کردن وضعیت

### گزینه 1: اسکریپت Status Check
```bash
chmod +x waha_check_realty.sh
./waha_check_realty.sh
```

### گزینه 2: دستی با curl
```bash
# API Key رو از .env بگیر
API_KEY=$(grep "WAHA_API_KEY=" .env | cut -d'=' -f2)

# وضعیت session
curl -H "X-Api-Key: $API_KEY" http://localhost:3002/api/sessions/default | jq
```

انتظار می‌ری ببینی:
```json
{
  "status": "WORKING",
  "me": {
    "id": "971XXXXXXXXX@c.us"
  }
}
```

---

## 🔧 تست Deep Links

وقتی status شد **WORKING**:

```bash
# شماره تلفن متصل رو بگیر
PHONE=$(curl -s -H "X-Api-Key: $API_KEY" http://localhost:3002/api/sessions/default | jq -r '.me.id' | sed 's/@c.us//')

echo "Test this link: https://wa.me/$PHONE?text=start_realty"
```

این لینک رو توی واتساپ باز کن، باید بات شروع به کار کنه!

---

## 📊 Monitoring

### لاگ‌های Waha:
```bash
docker-compose logs -f waha
```

### لاگ‌های Backend:
```bash
docker-compose logs -f backend | grep -i waha
```

### Redis Session Check:
```bash
docker-compose exec redis redis-cli
> KEYS user:*:mode
> GET user:971XXXXXXXXX:mode
```

---

## 🆘 عیب‌یابی

### اگر QR Code نمی‌بینی:
```bash
docker-compose logs waha --tail=50 | grep '█'
```

### اگر webhook کار نمی‌کنه:
```bash
# چک کن که backend در شبکه Docker هست
docker-compose ps backend

# چک کن webhook config
curl -H "X-Api-Key: $API_KEY" http://localhost:3002/api/sessions/default | jq '.config.webhooks'
```

باید ببینی:
```json
[{
  "url": "http://backend:8000/api/webhook/waha",
  "events": ["message.any"]
}]
```

### Restart کردن Session:
```bash
API_KEY=$(grep "WAHA_API_KEY=" .env | cut -d'=' -f2)

# Stop
curl -X POST -H "X-Api-Key: $API_KEY" http://localhost:3002/api/sessions/default/stop

# Start
curl -X POST -H "X-Api-Key: $API_KEY" http://localhost:3002/api/sessions/default/start
```

---

## 🎯 تفاوت‌های Expo vs Realty

| ویژگی | Expo Server | Realty Server |
|-------|-------------|---------------|
| Waha Port | 3001 | 3002 |
| WhatsApp Phone | 971505037158 | شماره جدید (باید Scan کنی) |
| Router Service | ✅ دارد (port 5000) | ❌ ندارد (مستقیم به backend) |
| Webhook URL | `http://router:5000/webhook` | `http://backend:8000/api/webhook/waha` |
| Backend Port | 8000 | 8000 (همون) |

**معماری Realty ساده‌تر است:**
```
WhatsApp → Waha (3002) → Backend (8000) → Brain.py
```

**معماری Expo پیچیده‌تر:**
```
WhatsApp → Waha (3001) → Router (5000) → Backend (8000) → Brain.py
```

---

## ✅ Checklist نهایی

- [ ] اسکریپت `deploy_waha_realty.sh` اجرا شد
- [ ] API Key در `.env` ذخیره شد
- [ ] QR Code اسکن شد
- [ ] Status شد `WORKING`
- [ ] Webhook config درست هست
- [ ] Deep link تست شد و جواب داد

---

## 📞 نمونه‌های Deep Link

بعد از متصل شدن واتساپ، این لینک‌ها رو تست کن:

```
https://wa.me/PHONE_NUMBER?text=start_realty
https://wa.me/PHONE_NUMBER?text=املاک
```

(PHONE_NUMBER رو با شماره واقعی جایگزین کن)

---

**توسعه‌دهنده:** این فقط برای Realty هست. برای Travel و Clinic همین روند رو تکرار می‌کنیم با پورت‌های 3003 و 3004 👍
