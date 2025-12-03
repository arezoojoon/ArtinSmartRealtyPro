# 🏢 ArtinSmartRealty - AI Real Estate Assistant Platform

> **"Your AI Real Estate Assistant - Never Sleep, Always Sell!"**  
> **"دستیار هوشمند املاک شما - هیچ‌وقت نمی‌خوابد، همیشه می‌فروشد!"**

---

## 🎯 **ما چی هستیم؟**

**ArtinSmartRealty** یک پلتفرم **SaaS چندزبانه** است که به مشاوران املاک یک **ربات هوش مصنوعی 24/7** می‌دهد تا:
- ✅ با مشتریان چت کند (تلگرام + واتساپ)
- ✅ نیازشان را بفهمد و کوالیفای کند
- ✅ ملک پیشنهاد دهد (از املاک خود مشاور)
- ✅ وقت ملاقات رزرو کند
- ✅ به صورت خودکار Follow-up کند

**Live Demo**: [realty.artinsmartagent.com](https://realty.artinsmartagent.com)

---

## 📚 **مستندات محصول**

| فایل | توضیح |
|------|--------|
| 📖 [PRODUCT_PRESENTATION.md](PRODUCT_PRESENTATION.md) | **سناریوی کامل تجربه مشتری** - از اولین پیام تا خرید ملک |
| 📄 [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) | **خلاصه اجرایی 1 صفحه** - برای سرمایه‌گذاران |
| 🎤 [PITCH_DECK_SCRIPT.md](PITCH_DECK_SCRIPT.md) | **اسکریپت ارائه 10 اسلایدی** - 7 دقیقه |
| 📊 [COMPETITIVE_ANALYSIS.md](COMPETITIVE_ANALYSIS.md) | **مقایسه با رقبا** - چرا ما بهتریم؟ |
| 🐛 [BUGS_FIXED.md](BUGS_FIXED.md) | **گزارش باگ‌های رفع شده** - Dec 2, 2025 |

---

## 🚀 **شروع سریع (برای دولوپرها)**

```bash
# Clone repository
git clone https://github.com/arezoojoon/ArtinSmartRealty.git
cd ArtinSmartRealty

# Start with Docker
docker-compose up -d

# Dashboard: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**لاگین پیش‌فرض**:
- Super Admin: `admin@artinsmartrealty.com` / `SuperAdmin123!`

## 🚀 Features

### 🏢 Multi-Tenant Architecture
- **Strict Data Isolation**: Each agent has completely separate data
- **Dedicated Bots**: Unique Telegram bot + WhatsApp number per agent
- **Custom Branding**: Logo and primary color for PDFs
- **Subscription Management**: Trial (14 days) → Active → Suspended

### 🔐 Authentication & Roles
| Role | Access |
|------|--------|
| **Super Admin** | Platform owner - view all tenants, access any dashboard |
| **Tenant (Agent)** | Own data only - leads, schedule, settings |
| **Lead (User)** | Bot interaction only |

### 🤖 Dual-Channel Bot Integration
- **Telegram**: Custom bot with inline keyboards
- **WhatsApp**: Business API with interactive buttons
- **Voice Intelligence**: Transcribe voice messages + extract entities
- **Multi-Language**: EN, FA (Persian), AR (Arabic), RU (Russian)

### 🧠 AI-Powered Features
- **Google Gemini 2.0 Flash**: Smart entity extraction, language detection
- **Tenant-Specific Data**: AI uses agent's property inventory, not generic data
- **Dynamic Persona**: "I'm [Agent Name]'s AI Assistant"
- **Property Matching**: Filter by budget, type, location, bedrooms

### 💰 Sales Psychology Techniques
| Technique | Implementation |
|-----------|----------------|
| **Pain & Solution** | Discover pain points → personalized salvation message |
| **FOMO** | Ghost Protocol sends urgency messages |
| **Scarcity** | Show only 3-4 available slots |
| **Price Shock** | ROI PDF shows expected appreciation |

### 📊 Agent Dashboard
- **KPI Cards**: Total leads, conversion rate, revenue
- **Lead Pipeline**: Kanban-style (New → Qualified → Scheduled → Won)
- **Calendar**: Weekly availability scheduler
- **Excel Export**: One-click CRM-ready download
- **ROI PDF**: Branded reports with Golden Visa info

## 📁 Project Structure

```
ArtinSmartRealty/
├── backend/
│   ├── database.py       # Multi-tenant schema with SQLAlchemy
│   ├── brain.py          # AI core with Gemini + sales psychology
│   ├── telegram_bot.py   # Telegram bot interface
│   ├── whatsapp_bot.py   # WhatsApp Business API
│   ├── main.py           # FastAPI + Auth + RBAC
│   ├── roi_engine.py     # PDF generation with price shock
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.jsx             # Login/Register/Forgot Password
│   │   │   ├── Dashboard.jsx         # Agent dashboard
│   │   │   ├── Settings.jsx          # Bot configuration
│   │   │   └── SuperAdminDashboard.jsx # Admin panel
│   │   ├── main.jsx                  # Auth routing
│   │   └── index.css                 # Glassmorphism styles
│   ├── package.json
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── deploy.sh
└── .env.example
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, SQLAlchemy (Async) |
| Database | PostgreSQL 15 with asyncpg |
| AI/ML | Google Gemini 2.0 Flash |
| Telegram | python-telegram-bot |
| WhatsApp | WhatsApp Cloud API (Meta) |
| Frontend | React 18, Vite 5, Tailwind CSS, lucide-react |
| Auth | JWT + PBKDF2 password hashing |
| PDF | ReportLab |
| Excel | openpyxl |
| Deployment | Docker, Nginx |

## 🚦 Quick Start

### Prerequisites
- Docker & Docker Compose
- Google Gemini API Key
- (Optional) Telegram Bot Token
- (Optional) WhatsApp Business API credentials

### 1. Clone & Configure
```bash
git clone https://github.com/arezoojoon/ArtinSmartRealty.git
cd ArtinSmartRealty

# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env
```

### 2. Deploy with Docker
```bash
chmod +x deploy.sh
./deploy.sh prod
```

### 3. Access the Platform
- **Dashboard**: http://localhost (or your domain)
- **Super Admin**: Login with credentials from `.env`
- **API Docs**: http://localhost/docs

## 👑 Super Admin Setup

Default credentials (change in `.env`):
```
Email: admin@artinsmartrealty.com
Password: SuperAdmin123!
```

Super Admin can:
- View all registered agents
- See subscription status and bot configuration
- Access any agent's dashboard
- Monitor platform usage

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account (14-day trial) |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/forgot-password` | Request reset token |
| POST | `/api/auth/reset-password` | Reset password |
| GET | `/api/auth/me` | Get current user |

### Tenants (Protected)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/tenants` | Super Admin | List all tenants |
| GET | `/api/tenants/{id}` | Owner/Admin | Get tenant details |
| PUT | `/api/tenants/{id}` | Owner/Admin | Update settings |

### Leads (Protected)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tenants/{id}/leads` | List leads (with filters) |
| PUT | `/api/tenants/{id}/leads/{lead_id}` | Update lead |
| GET | `/api/tenants/{id}/leads/export` | Export to Excel |
| GET | `/api/tenants/{id}/leads/{lead_id}/roi-pdf` | Generate ROI PDF |

### Tenant Data (Protected)
| Method | Endpoint | Description |
|--------|----------|-------------|
| CRUD | `/api/tenants/{id}/properties` | Agent's property inventory |
| CRUD | `/api/tenants/{id}/projects` | Off-plan projects |
| CRUD | `/api/tenants/{id}/knowledge` | FAQ/Knowledge base |

### Scheduling (Protected)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tenants/{id}/schedule` | List availability |
| POST | `/api/tenants/{id}/schedule` | Add slot |
| DELETE | `/api/tenants/{id}/schedule/{slot_id}` | Remove slot |

### Webhooks (Public)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook/telegram/{bot_token}` | Telegram webhook |
| GET | `/webhook/whatsapp` | WhatsApp verification |
| POST | `/webhook/whatsapp` | WhatsApp messages |

## 🤖 Lead Qualification Flow

```
START
  │
  ▼
WELCOME → "Hello! I'm [Agent]'s AI Assistant"
  │
  ▼
HOOK → "Get FREE ROI Analysis!" [Yes/No]
  │
  ▼
PHONE_GATE → "Share your phone number" (REQUIRED)
  │
  ▼
PAIN_DISCOVERY → "What's driving your interest?"
  • Currency protection (inflation)
  • Family residency (visa)
  • Passive income (rental)
  • Tax-free benefits
  │
  ▼
TRANSACTION_TYPE → [Buy / Rent]
  │
  ▼
PROPERTY_TYPE → [Apartment / Villa / Penthouse / Townhouse / Commercial / Land]
  │
  ▼
BUDGET → [Under 500K / 500K-1M / 1M-2M / 2M-5M / 5M+]
  │
  ▼
PAYMENT_METHOD → [Cash / Installment]
  │
  ▼
PURPOSE → [Investment / Living / Residency (Golden Visa)]
  │
  ▼
SOLUTION_BRIDGE → Personalized message + property recommendations
  │
  ▼
SCHEDULE → "🔥 Only 4 slots remaining!" (Scarcity)
  │
  ▼
COMPLETED → Confirmation + appointment details
```

## 🎨 Dashboard Theme

Luxury dark glassmorphism theme:
- **Background**: Deep Navy Blue (#0f1729)
- **Cards**: Glass effect with backdrop-blur
- **Accents**: Metallic Gold (#D4AF37)
- **Icons**: lucide-react

## 🔒 Security

| Feature | Implementation |
|---------|----------------|
| Password Hashing | PBKDF2 with 100,000 iterations |
| Authentication | JWT tokens (24h expiry) |
| Authorization | Role-based access control |
| API Protection | All endpoints require auth (except webhooks) |
| CORS | Environment-configurable origins |

## 📊 Database Schema

### Core Tables
- **Tenants**: Agent profiles, credentials, bot tokens, subscription
- **Leads**: Contact info, qualification data, psychology tracking
- **AgentAvailability**: Time slots for scheduling
- **Appointments**: Booked meetings

### Tenant Data Tables
- **TenantProperty**: Property inventory (name, price, ROI, Golden Visa)
- **TenantProject**: Off-plan projects with payment plans
- **TenantKnowledge**: FAQ and custom responses

## 🔄 Background Jobs

| Job | Trigger | Action |
|-----|---------|--------|
| Ghost Protocol | 2h no response | Send FOMO message |
| Appointment Reminders | 24h before | Notify agent + client |

## 🚀 Deployment Checklist

Before going live:

1. **Environment Variables** (`.env`):
   - [ ] `DB_PASSWORD` - Strong database password
   - [ ] `GEMINI_API_KEY` - Google AI API key
   - [ ] `JWT_SECRET` - Random 64+ character string
   - [ ] `PASSWORD_SALT` - Random 32+ character string
   - [ ] `SUPER_ADMIN_PASSWORD` - Change from default!
   - [ ] `CORS_ORIGINS` - Your domain only

2. **SSL/HTTPS**: Configure in nginx or use Cloudflare

3. **Telegram Bot Setup**:
   - Create bot via [@BotFather](https://t.me/BotFather)
   - Set webhook: `https://yourdomain.com/webhook/telegram/{token}`

4. **WhatsApp Setup**:
   - Create WhatsApp Business Account in [Meta Business Manager](https://business.facebook.com/)
   - Configure webhook: `https://yourdomain.com/webhook/whatsapp`

## 📝 License

MIT License

## 🤝 Support

For issues and feature requests, please open a GitHub issue.

---

Built with ❤️ for Dubai Real Estate Professionals