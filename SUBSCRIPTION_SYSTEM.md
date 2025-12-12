# 💳 Subscription System - Implementation Guide

**تاریخ:** 12 دسامبر 2025  
**نوع:** Feature Implementation  
**وضعیت:** ✅ Complete

---

## 📋 خلاصه

یک سیستم Subscription کامل با دو پلن:
- **Basic Plan ($99/month):** ربات + فالوآپ
- **Pro Plan ($199/month):** همه چیز + لید جنریشن (LinkedIn Scraper)

---

## 🎯 Features Implemented

### 1. Subscription Plans
```python
# backend/database.py

class SubscriptionPlan(str, Enum):
    FREE = "free"       # Trial only
    BASIC = "basic"     # Bot + Follow-up (No LinkedIn)
    PRO = "pro"         # Full features (Bot + Follow-up + LinkedIn)

class SubscriptionStatus(str, Enum):
    TRIAL = "trial"     # 7-14 days trial
    ACTIVE = "active"   # Paid subscription
    SUSPENDED = "suspended"  # Payment failed
    CANCELLED = "cancelled"  # User cancelled
    EXPIRED = "expired"  # Trial/subscription expired
```

### 2. Tenant Model Updates
```python
# New fields in Tenant model:
subscription_plan = Column(SQLEnum(SubscriptionPlan), default=SubscriptionPlan.FREE)
subscription_status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
trial_ends_at = Column(DateTime, nullable=True)
subscription_starts_at = Column(DateTime, nullable=True)
subscription_ends_at = Column(DateTime, nullable=True)
billing_cycle = Column(String(20), default="monthly")  # "monthly" or "yearly"
payment_method = Column(String(50), nullable=True)
last_payment_date = Column(DateTime, nullable=True)
next_payment_date = Column(DateTime, nullable=True)
```

### 3. Pricing Configuration
```python
PRICING = {
    "basic": {
        "price_monthly": 99,     # USD
        "price_yearly": 999,      # USD (2 months free)
        "trial_days": 7,
        "max_leads": 1000,
        "max_messages_per_month": 10000,
        "features": [
            "WhatsApp & Telegram Bot",
            "AI-powered conversations",
            "Automated follow-ups",
            "Lead scoring & grading",
            "Appointment scheduling",
            "Multi-language support"
        ]
    },
    "pro": {
        "price_monthly": 199,     # USD
        "price_yearly": 1999,     # USD (2 months free)
        "trial_days": 14,
        "max_leads": 10000,
        "max_messages_per_month": 100000,
        "features": [
            "✅ All Basic features",
            "LinkedIn Lead Scraper",
            "Automated outreach campaigns",
            "Advanced analytics",
            "CRM integration",
            "White-label branding",
            "Priority support"
        ]
    }
}
```

### 4. Feature Access Control
```python
# backend/subscription_guard.py

FEATURE_ACCESS = {
    "linkedin_scraper": [SubscriptionPlan.PRO],  # Only Pro
    "lead_generation": [SubscriptionPlan.PRO],   # Only Pro
    "bot": [SubscriptionPlan.BASIC, SubscriptionPlan.PRO],  # Both
    "followup": [SubscriptionPlan.BASIC, SubscriptionPlan.PRO],  # Both
    "whatsapp": [SubscriptionPlan.BASIC, SubscriptionPlan.PRO],  # Both
    "telegram": [SubscriptionPlan.BASIC, SubscriptionPlan.PRO],  # Both
    "advanced_analytics": [SubscriptionPlan.PRO],  # Only Pro
}

# Usage:
if not check_feature_access(tenant, "linkedin_scraper"):
    raise HTTPException(403, detail="Upgrade to Pro required")
```

---

## 🚀 API Endpoints

### 1. Get Pricing
```http
GET /api/subscription/pricing

Response:
{
  "plans": {
    "basic": {
      "name": "Basic Plan",
      "price_monthly": 99,
      "price_yearly": 999,
      "features": [...]
    },
    "pro": {
      "name": "Pro Plan",
      "price_monthly": 199,
      "price_yearly": 1999,
      "features": [...]
    }
  }
}
```

### 2. Register New Tenant
```http
POST /api/subscription/register

Request:
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "secure_password",
  "company_name": "Real Estate Co",
  "phone": "+971501234567",
  "plan": "pro",
  "billing_cycle": "monthly",
  "language": "en"
}

Response:
{
  "tenant_id": 1,
  "email": "john@example.com",
  "plan": "pro",
  "status": "trial",
  "trial_ends_at": "2025-12-26T10:00:00",
  "message": "Registration successful! Your 14-day trial has started."
}
```

