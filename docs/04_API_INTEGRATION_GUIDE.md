# 🔌 API & Integration Guide
## ArtinSmartRealty Platform - Developer Documentation

**Version:** 2.0  
**Last Updated:** November 28, 2025  
**Target Audience:** Client IT Departments, Integration Engineers, DevOps Teams  
**API Base URL:** `https://api.artinsmartrealty.com/v2`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Webhook Integration](#2-webhook-integration)
3. [REST API Reference](#3-rest-api-reference)
4. [Dashboard Access](#4-dashboard-access)
5. [Data Export Formats](#5-data-export-formats)
6. [Error Handling](#6-error-handling)
7. [Rate Limits](#7-rate-limits)
8. [Code Examples](#8-code-examples)

---

## 1. Authentication

### 1.1 API Key Generation

**Location:** Dashboard → Settings → API Keys

**Key Types:**

| Type | Purpose | Permissions | Expiry |
|------|---------|-------------|--------|
| **Read-Only** | Analytics, lead export | GET only | Never |
| **Write** | Create leads, update status | GET, POST, PATCH | Never |
| **Webhook** | Receive real-time events | N/A (inbound) | Never |

**Security Best Practices:**
- ✅ Store keys in environment variables (never in code)
- ✅ Rotate keys every 90 days
- ✅ Use separate keys for dev/staging/production
- ✅ Revoke immediately if compromised

---

### 1.2 Authentication Methods

#### **Method 1: API Key Header (Recommended)**

```http
GET /v2/leads HTTP/1.1
Host: api.artinsmartrealty.com
X-API-Key: artin_live_a1b2c3d4e5f6g7h8i9j0
X-Tenant-ID: 123
```

#### **Method 2: Bearer Token (OAuth 2.0)**

For server-to-server integrations requiring dynamic tenant switching:

```http
POST /v2/oauth/token HTTP/1.1
Host: api.artinsmartrealty.com
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=your_client_id
&client_secret=your_client_secret
&scope=leads:read leads:write
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "leads:read leads:write"
}
```

**Usage:**
```http
GET /v2/leads HTTP/1.1
Host: api.artinsmartrealty.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Tenant-ID: 123
```

---

## 2. Webhook Integration

### 2.1 Event Types

ArtinSmartRealty sends real-time webhooks for critical lead lifecycle events:

| Event | Description | Trigger |
|-------|-------------|---------|
| `lead.created` | New lead started conversation | User sends first message |
| `lead.qualified` | Lead completed qualification | Budget + property type captured |
| `lead.phone_captured` | Phone number provided | User enters valid phone |
| `lead.hot` | High-value lead identified | Budget > 5M AED + fast response |
| `lead.appointment_scheduled` | Viewing booked | User selects time slot |
| `lead.status_changed` | Lead status updated | Agent changes status in CRM |
| `conversation.timeout` | Lead inactive for 24h | Ghost protocol trigger |

---

### 2.2 Webhook Configuration

**Setup Location:** Dashboard → Settings → Webhooks

**Configuration Parameters:**

```json
{
  "webhook_url": "https://your-crm.com/api/webhooks/artinrealty",
  "secret_key": "whsec_a1b2c3d4e5f6g7h8",
  "events": [
    "lead.qualified",
    "lead.phone_captured",
    "lead.hot"
  ],
  "retry_policy": {
    "max_retries": 3,
    "retry_delay_seconds": 60
  }
}
```

---

### 2.3 Webhook Payload Structure

#### **Event: `lead.qualified`**

```json
POST https://your-crm.com/api/webhooks/artinrealty

Headers:
  Content-Type: application/json
  X-Artin-Event: lead.qualified
  X-Artin-Signature: sha256=a1b2c3d4e5f6g7h8i9j0...
  X-Artin-Delivery-ID: evt_a1b2c3d4e5f6g7h8

Body:
{
  "event": "lead.qualified",
  "timestamp": "2025-11-28T14:35:22Z",
  "tenant_id": 123,
  "data": {
    "lead_id": 12345,
    "source": "telegram",
    
    // Contact Information
    "name": "Ali Hassan",
    "phone": "+971501234567",
    "email": null,
    "telegram_username": "@ali_investor",
    "telegram_chat_id": "987654321",
    "language": "ar",
    
    // Qualification Data
    "budget_min": 2000000,
    "budget_max": 3000000,
    "budget_currency": "AED",
    "transaction_type": "BUY",
    "property_type": "APARTMENT",
    "purpose": "INVESTMENT",
    "bedrooms_min": 2,
    "bedrooms_max": 3,
    "preferred_location": "Dubai Marina",
    "preferred_locations": ["Dubai Marina", "JBR", "Business Bay"],
    
    // Behavioral Signals
    "status": "QUALIFIED",
    "hotness_score": 88,
    "qualification_duration_seconds": 68,
    "message_count": 12,
    "voice_messages_sent": 1,
    "images_uploaded": 0,
    
    // Conversation Context
    "conversation_state": "ENGAGEMENT",
    "pain_point": "inflation_risk",
    "urgency_score": 7,
    "last_interaction": "2025-11-28T14:35:20Z",
    
    // Voice Transcript (if available)
    "voice_transcript": "I want to invest in Dubai real estate to protect my wealth from inflation...",
    
    // URLs
    "conversation_url": "https://app.artinsmartrealty.com/leads/12345",
    "roi_report_url": "https://cdn.artinsmartrealty.com/reports/12345.pdf",
    
    // Custom Fields (if configured)
    "custom_fields": {
      "referral_source": "Instagram Ad",
      "campaign_id": "camp_summer2025"
    }
  }
}
```

---

#### **Event: `lead.hot`**

Triggered for high-value leads requiring immediate attention:

```json
{
  "event": "lead.hot",
  "timestamp": "2025-11-28T14:40:15Z",
  "tenant_id": 123,
  "data": {
    "lead_id": 12346,
    "name": "Fatima Al-Mansoori",
    "phone": "+971521234567",
    "budget_min": 8000000,
    "budget_max": 12000000,
    "property_type": "VILLA",
    "purpose": "RESIDENCY",
    "hotness_score": 98,
    "urgency_indicators": [
      "budget_above_5m",
      "fast_response_time",
      "golden_visa_intent",
      "phone_provided_voluntarily"
    ],
    "recommended_action": "Call within 15 minutes",
    "conversation_url": "https://app.artinsmartrealty.com/leads/12346"
  }
}
```

---

### 2.4 Webhook Security

#### **Signature Verification**

All webhooks include `X-Artin-Signature` header for verification:

```python
# Python Example
import hmac
import hashlib

def verify_webhook(request):
    secret = "whsec_a1b2c3d4e5f6g7h8"  # From dashboard
    signature = request.headers.get("X-Artin-Signature")
    
    # Signature format: sha256=<hash>
    expected_signature = "sha256=" + hmac.new(
        secret.encode(),
        request.body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid signature")
```

```javascript
// Node.js Example
const crypto = require('crypto');

function verifyWebhook(req, secret) {
  const signature = req.headers['x-artin-signature'];
  const expectedSignature = 'sha256=' + crypto
    .createHmac('sha256', secret)
    .update(req.rawBody)
    .digest('hex');
  
  if (signature !== expectedSignature) {
    throw new Error('Invalid signature');
  }
}
```

---

#### **Replay Attack Prevention**

Use `X-Artin-Delivery-ID` header to detect duplicate deliveries:

```python
# Redis-based deduplication (5-minute window)
import redis

r = redis.Redis()

def is_duplicate_webhook(delivery_id):
    key = f"webhook:processed:{delivery_id}"
    
    if r.exists(key):
        return True  # Already processed
    
    r.setex(key, 300, "1")  # Mark as processed for 5 minutes
    return False
```

---

### 2.5 Webhook Response Requirements

**Success Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "received",
  "processed": true,
  "crm_lead_id": "CRM-789"
}
```

**Failure Response (Will Retry):**
```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "status": "error",
  "message": "Database connection failed"
}
```

**Retry Policy:**
- **Max retries:** 3 attempts
- **Retry delays:** 1 minute, 5 minutes, 15 minutes
- **Timeout:** 10 seconds per request
- **Failure notification:** Email to admin after 3rd failure

---

## 3. REST API Reference

### 3.1 Leads Endpoint

#### **GET /v2/leads**

Retrieve leads with filtering and pagination.

**Request:**
```http
GET /v2/leads?status=QUALIFIED&limit=50&offset=0&sort=-created_at HTTP/1.1
Host: api.artinsmartrealty.com
X-API-Key: artin_live_a1b2c3d4e5f6g7h8
X-Tenant-ID: 123
```

**Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | String | Filter by lead status | `QUALIFIED` |
| `budget_min` | Integer | Min budget filter | `2000000` |
| `budget_max` | Integer | Max budget filter | `5000000` |
| `property_type` | String | Property type filter | `APARTMENT` |
| `created_after` | ISO 8601 | Created after date | `2025-11-01T00:00:00Z` |
| `language` | String | Lead language | `ar` |
| `limit` | Integer | Results per page (max 100) | `50` |
| `offset` | Integer | Pagination offset | `0` |
| `sort` | String | Sort field (`-` for desc) | `-created_at` |

**Response:**
```json
{
  "total": 245,
  "limit": 50,
  "offset": 0,
  "data": [
    {
      "id": 12345,
      "name": "Ali Hassan",
      "phone": "+971501234567",
      "email": null,
      "status": "QUALIFIED",
      "budget_min": 2000000,
      "budget_max": 3000000,
      "property_type": "APARTMENT",
      "transaction_type": "BUY",
      "purpose": "INVESTMENT",
      "preferred_location": "Dubai Marina",
      "language": "ar",
      "hotness_score": 88,
      "created_at": "2025-11-28T14:30:00Z",
      "last_interaction": "2025-11-28T14:35:00Z",
      "conversation_url": "https://app.artinsmartrealty.com/leads/12345"
    },
    // ... 49 more leads
  ]
}
```

---

#### **GET /v2/leads/{lead_id}**

Get detailed information for a single lead.

**Request:**
```http
GET /v2/leads/12345 HTTP/1.1
Host: api.artinsmartrealty.com
X-API-Key: artin_live_a1b2c3d4e5f6g7h8
X-Tenant-ID: 123
```

**Response:**
```json
{
  "id": 12345,
  "tenant_id": 123,
  "source": "telegram",
  
  // Contact Info
  "name": "Ali Hassan",
  "phone": "+971501234567",
  "email": null,
  "telegram_username": "@ali_investor",
  "telegram_chat_id": "987654321",
  "language": "ar",
  
  // Qualification
  "status": "QUALIFIED",
  "budget_min": 2000000,
  "budget_max": 3000000,
  "budget_currency": "AED",
  "transaction_type": "BUY",
  "property_type": "APARTMENT",
  "purpose": "INVESTMENT",
  "bedrooms_min": 2,
  "bedrooms_max": 3,
  "payment_method": "INSTALLMENT",
  "preferred_location": "Dubai Marina",
  "preferred_locations": ["Dubai Marina", "JBR"],
  
  // Behavioral Data
  "hotness_score": 88,
  "conversation_state": "ENGAGEMENT",
  "message_count": 12,
  "voice_messages_sent": 1,
  "images_uploaded": 0,
  "qualification_duration_seconds": 68,
  "pain_point": "inflation_risk",
  "urgency_score": 7,
  
  // Voice & Image
  "voice_transcript": "I want to invest in Dubai real estate...",
  "voice_file_url": "https://cdn.artinsmartrealty.com/voice/12345.ogg",
  "image_description": null,
  "image_file_url": null,
  
  // Conversation History
  "conversation_data": {
    "goal": "investment",
    "faq_questions_asked": [
      "What is the minimum investment for Golden Visa?",
      "Can I get a mortgage as a non-resident?"
    ]
  },
  
  // Timestamps
  "created_at": "2025-11-28T14:30:00Z",
  "updated_at": "2025-11-28T14:35:22Z",
  "last_interaction": "2025-11-28T14:35:20Z",
  "ghost_reminder_sent": false,
  
  // Appointment (if scheduled)
  "appointment": {
    "id": 789,
    "type": "VIEWING",
    "scheduled_date": "2025-11-30T15:00:00Z",
    "status": "CONFIRMED",
    "agent_id": 5,
    "agent_name": "Ahmed Al-Rashid"
  }
}
```

---

#### **POST /v2/leads**

Create a new lead manually (for CRM sync).

**Request:**
```http
POST /v2/leads HTTP/1.1
Host: api.artinsmartrealty.com
X-API-Key: artin_live_a1b2c3d4e5f6g7h8
X-Tenant-ID: 123
Content-Type: application/json

{
  "name": "Sarah Ahmed",
  "phone": "+971521234567",
  "email": "sarah@example.com",
  "source": "website",
  "budget_min": 1500000,
  "budget_max": 2000000,
  "property_type": "APARTMENT",
  "transaction_type": "BUY",
  "purpose": "LIVING",
  "preferred_location": "Business Bay",
  "language": "en",
  "notes": "Referred by existing client"
}
```

**Response:**
```json
{
  "id": 12346,
  "status": "NEW",
  "created_at": "2025-11-28T15:00:00Z",
  "conversation_url": "https://app.artinsmartrealty.com/leads/12346"
}
```

---

#### **PATCH /v2/leads/{lead_id}**

Update lead information or status.

**Request:**
```http
PATCH /v2/leads/12345 HTTP/1.1
Host: api.artinsmartrealty.com
X-API-Key: artin_live_a1b2c3d4e5f6g7h8
X-Tenant-ID: 123
Content-Type: application/json

{
  "status": "NEGOTIATING",
  "notes": "Client interested in Property #456. Sent brochure.",
  "agent_id": 5
}
```

**Response:**
```json
{
  "id": 12345,
  "status": "NEGOTIATING",
  "updated_at": "2025-11-28T15:10:00Z"
}
```

---

### 3.2 Analytics Endpoint

#### **GET /v2/analytics/funnel**

Retrieve sales funnel statistics.

**Request:**
```http
GET /v2/analytics/funnel?period=30d HTTP/1.1
Host: api.artinsmartrealty.com
X-API-Key: artin_live_a1b2c3d4e5f6g7h8
X-Tenant-ID: 123
```

**Query Parameters:**

| Parameter | Values | Description |
|-----------|--------|-------------|
| `period` | `7d`, `30d`, `90d`, `365d` | Time period |
| `start_date` | ISO 8601 | Custom start date |
| `end_date` | ISO 8601 | Custom end date |

**Response:**
```json
{
  "period": "30d",
  "start_date": "2025-10-29T00:00:00Z",
  "end_date": "2025-11-28T23:59:59Z",
  "funnel": [
    {
      "stage": "started",
      "count": 1000,
      "percentage": 100,
      "drop_off_from_previous": 0
    },
    {
      "stage": "qualified",
      "count": 400,
      "percentage": 40,
      "drop_off_from_previous": 60
    },
    {
      "stage": "phone_captured",
      "count": 150,
      "percentage": 15,
      "drop_off_from_previous": 62.5
    },
    {
      "stage": "viewing_scheduled",
      "count": 50,
      "percentage": 5,
      "drop_off_from_previous": 66.7
    },
    {
      "stage": "closed_won",
      "count": 20,
      "percentage": 2,
      "drop_off_from_previous": 60
    }
  ],
  "conversion_rate": 2.0,
  "average_qualification_time_seconds": 72
}
```

---

#### **GET /v2/analytics/agents**

Get agent performance metrics.

**Request:**
```http
GET /v2/analytics/agents?period=30d&sort=-closed_deals HTTP/1.1
Host: api.artinsmartrealty.com
X-API-Key: artin_live_a1b2c3d4e5f6g7h8
X-Tenant-ID: 123
```

**Response:**
```json
{
  "period": "30d",
  "data": [
    {
      "agent_id": 5,
      "agent_name": "Ahmed Al-Rashid",
      "email": "ahmed@example.com",
      "closed_deals": 8,
      "total_value_aed": 18500000,
      "average_deal_value_aed": 2312500,
      "leads_assigned": 45,
      "conversion_rate": 17.8,
      "average_response_time_seconds": 45,
      "performance_score": 95
    },
    {
      "agent_id": 3,
      "agent_name": "Sarah Hassan",
      "email": "sarah@example.com",
      "closed_deals": 6,
      "total_value_aed": 13200000,
      "average_deal_value_aed": 2200000,
      "leads_assigned": 38,
      "conversion_rate": 15.8,
      "average_response_time_seconds": 80,
      "performance_score": 88
    }
  ]
}
```

---

### 3.3 Export Endpoint

#### **GET /v2/export/leads**

Export leads to Excel/CSV.

**Request:**
```http
GET /v2/export/leads?format=xlsx&status=QUALIFIED HTTP/1.1
Host: api.artinsmartrealty.com
X-API-Key: artin_live_a1b2c3d4e5f6g7h8
X-Tenant-ID: 123
```

**Query Parameters:**

| Parameter | Values | Description |
|-----------|--------|-------------|
| `format` | `xlsx`, `csv` | Export format |
| `status` | Any lead status | Filter by status |
| `created_after` | ISO 8601 | Date filter |
| `columns` | Comma-separated | Select specific columns |

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="leads_2025-11-28.xlsx"

[Binary Excel file]
```

**Excel Columns:**
| Column | Example |
|--------|---------|
| Lead ID | 12345 |
| Name | Ali Hassan |
| Phone | +971501234567 |
| Email | ali@example.com |
| Status | QUALIFIED |
| Budget Min | 2,000,000 |
| Budget Max | 3,000,000 |
| Property Type | APARTMENT |
| Transaction Type | BUY |
| Purpose | INVESTMENT |
| Location | Dubai Marina |
| Hotness Score | 88 |
| Created Date | 2025-11-28 14:30:00 |
| Last Interaction | 2025-11-28 14:35:20 |

---

## 4. Dashboard Access

### 4.1 Tenant Dashboard URL Structure

**Format:** `https://app.artinsmartrealty.com/{tenant_slug}`

**Example:** `https://app.artinsmartrealty.com/dubai-elite-properties`

**Login Methods:**
1. **Email + Password** (default)
2. **SSO (SAML 2.0)** - Enterprise only
3. **Google OAuth** - Optional
4. **Magic Link** - Passwordless email login

---

### 4.2 Dashboard Features

#### **Lead Management**
- Kanban board (drag & drop)
- Lead detail view (conversation history)
- Bulk actions (assign, export, delete)
- Advanced filters (20+ criteria)

#### **Analytics**
- Sales funnel visualization
- Agent leaderboard
- Revenue charts (MRR, ARR)
- Custom date range selection
- Export to PDF/Excel

#### **Live Chat Monitor**
- Real-time conversation stream
- Agent takeover (✋ button)
- Message history
- Typing indicators
- WebSocket updates

#### **Settings**
- Bot customization (branding, colors)
- Webhook configuration
- API key management
- Team management (invite agents)
- Property inventory upload

---

### 4.3 Embedding Dashboard (iframe)

**Allowed for Enterprise clients:**

```html
<iframe
  src="https://app.artinsmartrealty.com/embed/leads?token=embed_a1b2c3d4"
  width="100%"
  height="800"
  frameborder="0"
  allow="clipboard-read; clipboard-write"
></iframe>
```

**Embed Token Generation:**
Dashboard → Settings → Embed → Generate Token

---

## 5. Data Export Formats

### 5.1 JSON Export

**Request:**
```http
GET /v2/leads?export=json HTTP/1.1
```

**Response:**
```json
{
  "export_id": "exp_a1b2c3d4",
  "created_at": "2025-11-28T15:30:00Z",
  "total_records": 245,
  "data": [
    { /* Lead 1 */ },
    { /* Lead 2 */ },
    // ...
  ]
}
```

---

### 5.2 CSV Export

**Response:**
```csv
lead_id,name,phone,email,status,budget_min,budget_max,property_type,created_at
12345,Ali Hassan,+971501234567,,QUALIFIED,2000000,3000000,APARTMENT,2025-11-28T14:30:00Z
12346,Sarah Ahmed,+971521234567,sarah@example.com,NEW,1500000,2000000,VILLA,2025-11-28T15:00:00Z
```

---

### 5.3 Excel Export

**Features:**
- Auto-adjusted column widths
- Formatted numbers (currency, percentages)
- Color-coded status cells
- Frozen header row
- Filters enabled

**File Size Limits:**
- CSV: Unlimited
- Excel: Max 100,000 rows (contact support for larger exports)

---

## 6. Error Handling

### 6.1 HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| `200 OK` | Success | Process response |
| `201 Created` | Resource created | Read `Location` header for URL |
| `400 Bad Request` | Invalid parameters | Check error message |
| `401 Unauthorized` | Missing/invalid API key | Verify authentication |
| `403 Forbidden` | Insufficient permissions | Check tenant access |
| `404 Not Found` | Resource doesn't exist | Verify lead/endpoint ID |
| `409 Conflict` | Duplicate resource | Use existing resource |
| `422 Unprocessable Entity` | Validation error | Fix request body |
| `429 Too Many Requests` | Rate limit exceeded | Wait and retry |
| `500 Internal Server Error` | Server error | Retry with backoff |
| `503 Service Unavailable` | Maintenance mode | Check status page |

---

### 6.2 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid phone number format",
    "details": {
      "field": "phone",
      "provided": "123456",
      "expected": "International format starting with +"
    },
    "request_id": "req_a1b2c3d4e5f6g7h8",
    "documentation_url": "https://docs.artinsmartrealty.com/errors/validation"
  }
}
```

**Common Error Codes:**

| Code | Description |
|------|-------------|
| `AUTHENTICATION_ERROR` | API key invalid or missing |
| `VALIDATION_ERROR` | Request body validation failed |
| `RESOURCE_NOT_FOUND` | Lead or endpoint doesn't exist |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INSUFFICIENT_PERMISSIONS` | Tenant access denied |
| `WEBHOOK_VERIFICATION_FAILED` | Signature mismatch |

---

## 7. Rate Limits

### 7.1 API Rate Limits

| Plan | Requests/Minute | Burst Allowance |
|------|----------------|-----------------|
| **Starter** | 60 | 120 (2x for 60s) |
| **Professional** | 100 | 200 |
| **Enterprise** | 500 | 1000 |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1732867200
```

**Exceeded Response:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit of 100 requests/minute exceeded",
    "retry_after_seconds": 60
  }
}
```

---

### 7.2 Webhook Delivery Rate Limits

**Outbound Webhooks:**
- Max 10 concurrent deliveries per tenant
- Timeout: 10 seconds per webhook
- Retry backoff: 1 min, 5 min, 15 min

**Best Practice:**
```python
# Process webhook asynchronously
@app.post("/webhooks/artinrealty")
async def webhook_handler(request):
    # Verify signature
    verify_webhook(request)
    
    # Queue for async processing
    queue.enqueue(process_webhook, request.json())
    
    # Return 200 immediately
    return {"status": "received"}
```

---

## 8. Code Examples

### 8.1 Python (Retrieve Qualified Leads)

```python
import requests

API_KEY = "artin_live_a1b2c3d4e5f6g7h8"
TENANT_ID = 123
BASE_URL = "https://api.artinsmartrealty.com/v2"

headers = {
    "X-API-Key": API_KEY,
    "X-Tenant-ID": str(TENANT_ID)
}

# Get qualified leads from last 7 days
params = {
    "status": "QUALIFIED",
    "created_after": "2025-11-21T00:00:00Z",
    "limit": 100
}

response = requests.get(
    f"{BASE_URL}/leads",
    headers=headers,
    params=params
)

if response.status_code == 200:
    leads = response.json()["data"]
    print(f"Found {len(leads)} qualified leads")
    
    for lead in leads:
        print(f"- {lead['name']}: {lead['phone']} (Budget: {lead['budget_min']})")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

---

### 8.2 Node.js (Webhook Handler with Express)

```javascript
const express = require('express');
const crypto = require('crypto');
const bodyParser = require('body-parser');

const app = express();
app.use(bodyParser.json());

const WEBHOOK_SECRET = 'whsec_a1b2c3d4e5f6g7h8';

// Webhook endpoint
app.post('/webhooks/artinrealty', (req, res) => {
  // Verify signature
  const signature = req.headers['x-artin-signature'];
  const expectedSignature = 'sha256=' + crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(JSON.stringify(req.body))
    .digest('hex');
  
  if (signature !== expectedSignature) {
    return res.status(401).json({ error: 'Invalid signature' });
  }
  
  // Process webhook
  const event = req.body;
  
  if (event.event === 'lead.qualified') {
    const lead = event.data;
    
    // Sync to CRM
    syncToCRM({
      name: lead.name,
      phone: lead.phone,
      budget: lead.budget_min,
      source: 'ArtinSmartRealty Bot'
    });
    
    console.log(`Qualified lead: ${lead.name} (${lead.phone})`);
  }
  
  res.json({ status: 'received' });
});

app.listen(3000, () => {
  console.log('Webhook server running on port 3000');
});
```

---

### 8.3 PHP (Create Lead via API)

```php
<?php
$apiKey = 'artin_live_a1b2c3d4e5f6g7h8';
$tenantId = 123;
$baseUrl = 'https://api.artinsmartrealty.com/v2';

$leadData = [
    'name' => 'Mohammed Ali',
    'phone' => '+971501234567',
    'email' => 'mohammed@example.com',
    'source' => 'website',
    'budget_min' => 3000000,
    'budget_max' => 5000000,
    'property_type' => 'VILLA',
    'transaction_type' => 'BUY',
    'purpose' => 'LIVING',
    'preferred_location' => 'Emirates Hills'
];

$ch = curl_init("{$baseUrl}/leads");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($leadData));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'X-API-Key: ' . $apiKey,
    'X-Tenant-ID: ' . $tenantId,
    'Content-Type: application/json'
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode == 201) {
    $lead = json_decode($response, true);
    echo "Lead created: ID {$lead['id']}\n";
} else {
    echo "Error: HTTP {$httpCode} - {$response}\n";
}
?>
```

---

### 8.4 cURL (Export Leads to Excel)

```bash
#!/bin/bash

API_KEY="artin_live_a1b2c3d4e5f6g7h8"
TENANT_ID=123
BASE_URL="https://api.artinsmartrealty.com/v2"

# Export qualified leads from last 30 days
curl -X GET \
  "${BASE_URL}/export/leads?format=xlsx&status=QUALIFIED&period=30d" \
  -H "X-API-Key: ${API_KEY}" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -o "leads_$(date +%Y%m%d).xlsx"

echo "Leads exported to leads_$(date +%Y%m%d).xlsx"
```

---

## 9. Testing & Sandbox

### 9.1 Sandbox Environment

**Base URL:** `https://sandbox.artinsmartrealty.com/v2`

**Features:**
- Separate test tenants
- Simulated webhook events
- Test API keys (prefix: `artin_test_`)
- No real Telegram/WhatsApp integration
- Data reset every 24 hours

**Request Test API Key:**
Dashboard → Settings → Developer Tools → Generate Sandbox Key

---

### 9.2 Webhook Testing Tool

**Built-in Webhook Tester:**
Dashboard → Settings → Webhooks → Test Event

**Manual Trigger:**
```http
POST https://sandbox.artinsmartrealty.com/v2/webhooks/test
X-API-Key: artin_test_a1b2c3d4
X-Tenant-ID: 123
Content-Type: application/json

{
  "event_type": "lead.qualified",
  "webhook_url": "https://your-dev-server.com/webhooks/test"
}
```

---

## 10. Support & Resources

### 10.1 Documentation Links

- **API Reference:** https://docs.artinsmartrealty.com/api
- **Webhook Guide:** https://docs.artinsmartrealty.com/webhooks
- **Integration Examples:** https://github.com/ArtinSmartRealty/api-examples
- **Changelog:** https://docs.artinsmartrealty.com/changelog
- **Status Page:** https://status.artinsmartrealty.com

---

### 10.2 Developer Support

**Channels:**
- Email: developers@artinsmartrealty.com
- Slack Community: artinrealty-dev.slack.com
- GitHub Issues: github.com/ArtinSmartRealty/api-client

**Response Times:**
- Email: 24 hours (business days)
- Slack: Community-driven
- Critical issues: 4 hours (Premium/Enterprise)

---

**Document Version:** 2.0  
**Last Updated:** November 28, 2025  
**API Version:** v2 (Stable)

**© 2025 ArtinSmartRealty. All rights reserved.**
