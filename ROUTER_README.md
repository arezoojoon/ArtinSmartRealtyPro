# 🚀 ArtinSmartAgent Standalone Router

Router مستقل برای مسیریابی پیام‌های WhatsApp به سرویس‌های مختلف (Realty, Travel, Expo, Clinic)

## ✨ ویژگی‌ها

- ✅ **حافظه دائمی**: اگر سرور restart شود، روت‌های کاربران از بین نمی‌رود
- ✅ **پشتیبانی از 1000+ ایجنت**: هر ایجنت می‌تواند لینک اختصاصی داشته باشد
- ✅ **فیلتر پیام‌های شخصی**: فقط پیام‌های business را پردازش می‌کند
- ✅ **Multi-Vertical**: چند سرویس مختلف در یک router
- ✅ **Health Check & Stats**: مانیتورینگ آماده

## 📋 پیش‌نیازها

- Python 3.11+
- Docker (اختیاری)

## 🏃 راه‌اندازی سریع

### روش 1: اجرای مستقیم با Python

```bash
cd backend
pip install -r router_requirements.txt
python standalone_router.py
```

Router روی `http://localhost:5000` اجرا می‌شود.

### روش 2: اجرا با Docker

```bash
# Build
docker build -f backend/Dockerfile.router -t artinrouter .

# Run
docker run -d \\
  -p 5000:5000 \\
  -v $(pwd)/router_data:/app/data \\
  --name artinrouter \\
  artinrouter
```

### روش 3: Docker Compose (توصیه می‌شود)

```bash
docker-compose -f docker-compose.router.yml up -d
```

## ⚙️ تنظیمات

### متغیرهای محیطی

```bash
# پورت router
ROUTER_PORT=5000
ROUTER_HOST=0.0.0.0

# مسیر فایل حافظه
ROUTES_DB_FILE=/app/data/user_routes.json

# آدرس‌های سرویس‌ها
REALTY_WEBHOOK=https://realty.artinsmartagent.com/api/webhook/waha
TRAVEL_WEBHOOK=https://travel.artinsmartagent.com/api/webhook/waha
EXPO_WEBHOOK=https://expo.artinsmartagent.com/api/webhook/waha
CLINIC_WEBHOOK=https://clinic.artinsmartagent.com/api/webhook/waha
```

### تنظیم WAHA

در پنل WAHA، webhook را روی آدرس router تنظیم کنید:

```
http://YOUR_SERVER_IP:5000/webhook
```

## 🔗 Deep Links

### ساختار لینک

```
wa.me/97150XXXXXXX?text=start_{SERVICE}_{AGENT_ID}
```

### مثال‌ها

**Real Estate:**
```
wa.me/971501234567?text=start_realty_agent101
wa.me/971501234567?text=start_realty_john
wa.me/971501234567?text=start_realty_downtown_team
```

**Travel:**
```
wa.me/971501234567?text=start_travel_agent5
wa.me/971501234567?text=start_travel_visa_specialist
```

**Expo:**
```
wa.me/971501234567?text=start_expo_booth12
```

**Clinic:**
```
wa.me/971501234567?text=start_clinic_dr_ali
```

## 📊 API Endpoints

### Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-14T23:00:00",
  "services": ["realty", "travel", "expo", "clinic"],
  "total_users": 156
}
```

### آمار استفاده
```bash
GET /stats
```

**Response:**
```json
{
  "total_users": 156,
  "by_service": {
    "realty": 98,
    "travel": 42,
    "expo": 12,
    "clinic": 4
  },
  "by_agent": {
    "realty_agent101": 25,
    "realty_john": 18,
    "travel_visa_specialist": 15
  },
  "recent_users": [...]
}
```

### لیست روت‌ها
```bash
GET /routes
```

**Response:**
```json
{
  "total": 156,
  "routes": {
    "***4567": {
      "service": "realty",
      "agent_id": "agent101",
      "timestamp": "2025-12-14T22:30:00"
    }
  }
}
```

## 🔄 نحوه کار Router

### فلوی پردازش پیام

```
WhatsApp User
      ↓
   WAHA Server
      ↓
