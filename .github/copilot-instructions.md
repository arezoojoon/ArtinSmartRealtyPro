# ArtinRealtySmartPro - AI Agent Instructions

## Project Overview
This is a **unified platform** combining two distinct systems:
1. **ArtinSmartRealty** - Multi-tenant SaaS for real estate agencies with AI-powered Telegram/WhatsApp bots (Google Gemini 2.0)
2. **AI Lead Scraper & Personalizer** - Chrome extension that scrapes LinkedIn profiles and generates personalized messages via Gemini API

Both systems integrate through the `unified_leads` database for seamless lead flow: LinkedIn → Bot Follow-up → Property Matching.

## Repository Structure
```
ArtinSmartRealty/          # Main SaaS platform (FastAPI + React)
├── backend/               # Python backend with AI brain
├── frontend/              # React dashboard with glassmorphism UI
├── docker-compose.yml     # Full stack deployment
└── .github/copilot-instructions.md  # Tenant-specific conventions

AI Lead Scraper & Personalize/  # Chrome extension (Manifest V3)
├── content.js             # LinkedIn DOM scraper
├── background.js          # Service worker with rate limiting
├── sidepanel.js           # Main UI
├── backend/               # Python FastAPI middleware for Gemini
└── .github/copilot-instructions.md  # Extension-specific conventions
```

## Critical Architecture Principles

### 1. Multi-Tenant Isolation (ABSOLUTE REQUIREMENT)
**EVERY database query in ArtinSmartRealty MUST filter by `tenant_id`**. This is not optional - it's a security boundary.

```python
# ❌ WRONG - Violates tenant isolation
leads = await session.execute(select(Lead))

# ✅ CORRECT - Strict tenant filtering
leads = await session.execute(
    select(Lead).where(Lead.tenant_id == tenant_id)
)
```

**Helper functions for tenant lookup:**
- `get_tenant_by_bot_token(telegram_bot_token)` - Telegram bots
- `get_tenant_by_whatsapp_phone_id(phone_number_id)` - WhatsApp Cloud API
- Tenants stored in database with separate: bot tokens, properties, knowledge base, scheduling slots

### 2. Brain-Centered AI Pattern
**ALL conversation logic lives in `brain.py`** - bot interfaces (`telegram_bot.py`, `whatsapp_bot.py`) are thin wrappers that ONLY handle platform APIs.

**Data flow:**
1. User message → Bot interface receives it
2. Bot retrieves/creates `Lead` from database
3. Recovers context from Redis (`context_recovery.py`)
4. Calls `brain.generate_ai_response(lead, message, tenant)` 
5. Brain returns `BrainResponse(message, buttons, next_state, metadata)`
6. Bot sends response via platform API
7. Saves state to PostgreSQL + Redis

**Never implement conversation logic in bot files** - always extend `brain.py` instead.

### 3. Enum Convention (Critical to Avoid Bugs)
Database uses **lowercase string values** for all enums - Python `Enum` classes map to VARCHAR columns.

```python
# ❌ WRONG - .name gives uppercase
lead.language = Language.EN.name  # "EN" - breaks DB constraint!

# ✅ CORRECT - Implicit .value (lowercase)
lead.language = Language.EN  # "en"
lead.status = LeadStatus.QUALIFIED  # "qualified"
```

**After enum schema changes, ALWAYS run migration before restart:**
```bash
docker-compose run --rm backend python migrate_enums_to_lowercase.py
```

### 4. Async Database Pattern
Use `async with async_session() as session:` everywhere. No synchronous DB calls.

```python
from database import async_session, select, Lead

async def get_leads(tenant_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Lead).where(Lead.tenant_id == tenant_id)
        )
        return result.scalars().all()
```

### 5. Translation System
All user-facing strings use the `TRANSLATIONS` dict in `brain.py`:

```python
TRANSLATIONS = {
    "key_name": {
        Language.EN: "English text",
        Language.FA: "متن فارسی",  # Persian (right-to-left)
        Language.AR: "النص العربي",  # Arabic
        Language.RU: "Русский текст"
    }
}
# Usage: get_translation("key_name", lead.language)
```

### 6. LinkedIn Extension Anti-Detection
Chrome extension uses **humanized delays** and **multiple CSS fallbacks** because LinkedIn constantly changes DOM structure.

