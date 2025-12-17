# 🚀 راهنمای Deploy سیستم Multi-Tenant WhatsApp Gateway

## ✅ چک‌لیست قبل از شروع

فایل‌های زیر باید وجود داشته باشند:

```
backend/
├── whatsapp_router_simple.py   ✅ (فایل جدید ساخته شد)
├── main.py                      ⏳ (نیاز به آپدیت - مرحله ۳)
└── requirements.txt             ✅

docker-compose.yml              ✅ (سرویس router وجود دارد)
```

---

## 🔧 مرحله ۱: آپدیت Backend - اضافه کردن X-Tenant-ID

**به این فایل بروید:**
```
i:\ArtinRealtySmartPro\ArtinSmartRealty\backend\main.py
```

**پیدا کنید:**
```python
@app.post("/api/webhook/whatsapp")
async def whatsapp_webhook_handler(request: Request):
```

**تغییر دهید به:**
```python
from fastapi import Header

@app.post("/api/webhook/whatsapp")
async def whatsapp_webhook_handler(
    request: Request,
    x_tenant_id: str = Header(None, alias="X-Tenant-ID")
):
    """Webhook handler با پشتیبانی از Router"""
    try:
        body = await request.json()
        payload = body.get("payload", {})
        from_number = payload.get("from", "").replace("@c.us", "")
        
        # ⭐ اگر از Router آمده، tenant_id مشخص است
        if x_tenant_id:
            logger.info(f"📩 Routed message for Tenant {x_tenant_id}")
            tenant_id = int(x_tenant_id)
        else:
            # Fallback: پیدا کردن tenant از whatsapp_phone_number_id
            logger.warning("Direct message - not routed")
            async with async_session() as session:
                tenant_result = await session.execute(
                    select(Tenant).where(
                        Tenant.whatsapp_phone_number_id == from_number
                    )
                )
                tenant = tenant_result.scalar_one_or_none()
                if not tenant:
                    return {"status": "error", "reason": "tenant_not_found"}
                tenant_id = tenant.id
        
        # دریافت tenant از database
        async with async_session() as session:
            tenant = await session.get(Tenant, tenant_id)
            if not tenant:
                return {"status": "error"}
            
            # پیدا/ساخت Lead
            lead_result = await session.execute(
                select(Lead).where(
                    Lead.tenant_id == tenant_id,
                    Lead.whatsapp_phone == from_number
                )
            )
            lead = lead_result.scalar_one_or_none()
            
            if not lead:
                lead = Lead(
                    tenant_id=tenant_id,
                    whatsapp_phone=from_number,
                    language=Language.FA,
                    status=LeadStatus.NEW
                )
                session.add(lead)
                await session.commit()
            
            # ادامه لاجیک brain.py...
            # (کد قبلی شما بدون تغییر)
            
        return {"status": "success"}
    except Exception as e:
        logger.exception(f"Webhook error: {e}")
        return {"status": "error"}
```

---

## 🚀 مرحله ۲: Deploy روی Production Server

```bash
# اتصال به سرور
ssh root@srv1195426

# رفتن به دایرکتوری پروژه
cd /opt/ArtinSmartRealtyPro/ArtinSmartRealty

# Pull کردن آخرین تغییرات
git pull

# Build کردن Router و Backend
docker-compose build --no-cache router backend

# Start کردن سرویس‌ها
docker-compose up -d

# چک کردن status
docker-compose ps
```

**خروجی مورد انتظار:**
```
NAME                  STATUS        PORTS
artinrealty-backend   healthy       0.0.0.0:8000->8000/tcp
artinrealty-router    running       0.0.0.0:8001->8001/tcp
artinrealty-waha      running       0.0.0.0:3001->3000/tcp
```

---

## 🔗 مرحله ۳: اتصال WAHA به Router

**دستور زیر را روی سرور اجرا کنید:**

```bash
curl -X POST \
  -H "X-Api-Key: waha_artinsmartrealty_secure_key_2024" \
  -H "Content-Type: application/json" \
  -d '{"webhooks":[{"url":"http://router:8001/webhook/waha","events":["message"]}]}' \
  http://localhost:3001/api/sessions/default
```

**چک کردن تنظیمات:**
```bash
curl -H "X-Api-Key: waha_artinsmartrealty_secure_key_2024" \
  http://localhost:3001/api/sessions/default
```

**باید `webhooks` را ببینید:**
```json
{
  "webhooks": [
    {
      "url": "http://router:8001/webhook/waha",
      "events": ["message"]
    }
  ]
}
```

---

## 🧪 مرحله ۴: تست سیستم

### تست ۱: سلامتی Router

```bash
curl http://localhost:8001/health
```

**خروجی:**
```json
{
  "status": "healthy",
  "total_locked_users": 0
}
```

### تست ۲: Deep Link (Tenant 2 - سامان احمدی)

**لینک تست:**
```
https://wa.me/971557357753?text=start_realty_2
```

**مراحل:**
1. لینک را در مرورگر باز کنید
2. WhatsApp باز می‌شود
3. پیام `start_realty_2` را ارسال کنید

**چک لاگ Router:**
```bash
docker logs artinrealty-router | grep "LOCKED"
```

**باید ببینید:**
```
🔒 User 971XXXXXXXXX LOCKED to Tenant 2
```

**چک لاگ Backend:**
```bash
docker logs artinrealty-backend | grep "Routed"
```

**باید ببینید:**
```
📩 Routed message for Tenant 2
```

### تست ۳: پیام معمولی

بعد از Lock شدن، پیام عادی بفرستید:
```
سلام، می‌خوام ملک ببینم
```

**Router باید:**
- شماره را lookup کند
- Tenant 2 را پیدا کند
- پیام را forward کند

---

## 📊 مانیتورینگ

### آمار Router

```bash
curl http://localhost:8001/router/stats
```

**نمونه خروجی:**
```json
{
  "total_users": 2,
  "mappings": {
    "971501234567": "2",
    "971502345678": "5"
  }
}
```

### فایل Mappings

```bash
docker exec artinrealty-router cat user_tenant_map.json
```

---

## 🐛 عیب‌یابی

### Router Start نمی‌شود

```bash
docker logs artinrealty-router --tail 50
```

### پیام‌ها Route نمی‌شوند

```bash
# چک کنید WAHA به Router وصل است
curl -H "X-Api-Key: waha_artinsmartrealty_secure_key_2024" \
  http://localhost:3001/api/sessions/default | grep webhook
```

### Lock نمی‌شود

```bash
# الگوی صحیح Deep Link
"start_realty_2"   # ✅
"START_REALTY_2"   # ✅
"startrealty2"     # ❌ (بدون _)
"start_realty_abc" # ❌ (باید عدد باشد)
```

---

## ✅ نتیجه نهایی

✅ یک شماره WhatsApp برای ۱۰۰۰+ Tenant  
✅ Router هوشمند برای هدایت پیام‌ها  
✅ Deep Links برای Lock کردن کاربران  
✅ مقیاس‌پذیری کامل

**لینک تست نهایی:**
```
https://wa.me/971557357753?text=start_realty_2
```

🎉 **سیستم آماده است!**
