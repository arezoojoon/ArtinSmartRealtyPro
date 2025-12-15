# 🟢 راهنمای راه‌اندازی WhatsApp (WAHA)

**تاریخ**: 15 دسامبر 2025  
**وضعیت**: ✅ WAHA راه‌اندازی شد - آماده اسکن QR Code

---

## 🔧 تغییرات انجام شده

### 1. اضافه کردن API Key به `.env`
```dotenv
WAHA_API_KEY=waha_artinsmartrealty_secure_key_2024
```

### 2. تنظیم docker-compose.yml
```yaml
waha:
  environment:
    - WAHA_API_KEY=${WAHA_API_KEY:-waha_artinsmartrealty_secure_key_2024}
    # Health check disabled - WAHA CORE doesn't support API auth in /health
```

### 3. شروع Session WhatsApp
```bash
# Session created and started successfully!
Status: SCAN_QR_CODE (waiting for phone scan)
```

---

## 📱 مراحل اتصال WhatsApp

### روش 1: از طریق Dashboard (ساده‌تر)

1. **باز کردن WAHA Dashboard:**
   ```
   http://localhost:3001
   ```

2. **ورود با credentials:**
   ```
   Username: admin
   Password: 45a6df4393af42f5a8a02314bf508d7c
   ```
   
   **⚠️ نکته مهم:** Password در هر بار restart تغییر می‌کند!  
   برای دریافت password جدید از logs استفاده کنید:
   ```bash
   docker logs artinrealty-waha 2>&1 | grep "WAHA_DASHBOARD_PASSWORD" | tail -1
   ```

3. **اسکن QR Code:**
   - به قسمت Sessions بروید
   - Session "default" را انتخاب کنید
   - QR Code را با WhatsApp موبایل اسکن کنید
   - WhatsApp > Settings > Linked Devices > Link a Device

### روش 2: از طریق API (پیشرفته)

```powershell
# 1. دریافت QR Code
$response = Invoke-WebRequest -Uri "http://localhost:3001/api/default/auth/qr" -Headers @{"X-Api-Key"="waha_artinsmartrealty_secure_key_2024"}
$qr = ($response.Content | ConvertFrom-Json)
Write-Host $qr.value

# 2. نمایش QR در Swagger UI
# باز کنید: http://localhost:3001/api  (API docs - بدون password!)
# یا Dashboard: http://localhost:3001
# Username: admin
# Password: (از logs دریافت کنید - هر بار تغییر می‌کند)

# 3. اسکن QR با موبایل
# WhatsApp > تنظیمات > دستگاه‌های متصل > افزودن دستگاه
```

---

## ✅ تایید اتصال موفق

### چک کردن وضعیت Session

```powershell
$response = Invoke-WebRequest -Uri "http://localhost:3001/api/sessions/default" -Headers @{"X-Api-Key"="waha_artinsmartrealty_secure_key_2024"}
($response.Content | ConvertFrom-Json) | Select-Object status,me
```

**خروجی موفق:**
```
status : WORKING
me     : @c.us {
           "id": "971501234567@c.us",
           "pushName": "نام شما"
         }
```

---

## 🧪 تست ارسال پیام

### ارسال تست به خودتان

```powershell
$body = @{
    chatId = "971501234567@c.us"  # شماره خودتان
    text = "🤖 سلام! من ربات ArtinSmartRealty هستم - تست موفق!"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:3001/api/default/sendText" `
    -Method POST `
    -Headers @{
        "X-Api-Key"="waha_artinsmartrealty_secure_key_2024"
        "Content-Type"="application/json"
    } `
    -Body $body
```

---

## 🔗 اتصال به Backend

### تنظیمات Tenant

در database، tenant باید `whatsapp_phone_number_id` داشته باشد:

```sql
-- چک کردن تنظیمات فعلی
SELECT id, business_name, whatsapp_phone_number_id 
FROM tenants 
WHERE id = 2;

-- اگر null بود، آپدیت کنید:
UPDATE tenants 
SET whatsapp_phone_number_id = '971501234567'  -- شماره متصل به WAHA
WHERE id = 2;
```

### تست Webhook

```powershell
# ارسال پیام تست به webhook
$testMessage = @{
    payload = @{
        from = "971509876543@c.us"
        body = "/start"
        timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    }
} | ConvertTo-Json -Depth 5

Invoke-WebRequest -Uri "http://localhost:8000/api/webhook/waha" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $testMessage
```

---

## 🐛 عیب‌یابی

### مشکل: QR Code منقضی شد

```powershell
# Restart session
Invoke-WebRequest -Uri "http://localhost:3001/api/sessions/default/stop" `
    -Method POST `
    -Headers @{"X-Api-Key"="waha_artinsmartrealty_secure_key_2024"}

Start-Sleep -Seconds 3

Invoke-WebRequest -Uri "http://localhost:3001/api/sessions/default/start" `
    -Method POST `
    -Headers @{"X-Api-Key"="waha_artinsmartrealty_secure_key_2024"}
```

### مشکل: Session Failed

```powershell
# پاک کردن session data و شروع مجدد
docker-compose stop waha
docker volume rm artinsmartrealty_waha_sessions
docker volume rm artinsmartrealty_waha_cache
docker-compose up -d waha