```javascript
// ALWAYS use CONFIG.DELAYS - never hardcode setTimeout values
await humanDelay(CONFIG.DELAYS.MIN, CONFIG.DELAYS.MAX);  // 500-1500ms random

// Multiple selector fallbacks (LinkedIn changes classes weekly)
const name = document.querySelector('h1.text-heading-xlarge') ||
             document.querySelector('[data-anonymize="person-name"]') ||
             document.querySelector('.pv-text-details__left-panel h1');
```

## Development Workflows

### Running ArtinSmartRealty (Docker - Recommended)
```powershell
cd ArtinSmartRealty
docker-compose up -d  # Starts db, redis, backend, frontend, nginx, waha
docker-compose logs -f backend  # Tail logs
docker-compose build --no-cache backend  # Rebuild after code changes
```

### Running ArtinSmartRealty (Local Development)
```powershell
# Backend (Python 3.11+)
cd ArtinSmartRealty/backend
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (Node 18+)
cd ArtinSmartRealty/frontend
npm install; npm run dev  # Vite dev server on port 3000
```

### Running Lead Scraper Extension
```powershell
# Backend
cd "AI Lead Scraper & Personalize/backend"
.\venv\Scripts\Activate.ps1
python main.py  # Runs on http://localhost:8000

# Extension: Load unpacked in chrome://extensions/
# Navigate to LinkedIn profile → Click purple floating button
```

### Testing
```powershell
# ArtinSmartRealty stress test (creates test tenants + leads)
docker-compose run --rm backend python backend/tests/stress_test.py

# Lead Scraper: Manual testing via Chrome extension on LinkedIn profiles
```

## Key Files & Responsibilities

### ArtinSmartRealty Backend (`ArtinSmartRealty/backend/`)
| File | Purpose | Critical Notes |
|------|---------|----------------|
| `brain.py` | AI conversation engine | 4387 lines - ALL sales logic lives here |
| `database.py` | SQLAlchemy async models | 1096 lines - multi-tenant schema |
| `main.py` | FastAPI app + JWT auth | 2800 lines - uses APScheduler for daily reports |
| `telegram_bot.py` | Telegram interface | Thin wrapper - delegates to `brain.py` |
| `whatsapp_bot.py` | WhatsApp interface | Uses `whatsapp_providers.py` for WAHA/Twilio |
| `followup_engine.py` | Auto follow-up system | Processes leads every hour with `FOR UPDATE SKIP LOCKED` |
| `redis_manager.py` | Session persistence | 24h TTL - bot works without Redis (degrades to DB-only) |
| `roi_engine.py` | PDF report generation | ReportLab - branded with tenant logo |
| `vertical_router.py` | Multi-vertical routing | Routes WhatsApp messages to realty/expo/support |

### Lead Scraper Files (`AI Lead Scraper & Personalize/`)
| File | Purpose | Lines | Critical Notes |
|------|---------|-------|----------------|
| `content.js` | LinkedIn DOM scraper | 324 | Injects floating button, extracts profile data |
| `background.js` | Service worker | 108 | Handles API calls, **MUST return true in async handlers** |
| `sidepanel.js` | Main UI logic | 260+ | Profile display, message generation, CRM save |
| `backend/main.py` | FastAPI middleware | 429 | Gemini API calls with PAS framework prompting |
| `backend/database.py` | SQLite CRM | 313 | Auto-save, Excel export, duplicate detection |

## Environment Variables

### ArtinSmartRealty (`.env` in project root)
```dotenv
# CRITICAL - Generate with: openssl rand -base64 64
JWT_SECRET=<64+ chars>
PASSWORD_SALT=<32+ chars>  # PBKDF2 with 600k iterations

# Google Gemini API (FREE tier: 15 RPM)
GEMINI_API_KEY=<your_key>

# Database (defaults to Docker setup)
DB_PASSWORD=<secure_password>
DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@db:5432/artinrealty

# Super Admin (platform owner)
SUPER_ADMIN_EMAIL=admin@artinsmartrealty.com
SUPER_ADMIN_PASSWORD=<change_in_production>

# WhatsApp (two different tokens!)
WHATSAPP_VERIFY_TOKEN=<simple_string>  # For webhook registration only
# Note: Access token (EAAT... ~200 chars) stored in database, NOT .env
```

### Lead Scraper (`backend/.env`)
```dotenv
GEMINI_API_KEY=<your_key>  # Same FREE Google Gemini key
```

## Common Pitfalls & Solutions