Standalone Router (Port 5000)
      ↓
  ┌──────────────────┐
  │ Deep Link Check  │ → start_realty_* detected?
  └──────────────────┘
      ↓ No
  ┌──────────────────┐
  │ Memory Check     │ → User has saved route?
  └──────────────────┘
      ↓ No
  ┌──────────────────┐
  │ Filter Personal  │ → IGNORE (not a business message)
  └──────────────────┘
```

### مثال واقعی

**سناریو 1: کاربر جدید**
```
1. User clicks: wa.me/971501234567?text=start_realty_agent101
2. Router receives: {"body": "start_realty_agent101", "from": "971509876543@c.us"}
3. Router detects: service=realty, agent_id=agent101
4. Router saves: {"971509876543": {"service": "realty", "agent_id": "agent101"}}
5. Router forwards → https://realty.artinsmartagent.com/api/webhook/waha
6. Response: {"status": "new_assignment", "service": "realty"}
```

**سناریو 2: کاربر قبلی**
```
1. User sends: "سلام، ملک جدید داری؟"
2. Router checks memory: 971509876543 → realty/agent101
3. Router forwards → https://realty.artinsmartagent.com/api/webhook/waha
4. Response: {"status": "forwarded", "service": "realty"}
```

**سناریو 3: پیام شخصی**
```
1. Unknown number sends: "سلام مادر جان"
2. Router checks: No deep link + No saved route
3. Router IGNORES (doesn't forward anywhere)
4. Response: {"status": "ignored_personal"}
```

## 🛠️ مانیتورینگ و Debugging

### مشاهده لاگ‌ها (Docker)

```bash
docker-compose -f docker-compose.router.yml logs -f
```

### مشاهده فایل Routes

```bash
cat router_data/user_routes.json
```

### تست دستی

```bash
# ارسال پیام تست
curl -X POST http://localhost:5000/webhook \\
  -H "Content-Type: application/json" \\
  -d '{
    "payload": {
      "from": "971501234567@c.us",
      "body": "start_realty_test"
    }
  }'
```

## 🔐 امنیت

### فیلترینگ خودکار

- ✅ پیام‌های گروهی نادیده گرفته می‌شوند
- ✅ Status updates فیلتر می‌شوند
- ✅ پیام‌های بدون روت assignment نادیده گرفته می‌شوند

### حفاظت از داده

- فایل `user_routes.json` شماره‌های کامل را ذخیره می‌کند
- API endpoint `/routes` فقط 4 رقم آخر را نمایش می‌دهد
- لاگ‌ها شماره‌های کامل را نشان می‌دهند (فقط برای مدیر)

## 📈 عملکرد

- **پردازش**: ~100 پیام در ثانیه
- **حافظه**: ~50MB RAM
- **CPU**: <5% در حالت عادی
- **Latency**: <50ms routing time

## 🚨 عیب‌یابی

### مشکل: Router پیام را نمی‌فرستد

```bash
# چک کردن health
curl http://localhost:5000/health

# چک کردن logs
docker-compose -f docker-compose.router.yml logs --tail 100

# تست manual forwarding
curl -X POST https://realty.artinsmartagent.com/api/webhook/waha \\
  -H "Content-Type: application/json" \\
  -d '{"test": "manual"}'
```

### مشکل: حافظه کار نمی‌کند

```bash
# چک کردن فایل JSON
cat router_data/user_routes.json

# حذف و ایجاد مجدد
rm router_data/user_routes.json
docker-compose -f docker-compose.router.yml restart
```

### مشکل: WAHA به router وصل نیست

```bash
# تست از خارج سرور
curl -X POST http://YOUR_SERVER_IP:5000/webhook \\
  -H "Content-Type: application/json" \\
  -d '{"payload": {"from": "test@c.us", "body": "test"}}'

# چک کردن firewall
sudo ufw status
sudo ufw allow 5000
```

## 📞 پشتیبانی

- Website: https://artinsmartagent.com
- Email: info@artinsmartagent.com
- Documentation: این فایل README

## 📝 License

© 2025 ArtinSmartAgent - All Rights Reserved
