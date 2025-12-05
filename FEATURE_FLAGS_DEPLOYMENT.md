# 🚀 Feature Flags System - Deployment Guide

## مراحل نصب در Production Server

### مرحله 1: دریافت کد جدید

```bash
cd /opt/ArtinSmartRealty
git pull origin main
```

### مرحله 2: اجرای Migration (ایجاد جدول tenant_features)

```bash
# 1. اجرای فایل migration برای دیدن SQL
docker-compose exec backend python migrations/add_tenant_features.py

# 2. اجرای SQL مستقیم در PostgreSQL
docker-compose exec db psql -U postgres -d realty_db << 'EOF'

-- Create enum type for features
DO $$ BEGIN
    CREATE TYPE featureflag AS ENUM (
        'rag_system',
        'voice_ai',
        'advanced_analytics',
        'whatsapp_bot',
        'telegram_bot',
        'broadcast_messages',
        'lottery_system',
        'calendar_booking',
        'lead_export',
        'api_access',
        'custom_branding',
        'multi_language'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create tenant_features table
CREATE TABLE IF NOT EXISTS tenant_features (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    feature featureflag NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    enabled_at TIMESTAMP DEFAULT NOW(),
    enabled_by INTEGER,
    notes VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uix_tenant_feature UNIQUE (tenant_id, feature)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tenant_features_tenant_id ON tenant_features(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_features_enabled ON tenant_features(tenant_id, is_enabled);

-- Auto-enable core features for all existing tenants
INSERT INTO tenant_features (tenant_id, feature, is_enabled, notes)
SELECT t.id, 'telegram_bot'::featureflag, TRUE, 'Auto-enabled for all'
FROM tenants t ON CONFLICT DO NOTHING;

INSERT INTO tenant_features (tenant_id, feature, is_enabled, notes)
SELECT t.id, 'multi_language'::featureflag, TRUE, 'Auto-enabled for all'
FROM tenants t ON CONFLICT DO NOTHING;

INSERT INTO tenant_features (tenant_id, feature, is_enabled, notes)
SELECT t.id, 'calendar_booking'::featureflag, TRUE, 'Auto-enabled for all'
FROM tenants t ON CONFLICT DO NOTHING;

INSERT INTO tenant_features (tenant_id, feature, is_enabled, notes)
SELECT t.id, 'broadcast_messages'::featureflag, TRUE, 'Auto-enabled for all'
FROM tenants t ON CONFLICT DO NOTHING;

INSERT INTO tenant_features (tenant_id, feature, is_enabled, notes)
SELECT t.id, 'rag_system'::featureflag, TRUE, 'New feature - enabled for all'
FROM tenants t ON CONFLICT DO NOTHING;

EOF
```

### مرحله 3: Restart Backend

```bash
docker-compose restart backend
```

### مرحله 4: تست API

```bash
# 1. دریافت لیست همه فیچرها
curl https://realty.artinsmartagent.com/api/admin/features \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# 2. دریافت فیچرهای یک تنانت خاص
curl https://realty.artinsmartagent.com/api/admin/tenants/5/features \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# 3. فعال کردن یک فیچر برای تنانت
curl -X PUT https://realty.artinsmartagent.com/api/admin/tenants/5/features/voice_ai \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "feature": "voice_ai",
    "enabled": true,
    "notes": "Enabled for premium tier"
  }'

# 4. غیرفعال کردن یک فیچر
curl -X PUT https://realty.artinsmartagent.com/api/admin/tenants/3/features/advanced_analytics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "feature": "advanced_analytics",
    "enabled": false,
    "notes": "Trial user - not available"
  }'

# 5. فعال کردن چند فیچر یکجا (Bulk)
curl -X POST https://realty.artinsmartagent.com/api/admin/tenants/5/features/bulk \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "features": ["rag_system", "voice_ai", "advanced_analytics"],
    "enabled": true
  }'
```

---

## 📋 لیست فیچرهای موجود

| Feature Key | نام فارسی | توضیحات |
|------------|----------|---------|
| `rag_system` | سیستم دانش هوشمند | پاسخ‌های هوشمند با استفاده از دانش املاک دبی |
| `voice_ai` | تماس صوتی هوشمند | اتوماسیون تماس‌های تلفنی |
| `advanced_analytics` | آنالیتیکس پیشرفته | گزارشات و تحلیل‌های پیشرفته |
| `whatsapp_bot` | ربات واتساپ | اتصال به WhatsApp Business API |
| `telegram_bot` | ربات تلگرام | اتصال به Telegram Bot API |
| `broadcast_messages` | پیام‌های گروهی | ارسال پیام به همه کاربران |
| `lottery_system` | سیستم قرعه‌کشی | گیمیفیکیشن - قرعه‌کشی و جوایز |
| `calendar_booking` | رزرو وقت ملاقات | مدیریت تقویم و نوبت‌دهی |
| `lead_export` | خروجی لیدها | دانلود لیدها به CSV/Excel |
| `api_access` | دسترسی API | REST API برای یکپارچه‌سازی |
| `custom_branding` | برندینگ اختصاصی | سفارشی‌سازی ظاهر و برند |
| `multi_language` | چند زبانه | پشتیبانی از 4 زبان (فارسی/انگلیسی/عربی/روسی) |