### 1. Tenant Data Leakage
```python
# ❌ Query without tenant filter exposes all tenants' data
properties = await session.execute(select(TenantProperty))

# ✅ Always filter by tenant_id
properties = await session.execute(
    select(TenantProperty).where(TenantProperty.tenant_id == tenant_id)
)
```

### 2. Manifest V3 Async Message Handler
```javascript
// ❌ Message channel closes before async work finishes
chrome.runtime.onMessage.addListener(async (message, sender, sendResponse) => {
    const result = await fetch(...);
    sendResponse(result);  // Never reaches caller!
});

// ✅ MUST return true to keep channel open
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    handleMessageAsync(message).then(sendResponse);
    return true;  // Critical - keeps channel alive!
});
```

### 3. Redis Unavailable
Always check `redis_manager.redis_client` before use. Bot degrades gracefully to DB-only state without Redis.

```python
if redis_manager.redis_client:
    await save_context_to_redis(tenant_id, user_id, context)
else:
    logger.warning("Redis unavailable - using DB-only mode")
```

### 4. WhatsApp Token Confusion
- `WHATSAPP_VERIFY_TOKEN` (in `.env`) - Simple string for webhook registration
- `tenant.whatsapp_access_token` (in database) - Long "EAAT..." token (~200 chars) for API calls

### 5. LinkedIn Scraping Breaks
If extraction fails, check CSS selectors in `content.js` functions:
- `extractName()` - 4 fallback selectors
- `extractAbout()` - 3 fallback selectors
- `extractRecentPosts()` - Requires scrolling first (lazy-loaded content)

## Sales Psychology Features (Preserve These!)

### Ghost Protocol
Background task in `telegram_bot.py` re-engages stale leads with FOMO messages at 14h, 24h, 48h intervals. Uses scarcity messaging: "Only 3 units left at pre-launch prices!"

### Hot Lead Alert
When user shares phone number → instant Telegram notification to `tenant.admin_chat_id`. Setup via `/set_admin` command in bot.

### Morning Coffee Report
Daily digest at 8:00 AM Dubai time with conversion metrics. Scheduler in `main.py` using APScheduler.

## Security Best Practices

### Input Sanitization
```python
from input_sanitizer import sanitize_text, sanitize_email, sanitize_phone

# Always sanitize user input before database storage
name = sanitize_text(raw_name, max_length=255)
email = sanitize_email(raw_email)
phone = sanitize_phone(raw_phone)
```

### XSS Prevention (Frontend)
```javascript
// ❌ NEVER use innerHTML with user data
element.innerHTML = userInput;

// ✅ Use textContent or escape HTML
element.textContent = userInput;
// OR
element.innerHTML = userInput.replace(/</g, '&lt;').replace(/>/g, '&gt;');
```

### Password Hashing
Uses PBKDF2-SHA256 with 600,000 iterations (OWASP 2023 recommendation). Constant-time comparison via `secrets.compare_digest()` prevents timing attacks.

## Deployment Commands

```bash
# Full production deployment
cd ArtinSmartRealty
./DEPLOY_TO_PRODUCTION.sh

# Quick deploy (just rebuild backend)
docker-compose build --no-cache backend
docker-compose up -d backend

# Run migrations (after schema changes)
docker-compose run --rm backend alembic upgrade head

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Export leads to Excel
curl http://localhost:8000/api/export-excel -H "Authorization: Bearer <token>"
```

## External Dependencies

- **PostgreSQL 15** - Multi-tenant database with strict `tenant_id` isolation
- **Redis 7** - Session persistence + vertical routing (optional - degrades gracefully)
- **Google Gemini API** - `gemini-2.0-flash-exp` model (FREE tier: 15 requests/min)
- **Telegram Bot API** - Each tenant stores `telegram_bot_token`
- **WhatsApp** - WAHA (self-hosted, unlimited) OR Meta Cloud API (requires approval)
- **WAHA** - Self-hosted WhatsApp API (devlikeapro/waha Docker image)

## Branding & Naming
- **Platform**: ArtinSmartRealty Pro (NOT "ArtinRealtySmartPro")
- **Extension**: Artin Lead Scraper & Personalizer (NOT "AI Lead Scraper")
- **Developer**: Arezoo Mohammadzadegan
- **Company**: ArtinSmartAgent
- **Contact**: info@artinsmartagent.com | www.artinsmartagent.com