### 3. Confirm Payment
```http
POST /api/subscription/payment/confirm

Request:
{
  "tenant_id": 1,
  "plan": "pro",
  "billing_cycle": "monthly",
  "payment_method": "stripe",
  "transaction_id": "ch_1234567890"
}

Response:
{
  "status": "success",
  "message": "Payment confirmed. Subscription activated!",
  "subscription_ends_at": "2026-01-12T10:00:00",
  "next_payment_date": "2026-01-12T10:00:00"
}
```

### 4. Get Subscription Status
```http
GET /api/subscription/status/{tenant_id}

Response:
{
  "tenant_id": 1,
  "email": "john@example.com",
  "plan": "pro",
  "status": "active",
  "is_active": true,
  "trial_ends_at": null,
  "subscription_starts_at": "2025-12-12T10:00:00",
  "subscription_ends_at": "2026-01-12T10:00:00",
  "next_payment_date": "2026-01-12T10:00:00",
  "is_trial_expired": false,
  "is_subscription_expired": false,
  "plan_info": {...}
}
```

### 5. Upgrade Plan
```http
POST /api/subscription/upgrade

Request:
{
  "tenant_id": 1,
  "new_plan": "pro"
}

Response:
{
  "status": "success",
  "message": "Upgraded to Pro plan!",
  "plan": "pro"
}
```

### 6. Cancel Subscription
```http
POST /api/subscription/cancel/{tenant_id}

Response:
{
  "status": "cancelled",
  "message": "Subscription cancelled. Access continues until end of billing period.",
  "ends_at": "2026-01-12T10:00:00"
}
```

---

## 🎨 Frontend Pages

### 1. Login Page (`frontend/login.html`)
- Email/password login
- **"Start Free Trial" button** prominently displayed
- Features list to attract new users
- Forgot password link

### 2. Registration Page (`frontend/register.html`)
- Beautiful dual-column layout
- Plan selector (Basic vs Pro)
- Billing cycle toggle (Monthly vs Yearly)
- Live price updates
- Pricing cards with feature comparison
- Form validation
- Auto-redirect to login after successful registration

---

## 🔒 LinkedIn Scraper Protection

LinkedIn routes are now protected with subscription checks:

```python
# backend/api/linkedin_routes.py

@router.post("/generate-message")
async def generate_linkedin_message(request: GenerateMessageRequest):
    # ✅ Check subscription active
    if not check_subscription_active(tenant):
        raise HTTPException(403, detail={
            "error": "subscription_expired",
            "message": "Your subscription has expired.",
            "upgrade_url": "/subscription/pricing"
        })
    
    # ✅ Check Pro plan
    if not check_feature_access(tenant, "linkedin_scraper"):
        raise HTTPException(403, detail={
            "error": "upgrade_required",
            "feature": "linkedin_scraper",
            "required_plan": "pro",
            "message": "LinkedIn Scraper requires Pro Plan.",
            "upgrade_url": "/subscription/pricing"
        })
```

---

## 💾 Database Migration

Run migration to add subscription columns:

```bash
# From project root
python migrate_subscription_plans.py
```

Migration adds:
- `SubscriptionPlan` enum type
- `SubscriptionStatus` enum update
- 7 new columns to `tenants` table
- Migrates existing tenants to `free` plan

---

## 📊 Usage Limits

```python
# backend/subscription_guard.py

get_plan_limits(tenant) returns:

FREE/TRIAL:
- max_leads: 100
- max_messages_per_month: 1,000
- max_bot_instances: 1
- max_followup_campaigns: 3
- linkedin_scraper: False
- advanced_analytics: False

BASIC ($99/month):
- max_leads: 1,000
- max_messages_per_month: 10,000
- max_bot_instances: 2
- max_followup_campaigns: 10
- linkedin_scraper: False
- advanced_analytics: False

PRO ($199/month):
- max_leads: 10,000
- max_messages_per_month: 100,000
- max_bot_instances: 10
- max_followup_campaigns: 100
- linkedin_scraper: True
- advanced_analytics: True
```

---

## 🎯 Plan Comparison

| Feature | Free/Trial | Basic | Pro |
|---------|-----------|-------|-----|
| **Price** | $0 (7-14 days) | $99/month | $199/month |
| **WhatsApp Bot** | ✅ | ✅ | ✅ |
| **Telegram Bot** | ✅ | ✅ | ✅ |
| **AI Conversations** | ✅ | ✅ | ✅ |
| **Automated Follow-ups** | ✅ | ✅ | ✅ |
| **Lead Scoring** | ✅ | ✅ | ✅ |
| **Appointment Booking** | ✅ | ✅ | ✅ |
| **Multi-language** | ✅ | ✅ | ✅ |
| **Max Leads** | 100 | 1,000 | 10,000 |
| **Messages/month** | 1,000 | 10,000 | 100,000 |
| **Bot Instances** | 1 | 2 | 10 |
| **LinkedIn Scraper** | ❌ | ❌ | ✅ |
| **Lead Generation** | ❌ | ❌ | ✅ |
| **Advanced Analytics** | ❌ | ❌ | ✅ |
| **CRM Integration** | ❌ | ❌ | ✅ |
| **White-label Branding** | ❌ | ❌ | ✅ |
| **Priority Support** | ❌ | ❌ | ✅ |