---

## 🎯 سناریوهای استفاده

### 1. فعال کردن RAG System برای همه تنانت‌ها

```python
# در کد Python
from feature_flags import has_feature
from database import FeatureFlag

# در endpoint تولید پاسخ
if await has_feature(tenant_id, FeatureFlag.RAG_SYSTEM):
    # استفاده از سیستم RAG
    knowledge = get_relevant_knowledge(user_message, tenant_id)
    ai_response = generate_response_with_knowledge(message, knowledge)
else:
    # پاسخ ساده بدون دانش
    ai_response = generate_simple_response(message)
```

### 2. محدود کردن فیچر Voice AI به کاربران Premium

```python
from feature_flags import require_feature

@app.post("/api/voice/call")
async def start_voice_call(tenant_id: int):
    # چک اجباری - اگر فیچر غیرفعال باشد، 403 Error می‌دهد
    await require_feature(
        tenant_id, 
        FeatureFlag.VOICE_AI,
        error_message="Voice AI is only available for Premium users"
    )
    
    # ادامه کد...
    return start_call()
```

### 3. نمایش منوی دینامیک بر اساس فیچرها

```python
from feature_flags import get_enabled_features

@app.get("/api/dashboard/menu")
async def get_dashboard_menu(tenant_id: int):
    enabled_features = await get_enabled_features(tenant_id)
    
    menu_items = []
    
    if FeatureFlag.BROADCAST_MESSAGES in enabled_features:
        menu_items.append({"id": "broadcast", "label": "Broadcast"})
    
    if FeatureFlag.ADVANCED_ANALYTICS in enabled_features:
        menu_items.append({"id": "analytics", "label": "Analytics"})
    
    if FeatureFlag.LOTTERY_SYSTEM in enabled_features:
        menu_items.append({"id": "lottery", "label": "Lottery"})
    
    return {"menu": menu_items}
```

---

## 🔒 امنیت

- ✅ فقط Super Admin (tenant_id=0) می‌تواند فیچرها را مدیریت کند
- ✅ هر تغییر فیچر ثبت می‌شود (enabled_by, enabled_at, notes)
- ✅ Constraint یکتا: هر تنانت برای هر فیچر فقط یک رکورد دارد
- ✅ Foreign Key Cascade: حذف تنانت → حذف اتوماتیک فیچرهای او

---

## 📊 مانیتورینگ

### چک کردن فیچرهای فعال یک تنانت

```sql
SELECT 
    t.name AS tenant_name,
    f.feature,
    f.is_enabled,
    f.enabled_at,
    f.notes
FROM tenant_features f
JOIN tenants t ON f.tenant_id = t.id
WHERE t.id = 5;
```

### لیست تنانت‌هایی که یک فیچر را دارند

```sql
SELECT 
    t.id,
    t.name,
    f.enabled_at
FROM tenant_features f
JOIN tenants t ON f.tenant_id = t.id
WHERE f.feature = 'voice_ai' AND f.is_enabled = TRUE;
```

### آمار استفاده از فیچرها

```sql
SELECT 
    feature,
    COUNT(*) AS enabled_count,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tenants) AS percentage
FROM tenant_features
WHERE is_enabled = TRUE
GROUP BY feature
ORDER BY enabled_count DESC;
```

---

## ✅ چک‌لیست Deployment

- [ ] کد جدید را pull کردم (`git pull origin main`)
- [ ] Migration SQL را اجرا کردم (جدول `tenant_features` ساخته شد)
- [ ] Backend را restart کردم (`docker-compose restart backend`)
- [ ] API تست شد (GET `/api/admin/features` کار می‌کند)
- [ ] فیچرهای پیش‌فرض برای تنانت‌های موجود فعال شدند
- [ ] سیستم RAG برای همه فعال است

---

## 🎉 نتیجه

شما الان می‌توانید:
- ✅ برای هر تنانت فیچرهای خاصی را فعال/غیرفعال کنید
- ✅ فیچرهای جدید را تدریجی منتشر کنید (gradual rollout)
- ✅ به کاربران trial فیچرهای محدود بدهید
- ✅ به کاربران premium فیچرهای پیشرفته بدهید
- ✅ ردیابی کنید که چه کسی چه فیچری را فعال کرده

**سیستم Feature Flags شما آماده است!** 🚀