# سپس session را مجدد start کنید
```

### مشکل: پیام‌ها دریافت نمی‌شوند

```powershell
# چک کردن webhook configuration
$response = Invoke-WebRequest -Uri "http://localhost:3001/api/sessions/default" `
    -Headers @{"X-Api-Key"="waha_artinsmartrealty_secure_key_2024"}
($response.Content | ConvertFrom-Json).config
```

---

## 📊 مانیتورینگ

### چک کردن Logs

```powershell
# لاگ‌های لحظه‌ای WAHA
docker logs artinrealty-waha -f --tail 50

# جستجوی پیام‌های دریافتی
docker logs artinrealty-waha | Select-String "message.any"

# جستجوی خطاها
docker logs artinrealty-waha | Select-String "ERROR"
```

### وضعیت Health

```powershell
# Session status
Invoke-WebRequest -Uri "http://localhost:3001/api/sessions/default" `
    -Headers @{"X-Api-Key"="waha_artinsmartrealty_secure_key_2024"} | 
    Select-Object StatusCode

# Container status
docker ps | Select-String "waha"
```

---

## 🔐 امنیت

### API Key Management

**⚠️ هرگز API key را commit نکنید!**

```bash
# .gitignore باید شامل:
.env
*.env
```

### Credentials Dashboard

**به صورت auto-generate در هر start:**
```
WAHA_DASHBOARD_USERNAME=admin
WAHA_DASHBOARD_PASSWORD=<random-hash>
```

این credentials را از لاگ کپی کنید و در جای امنی ذخیره کنید.

---

## 🚀 Integration با Backend

### whatsapp_bot.py

Backend شما از **`whatsapp_providers.py`** استفاده می‌کند:

```python
# در whatsapp_providers.py
WAHA_API_URL = "http://waha:3000/api"
WAHA_API_KEY = os.getenv("WAHA_API_KEY")

# Headers برای تمام requests
headers = {
    "X-Api-Key": WAHA_API_KEY,
    "Content-Type": "application/json"
}
```

### ارسال پیام از Bot

```python
from whatsapp_providers import send_waha_message

# Text message
await send_waha_message(
    phone="971501234567",
    message="سلام! این پیام از ربات است."
)

# Image با caption
await send_waha_image(
    phone="971501234567",
    image_url="https://example.com/property.jpg",
    caption="🏢 آپارتمان لوکس دبی مارینا"
)

# PDF
await send_waha_document(
    phone="971501234567",
    document_url="https://example.com/roi_report.pdf",
    filename="ROI_Analysis.pdf"
)
```

---

## 📋 Checklist راه‌اندازی

- [x] WAHA container راه‌اندازی شد
- [x] API Key تنظیم شد
- [x] Session "default" ایجاد شد
- [x] Session شروع شد (status: SCAN_QR_CODE)
- [x] QR Code اسکن شد با موبایل ✅
- [x] Session به WORKING تغییر کرد ✅ (971557357753@c.us)
- [ ] شماره تنانت در database ثبت شود
- [ ] تست ارسال پیام انجام شود
- [ ] تست دریافت پیام از ربات

---

## 🆘 دستورات سریع

```powershell
# مشاهده وضعیت
docker-compose ps waha

# Restart WAHA
docker-compose restart waha

# مشاهده logs
docker logs artinrealty-waha -f

# دریافت QR (باید در browser باز شود)
Start-Process "http://localhost:3001"

# تست اتصال
curl http://localhost:3001/api/sessions -H "X-Api-Key: waha_artinsmartrealty_secure_key_2024"
```

---

## ✨ Next Steps

1. **اسکن QR Code**  
   باز کنید: `http://localhost:3001` → Login → اسکن QR

2. **ثبت شماره در Tenant**  
   ```sql
   UPDATE tenants SET whatsapp_phone_number_id = '971XXXXXXXXX' WHERE id = 2;
   ```

3. **تست End-to-End**  
   پیام بفرستید به شماره WhatsApp → باید ربات پاسخ دهد

4. **Deploy Router** (اختیاری)  
   اگر می‌خواهید multi-vertical routing داشته باشید

---
**🎉 WAHA آماده است - فقط QR Code اسکن کنید!**

### روش ساده: Dashboard
باز کنید: http://72.62.91.26:3001  
Login: admin / 45a6df4393af42f5a8a02314bf508d7c

### روش بدون Password: API Docs
باز کنید: http://72.62.91.26:3001/api  
(نیاز به login ندارد - مستقیم QR Code می‌بینید)

### دانلود QR به Desktop
**⚠️ این دستور را روی کامپیوتر خودتان (Windows) اجرا کنید - نه روی سرور!**

از **Windows PowerShell محلی** اجرا کنید:
```powershell
scp root@72.62.91.26:/tmp/qr.png $env:USERPROFILE\Desktop\whatsapp_qr.png
Start-Process "$env:USERPROFILE\Desktop\whatsapp_qr.png"
```

**یا اگر دسترسی SSH ندارید:**
```powershell
# دانلود مستقیم QR از API
Invoke-WebRequest -Uri "http://72.62.91.26:3001/api/default/auth/qr" `
    -Headers @{"X-Api-Key"="waha_artinsmartrealty_secure_key_2024"} `
    -OutFile "$env:USERPROFILE\Desktop\whatsapp_qr.png"
Start-Process "$env:USERPROFILE\Desktop\whatsapp_qr.png"
```