---

## 🔄 User Flow

### New User Registration:
1. User visits `/login.html`
2. Clicks "Start Free Trial"
3. Redirected to `/register.html`
4. Selects plan (Basic or Pro)
5. Enters details and submits
6. Backend creates tenant with `subscription_status=TRIAL`
7. Trial period starts (7-14 days)
8. User redirected to `/login.html`
9. Logs in and starts using platform

### Trial to Paid Conversion:
1. User receives email notification 2 days before trial ends
2. User clicks "Upgrade Now"
3. Redirected to payment page
4. Enters payment details (Stripe/PayPal)
5. Payment processed
6. Backend calls `/api/subscription/payment/confirm`
7. `subscription_status` → `ACTIVE`
8. `subscription_ends_at` set to +30 days
9. User continues using platform

### Feature Access:
1. User tries to use LinkedIn Scraper
2. Backend checks `check_feature_access(tenant, "linkedin_scraper")`
3. If `subscription_plan != PRO`:
   - Return 403 with upgrade message
   - Show pricing modal
4. If `subscription_plan == PRO`:
   - Allow access
   - Execute feature

---

## 🎨 UI/UX Highlights

### Login Page:
- ✅ Clean, professional design
- ✅ "Start Free Trial" CTA prominently displayed
- ✅ Features list to showcase value
- ✅ Gradient background matching brand
- ✅ Responsive design

### Registration Page:
- ✅ Dual-column layout (form + pricing)
- ✅ Interactive plan selector
- ✅ Monthly/Yearly toggle with savings
- ✅ Live price updates
- ✅ Pro plan highlighted
- ✅ Clear feature comparison
- ✅ Form validation
- ✅ Success/error alerts

---

## 🚀 Deployment Steps

1. **Database Migration:**
```bash
python migrate_subscription_plans.py
```

2. **Environment Variables:**
```bash
# .env
STRIPE_SECRET_KEY=sk_test_...  # Add payment gateway keys
STRIPE_PUBLISHABLE_KEY=pk_test_...
PAYPAL_CLIENT_ID=...
PAYPAL_SECRET=...
```

3. **Update main.py:**
Already done ✅ - subscription router included

4. **Deploy Frontend:**
```bash
# Copy files to server
scp frontend/login.html user@server:/var/www/html/
scp frontend/register.html user@server:/var/www/html/
```

5. **Test:**
- Visit `/login.html`
- Click "Start Free Trial"
- Register with test account
- Verify trial started
- Try accessing LinkedIn Scraper
- Verify plan restrictions work

---

## 📝 Next Steps (Optional Enhancements)

1. **Payment Integration:**
   - Integrate Stripe API
   - Integrate PayPal API
   - Add crypto payment option

2. **Email Notifications:**
   - Trial ending reminder (2 days before)
   - Payment successful
   - Payment failed
   - Subscription renewed
   - Subscription cancelled

3. **Admin Dashboard:**
   - View all subscriptions
   - Manually upgrade/downgrade users
   - View revenue metrics
   - Send promotional offers

4. **Usage Analytics:**
   - Track feature usage per tenant
   - Show usage vs limits
   - Send alerts when approaching limits

5. **Webhooks:**
   - Stripe webhooks for automatic payment processing
   - PayPal IPN for payment notifications

---

## ✅ Checklist

- [x] Added `SubscriptionPlan` and `SubscriptionStatus` enums
- [x] Updated Tenant model with subscription fields
- [x] Created subscription API (`/api/subscription/*`)
- [x] Created feature access control (`subscription_guard.py`)
- [x] Protected LinkedIn Scraper with Pro plan check
- [x] Created registration page with plan selector
- [x] Created login page with "Start Free Trial" button
- [x] Created database migration script
- [x] Updated main.py with subscription router
- [x] Documented everything
- [ ] Integrate payment gateway (Stripe/PayPal)
- [ ] Setup email notifications
- [ ] Add admin subscription management
- [ ] Deploy to production

---

**Status:** ✅ Core Implementation Complete  
**Payment Integration:** Pending (Stripe/PayPal)  
**Production Ready:** 90% (needs payment gateway)

---

**Git Commit:** `git commit -m "Add subscription system with Basic and Pro plans"`
