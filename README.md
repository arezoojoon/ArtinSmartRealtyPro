# ArtinSmartRealty V2 - Commercial SaaS Edition

A high-end, multi-tenant Real Estate SaaS platform built with Python (FastAPI), PostgreSQL (Async), React (Vite + Tailwind), and Docker.

![Dashboard Preview](https://ui-avatars.com/api/?name=Dashboard&background=0f1729&color=D4AF37&size=128)

## 🚀 Features

### Core Platform
- **Multi-Tenant Architecture**: Strict data isolation for each real estate agent
- **Intelligent Lead Capture**: Automated qualification flow via Telegram
- **Multi-Language Support**: EN, FA (Persian), AR (Arabic), RU (Russian)
- **Voice Intelligence**: Process voice messages with AI transcription
- **Native Scheduling**: Built-in appointment scheduling with conflict detection

### AI-Powered Features
- **Google Gemini 2.0 Flash Integration**: Smart entity extraction, language detection
- **Turbo Qualification Flow**: Button-based lead qualification (no typing required)
- **ROI Analysis Engine**: Generate branded PDF reports with ROI projections
- **Ghost Protocol**: Auto-follow-up with inactive leads after 2 hours

### Dashboard
- **Modern Dark Theme**: Luxury aesthetics with Navy Blue and Gold accents
- **Lead Pipeline**: Kanban-style view with drag-and-drop
- **Visual Calendar**: Weekly availability scheduler
- **Excel Export**: One-click CRM-ready data export

## 📁 Project Structure

```
ArtinSmartRealty/
├── backend/
│   ├── database.py       # Multi-tenant schema with SQLAlchemy
│   ├── brain.py          # AI core with Gemini integration
│   ├── telegram_bot.py   # Telegram interface
│   ├── main.py           # FastAPI application
│   ├── roi_engine.py     # PDF generation engine
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── Dashboard.jsx  # Main dashboard component
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
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
| Bot | python-telegram-bot |
| Frontend | React 18, Vite 5, Tailwind CSS |
| PDF | ReportLab |
| Excel | openpyxl |
| Deployment | Docker, Nginx |

## 🚦 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)
- Google Gemini API Key
- Telegram Bot Token

### 1. Clone & Configure
```bash
git clone https://github.com/your-repo/ArtinSmartRealty.git
cd ArtinSmartRealty

# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env
```

### 2. Deploy with Docker
```bash
# Make deploy script executable
chmod +x deploy.sh

# Start production
./deploy.sh prod

# Or start development (database only)
./deploy.sh dev
```

### 3. Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📡 API Endpoints

### Tenants
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tenants` | Create new tenant (agent) |
| GET | `/api/tenants` | List all tenants |
| GET | `/api/tenants/{id}` | Get tenant details |

### Leads
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tenants/{id}/leads` | List leads (with filters) |
| GET | `/api/tenants/{id}/leads/export` | Export to Excel |
| GET | `/api/tenants/{id}/leads/{lead_id}/roi-pdf` | Generate ROI PDF |

### Scheduling
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tenants/{id}/schedule` | Add availability slot |
| GET | `/api/tenants/{id}/schedule` | List availability |
| DELETE | `/api/tenants/{id}/schedule/{slot_id}` | Remove slot |

### Appointments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tenants/{id}/appointments` | Create appointment |
| GET | `/api/tenants/{id}/appointments` | List appointments |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tenants/{id}/dashboard/stats` | Get KPI statistics |

### Telegram Webhook
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook/telegram/{bot_token}` | Telegram webhook handler |

## 🤖 Telegram Bot Flow

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
TRANSACTION_TYPE → [Buy / Rent]
  │
  ▼
PROPERTY_TYPE → [Residential / Commercial]
  │
  ▼
BUDGET → [Under 500K / 500K-1M / 1M-2M / 2M-5M / 5M+]
  │
  ▼
PAYMENT_METHOD → [Cash / Installment]
  │
  ▼
PURPOSE → [Investment / Living / Residency]
  │
  ▼
SCHEDULE → Pick available slot
  │
  ▼
COMPLETED → Confirmation message
```

## 🎨 Dashboard Theme

The dashboard uses a luxury dark theme:
- **Background**: Deep Navy Blue (#0f1729)
- **Cards**: Glassmorphism effect with transparency
- **Accents**: Metallic Gold (#D4AF37)
- **Text**: White and soft gray

## 🔒 Security Considerations

1. Use strong passwords for database
2. Keep API keys in environment variables
3. Enable HTTPS in production
4. Implement rate limiting (configured in nginx.conf)
5. Regular dependency updates

## 📊 Database Schema

### Tables
- **Tenants**: Agent profiles, bot tokens, settings
- **Leads**: Contact info, qualification data, voice transcripts
- **AgentAvailability**: Time slots for scheduling
- **Appointments**: Booked meetings with leads

## 🔄 Background Jobs

| Job | Frequency | Description |
|-----|-----------|-------------|
| Ghost Protocol | Every hour | Send follow-up to inactive leads (2h threshold) |
| Appointment Reminders | Every hour | Send 24h reminder to upcoming appointments |

## 📝 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

Built with ❤️ for Dubai Real Estate Professionals