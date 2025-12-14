# API Documentation

Base URL: `https://your-domain.com/api` or `http://localhost:8000`

---

## Authentication

All API endpoints (except webhooks) require JWT authentication.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "admin@yourcompany.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
  "token_type": "bearer",
  "tenant": {
    "id": 1,
    "name": "Your Real Estate Agency",
    "email": "admin@yourcompany.com",
    "subscription_status": "ACTIVE"
  }
}
```

### Using Auth Token

Include in request headers:
```http
Authorization: Bearer <your_access_token>
```

---

## Leads

### Get All Leads

```http
GET /leads?skip=0&limit=100&status=NEW
Authorization: Bearer <token>
```

**Query Parameters:**
- `skip` (int, optional): Pagination offset (default: 0)
- `limit` (int, optional): Max results (default: 100)
- `status` (string, optional): Filter by status (NEW, QUALIFIED, CONTACTED, APPOINTMENT_SET, WON, LOST)

**Response:**
```json
{
  "total": 156,
  "leads": [
    {
      "id": 1,
      "telegram_user_id": "123456789",
      "name": "Ahmed Hassan",
      "phone": "+971501234567",
      "language": "EN",
      "status": "QUALIFIED",
      "lead_score": 85,
      "temperature": "hot",
      "conversation_state": "SLOT_FILLING",
      "conversation_data": {
        "goal": "investment",
        "property_type": "apartment",
        "budget_min": 500000,
        "budget_max": 1000000
      },
      "created_at": "2025-12-10T10:30:00Z",
      "last_interaction": "2025-12-12T14:15:00Z"
    }
  ]
}
```

### Get Lead by ID

```http
GET /leads/{lead_id}
Authorization: Bearer <token>
```

### Get Lead Statistics

```http
GET /leads/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_leads": 1243,
  "new_today": 42,
  "conversion_rate": 18.5,
  "by_status": {
    "NEW": 156,
    "QUALIFIED": 89,
    "CONTACTED": 234,
    "WON": 125
  },
  "by_temperature": {
    "hot": 67,
    "warm": 234,
    "cold": 942
  },
  "avg_lead_score": 62.4
}
```

### Create Lead (Manual)

```http
POST /leads
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "John Doe",
  "phone": "+971501234567",
  "email": "john@example.com",
  "language": "EN",
  "conversation_data": {
    "goal": "living",
    "budget_min": 800000
  }
}
```

### Update Lead

```http
PATCH /leads/{lead_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "QUALIFIED",
  "notes": "Very interested in Marina area"
}
```

### Delete Lead

```http
DELETE /leads/{lead_id}
Authorization: Bearer <token>
```

---

## Properties

### Get All Properties

```http
GET /properties?transaction_type=sale&property_type=apartment
Authorization: Bearer <token>
```

**Query Parameters:**
- `transaction_type`: `sale`, `rent`, `offplan`
- `property_type`: `apartment`, `villa`, `townhouse`, `penthouse`, `studio`
- `min_price`, `max_price`: Number
- `bedrooms`, `bathrooms`: Number

**Response:**
```json
{
  "total": 45,
  "properties": [
    {
      "id": 1,
      "title": "Luxury 2BR Apartment in Dubai Marina",
      "description": "Stunning sea view, fully furnished",
      "transaction_type": "sale",
      "property_type": "apartment",
      "price_aed": 1500000,
      "bedrooms": 2,
      "bathrooms": 2,
      "area_sqft": 1200,
      "location": "Dubai Marina",
      "amenities": ["Pool", "Gym", "Parking"],
      "images": [
        "https://cdn.example.com/prop1_img1.jpg"
      ],
      "created_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

### Create Property

```http
POST /properties
Authorization: Bearer <token>
Content-Type: multipart/form-data

title=Luxury 3BR Villa
description=Spacious villa with garden
transaction_type=sale
property_type=villa
price_aed=3500000
bedrooms=3
bathrooms=4
area_sqft=2800
location=Arabian Ranches
images=@villa1.jpg
images=@villa2.jpg
```

---

## Appointments

### Get Available Slots

```http
GET /appointments/available-slots?date=2025-12-15
Authorization: Bearer <token>
```

**Response:**
```json
{
  "date": "2025-12-15",
  "slots": [
    {"time": "09:00", "available": true},
    {"time": "10:00", "available": false},
    {"time": "11:00", "available": true}
  ]
}
```

### Book Appointment

```http
POST /appointments
Authorization: Bearer <token>
Content-Type: application/json

{
  "lead_id": 123,
  "appointment_type": "consultation",
  "date": "2025-12-15",
  "time": "10:00",
  "notes": "Interested in Marina properties"
}
```

---

## ROI Calculator

### Generate ROI Report

```http
POST /roi/calculate
Authorization: Bearer <token>
Content-Type: application/json

{
  "lead_id": 123,
  "purchase_price": 1000000,
  "annual_rent": 70000,
  "purchase_costs": 50000,
  "maintenance_costs": 15000,
  "language": "EN"
}
```

**Response:**
```json
{
  "pdf_url": "/pdf_reports/roi_123_20251212.pdf",
  "calculations": {
    "net_roi": 5.5,
    "gross_yield": 7.0,
    "payback_period": 18,
    "monthly_income": 5833,
    "golden_visa_eligible": false
  }
}
```

---

## Broadcast

### Send Broadcast Message

```http
POST /broadcast
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "New Property Alert",
  "message": "Exclusive off-plan project launching!",
  "target_leads": [1, 2, 3],  // or "all" for all leads
  "channel": "telegram"  // or "whatsapp"
}
```

---

## Analytics

### Get Conversion Funnel

```http
GET /analytics/funnel?start_date=2025-12-01&end_date=2025-12-31
Authorization: Bearer <token>
```

**Response:**
```json
{
  "period": "2025-12-01 to 2025-12-31",
  "funnel": [
    {"stage": "New Leads", "count": 1243, "percentage": 100},
    {"stage": "Qualified", "count": 468, "percentage": 37.6},
    {"stage": "Contacted", "count": 234, "percentage": 18.8},
    {"stage": "Appointment Set", "count": 89, "percentage": 7.2},
    {"stage": "Won", "count": 23, "percentage": 1.8}
  ],
  "conversion_rate": 1.8
}
```

---

## Webhooks

### Telegram Webhook

```http
POST /telegram/webhook
Content-Type: application/json

// Telegram update object (automatically sent by Telegram)
```

### WhatsApp Webhook (WAHA)

```http
POST /waha/webhook
Content-Type: application/json

{
  "event": "message",
  "session": "default",
  "payload": {
    "from": "971501234567@c.us",
    "body": "Hello, I want to buy a property"
  }
}
```

---

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "detail": "Lead not found",
  "error_code": "LEAD_NOT_FOUND"
}
```

---

## Rate Limiting

- **Public endpoints**: 100 requests/minute
- **Authenticated endpoints**: 1000 requests/minute
- **Webhooks**: Unlimited

---

## Interactive API Docs

Visit `https://your-domain.com/docs` for interactive Swagger UI documentation.

---

## SDKs & Examples

### Python

```python
import requests

# Login
response = requests.post(
    "https://api.yourcompany.com/auth/login",
    json={"email": "admin@example.com", "password": "password"}
)
token = response.json()["access_token"]

# Get leads
headers = {"Authorization": f"Bearer {token}"}
leads = requests.get(
    "https://api.yourcompany.com/leads",
    headers=headers
).json()
```

### JavaScript

```javascript
// Login
const login = await fetch("https://api.yourcompany.com/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "admin@example.com",
    password: "password"
  })
});
const { access_token } = await login.json();

// Get leads
const leads = await fetch("https://api.yourcompany.com/leads", {
  headers: { "Authorization": `Bearer ${access_token}` }
});
const data = await leads.json();
```

---

## Support

For API questions:
- Documentation: https://docs.artinsmartrealty.com
- Email: api@artinsmartrealty.com
- GitHub Issues: https://github.com/arezoojoon/ArtinSmartRealtyPro/issues
