# 🔧 راهنمای اتصال Webhook واتساپ
# WhatsApp Webhook Setup Guide - URGENT FIX

## ✅ مشکل حل شد! Problem Solved!

فایل `.env` ایجاد شد با توکن تأیید صحیح.
The `.env` file has been created with the correct verification token.

---

## 📋 اطلاعات Webhook شما / Your Webhook Details

### 🔗 Callback URL (همان برای Meta و Twilio):
```
https://realty.artinsmartagent.com/webhook/whatsapp
```

### 🔐 Verify Token (فقط برای Meta):
```
Gs/C+v4EDvQkwRii9254B8daNccbDJdy7SGg+TP+yy0ARTIN2024
```

**⚠️ مهم:** این توکن را دقیقاً کپی کنید - هر کاراکتری مهم است!
**Important:** Copy this token EXACTLY - every character matters!

---

## 🚀 مراحل راه‌اندازی / Setup Steps

### گزینه 1️⃣: Meta WhatsApp Cloud API (پیشنهادی برای Production)

1. **وارد Meta Developers شوید:**
   - برو به: https://developers.facebook.com/
   - وارد حساب Business Manager خود شوید

2. **انتخاب اپلیکیشن:**
   - از لیست Apps، اپلیکیشن واتساپ خود را انتخاب کنید
   - از منوی سمت چپ، بخش **WhatsApp > Configuration** را باز کنید

3. **تنظیم Webhook:**
   - در قسمت **Webhook**، روی **Edit** کلیک کنید
   - **Callback URL** را وارد کنید:
     ```
     https://realty.artinsmartagent.com/webhook/whatsapp
     ```
   
   - **Verify Token** را دقیقاً کپی و paste کنید:
     ```
     Gs/C+v4EDvQkwRii9254B8daNccbDJdy7SGg+TP+yy0ARTIN2024
     ```
   
   - روی **Verify and Save** کلیک کنید
   - ✅ باید پیغام "Success" ببینید!

4. **فعال‌سازی Webhook Fields:**
   - در همان صفحه، تیک بزنید روی:
     - ☑️ `messages` (ضروری)
     - ☑️ `message_status` (اختیاری - برای دیدن وضعیت پیام)
   - روی **Save** کلیک کنید

---

### گزینه 2️⃣: Twilio WhatsApp API (سریع‌تر برای تست)

1. **وارد Twilio Console شوید:**
   - برو به: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
   - لاگین کنید

2. **تنظیم Webhook در Sandbox:**
   - قسمت **Sandbox Settings** را باز کنید
   - در قسمت **When a message comes in**:
     ```
     https://realty.artinsmartagent.com/webhook/whatsapp
     ```
   - متد را روی **HTTP POST** بگذارید
   - ذخیره کنید

3. **تست کردن:**
   - شماره Sandbox Twilio را به واتساپ خود اضافه کنید
   - کد Join را ارسال کنید (مثلاً: `join yellow-dog`)
   - سپس یک پیام فارسی بفرستید: `سلام`
   - ✅ ربات باید جواب بدهد!

---

## 🔍 عیب‌یابی / Troubleshooting

### ❌ اگر Meta می‌گوید: "Callback URL couldn't be validated"

**چک کنید:**

1. **آیا سرور در حال اجرا است؟**
   ```bash
   # در VPS اجرا کنید:
   ssh srv1151343
   cd /path/to/ArtinSmartRealty
   docker-compose ps
   ```
   باید ببینید:
   ```
   backend    Up    0.0.0.0:8000->8000/tcp
   ```

2. **آیا .env فایل به Docker منتقل شده؟**
   ```bash
   # کپی .env جدید به سرور:
   git pull origin main
   
   # Rebuild با فایل جدید:
   docker-compose down
   docker-compose up -d --build
   ```

3. **آیا URL در دسترس است؟**
   ```bash
   # از کامپیوتر خودتان تست کنید:
   curl "https://realty.artinsmartagent.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=Gs/C+v4EDvQkwRii9254B8daNccbDJdy7SGg+TP+yy0ARTIN2024&hub.challenge=test123"
   ```
   باید دریافت کنید: `test123`

4. **بررسی لاگ‌های سرور:**
   ```bash
   docker-compose logs backend -f | grep -i webhook
   ```
   باید ببینید:
   ```
   GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token=...
   200 OK
   ```

### ❌ اگر پیغام "Invalid verify token" می‌آید

**راه‌حل:**
- توکن را دوباره از `.env` کپی کنید
- مطمئن شوید space یا enter اضافی نیست
- از یک text editor ساده استفاده کنید (نه Word!)

---

## ✅ تست نهایی / Final Testing

### با Meta:
1. در Meta Developers Console، قسمت **API Setup** را باز کنید
2. شماره تست خود را اضافه کنید (Add Phone Number)
3. از تلفن خود یک پیام به شماره Business بفرستید:
   ```
   سلام، می‌خواهم یک ملک ببینم
   ```
4. ✅ ربات باید در عرض چند ثانیه پاسخ دهد

### با Twilio:
1. شماره Sandbox را به مخاطبین اضافه کنید
2. کد Join را ارسال کنید
3. پیام تست بفرستید:
   ```
   من دنبال خانه در تهران هستم
   ```
4. ✅ ربات باید با سؤالات ملکی جواب دهد

---

## 📞 پشتیبانی / Support

اگر همچنان مشکل دارید:

1. **لاگ‌های کامل را بررسی کنید:**
   ```bash
   docker-compose logs backend --tail=100
   ```

2. **Endpoint را مستقیماً تست کنید:**
   ```bash
   curl -X GET "https://realty.artinsmartagent.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=Gs/C+v4EDvQkwRii9254B8daNccbDJdy7SGg+TP+yy0ARTIN2024&hub.challenge=12345"
   ```

3. **SSL Certificate را بررسی کنید:**
   ```bash
   curl -I https://realty.artinsmartagent.com
   ```
   باید `200 OK` ببینید، نه certificate error.

---

## 🎯 خلاصه سریع / Quick Summary

```
Callback URL:  https://realty.artinsmartagent.com/webhook/whatsapp
Verify Token:  Gs/C+v4EDvQkwRii9254B8daNccbDJdy7SGg+TP+yy0ARTIN2024
Method:        POST
Protocol:      HTTPS (required)
```

**✅ بعد از راه‌اندازی، حتماً سرور را restart کنید:**
```bash
docker-compose restart backend
```

**موفق باشید! 🚀**
