# ArtinSmartRealty V2 - AI Agent Instructions

## Project Overview
Multi-tenant SaaS platform providing AI-powered real estate assistants for agents. Each tenant gets dedicated Telegram/WhatsApp bots that qualify leads 24/7, using Google Gemini 2.0 Flash for conversational AI. Persian (Farsi), English, Arabic, and Russian supported.

## Architecture

### Multi-Tenant Isolation (CRITICAL)
- **Strict data separation**: EVERY database query MUST filter by `tenant_id`
- Each tenant has separate: bot tokens, leads, properties, knowledge base, scheduling slots
- Never cross-contaminate tenant data - use `get_tenant_by_bot_token()` or `get_tenant_by_whatsapp_phone_id()`
- Super Admin role can impersonate tenants via `ImpersonationBar.jsx`

### Core Components
```
backend/
├── brain.py              # AI conversation engine (Gemini API + sales psychology)
├── telegram_bot.py       # Telegram interface - delegates ALL logic to brain.py
├── whatsapp_bot.py       # WhatsApp interface - uses whatsapp_providers.py
├── database.py           # SQLAlchemy async models (1048 lines)
├── main.py               # FastAPI app + JWT auth + scheduling
├── roi_engine.py         # PDF report generation with ReportLab
├── redis_manager.py      # Session persistence (24h TTL)
├── vertical_router.py    # Multi-vertical routing (realty/expo/support)
├── feature_flags.py      # Per-tenant feature access control
└── api/                  # APIRouter modules (broadcast, catalogs, lotteries, admin)

frontend/src/
├── components/Dashboard.jsx        # Agent KPI cards + lead pipeline
├── components/Settings.jsx         # Bot config + API keys
├── components/SuperAdminDashboard.jsx  # Platform admin panel
└── main.jsx                        # Auth routing + impersonation state
```

### Data Flow Pattern
1. User message → `telegram_bot.py` or `whatsapp_bot.py`
2. Bot retrieves/creates `Lead` object from database
3. Recovers context from Redis if available (`context_recovery.py`)
4. Calls `brain.py` → `generate_ai_response()` with lead state
5. Brain returns `BrainResponse` with message, buttons, metadata
6. Bot sends response via platform API
7. Saves updated state to PostgreSQL + Redis

### Conversation State Machine
All AI logic lives in `brain.py`. States stored in `Lead.conversation_state`:
- `start` → Language selection
- `collecting_name` → Parse "Name – +971XXXXXXXXX" format
- `transaction_type` → Buy/Rent
- `budget`, `property_type`, `bedrooms`, `location`, `payment_method`, `purpose`
- `show_recommendations` → Filter properties by tenant + lead criteria
- `booking_slot` → Schedule appointment from `AgentAvailability`

**ENUM VALUES**: All enums (Language, ConversationState, LeadStatus, PropertyType, etc.) use **lowercase** values in database (e.g., `"en"`, `"new"`, `"apartment"`). Migration scripts in `backend/migrate_enums_*.py`.

## Development Workflows

### Local Development
```powershell
# Backend (requires Python 3.11+)
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev  # Vite dev server on port 3000
```

### Docker Deployment
```bash
docker-compose up -d  # All services (db, redis, backend, frontend, nginx)
docker-compose logs -f backend  # Tail logs
docker-compose build --no-cache backend  # Rebuild after code changes
```

**CRITICAL**: After enum schema changes, run migration BEFORE restarting:
```bash
docker-compose run --rm backend python migrate_enums_to_lowercase.py
```

### Testing
- Stress tests: `backend/tests/stress_test.py` (creates test tenants + leads)
- No pytest/unittest framework - uses custom async test functions
- Manual testing via `/set_admin` command in Telegram bots

## Key Conventions

### Database Patterns
- **Async-only**: Use `async with async_session() as session:` everywhere
- **Soft enums**: Python `Enum` classes map to VARCHAR columns, not native ENUM types
- **Helper functions**: Prefer `get_available_slots()`, `book_slot()`, `update_lead()` over raw SQL
- **Tenant context injection**: `get_tenant_context_for_ai(tenant_id)` fetches custom knowledge for RAG

### AI Response Structure
`brain.py` returns `BrainResponse` objects:
```python
BrainResponse(
    message="User-facing text (translated)",
    buttons=[{"text": "English", "callback": "lang_en"}],
    next_state=ConversationState.COLLECTING_NAME,
    metadata={"notify_admin": True, "trigger_ghost": False}
)
```

### WhatsApp Button Adaptation
- Telegram: Unlimited inline buttons
- WhatsApp: Max 3 reply buttons OR 10 list items
- `whatsapp_providers.py` auto-converts based on button count
- Both use SAME brain.py responses

### Translation Pattern
All user-facing strings in `brain.py` use:
```python
TRANSLATIONS = {
    "key_name": {
        Language.EN: "English text",
        Language.FA: "متن فارسی",  # Right-to-left
        Language.AR: "النص العربي",
        Language.RU: "Русский текст"
    }
}
```
Then: `get_translation("key_name", lead.language)`

### Redis Session Keys
- Context: `bot:session:{tenant_id}:{telegram_id}` (24h TTL)
- Timeouts: `bot:timeout:{tenant_id}:{telegram_id}`
- Vertical mode: `user:{whatsapp_phone}:mode` (expo/realty/support)

### PDF Generation
`roi_engine.py` uses ReportLab:
- Branded with tenant logo + primary color
- Persian/Arabic requires Bidi text handling (external library NOT used - pre-reverse strings)
- Generated in Docker volume: `/app/pdf_reports`

## Sales Psychology Features (CRITICAL to preserve)

### 1. Hot Lead Alert
When user shares phone → instant Telegram notification to `tenant.admin_chat_id`. Setup: `/set_admin` command.

### 2. Ghost Protocol
Background task re-engages stale leads with FOMO messages (14h, 24h, 48h delays). See `_ghost_protocol_loop()` in `telegram_bot.py`.

### 3. Scarcity Messaging
Show max 3-4 properties with "⚠️ Only X units left!" dynamically injected.

### 4. Morning Coffee Report
Daily digest to admin at 8:00 AM Dubai time with conversion metrics. Scheduler in `main.py` using APScheduler.

## External Dependencies

### Required Services
- **PostgreSQL 15**: Multi-tenant database (strict isolation via `tenant_id`)
- **Redis 7**: Session persistence + vertical routing state
- **Google Gemini API**: `GEMINI_API_KEY` env var (free tier: 15 RPM)
- **Telegram Bot API**: Each tenant stores `telegram_bot_token`
- **WhatsApp Cloud API** (optional): Meta Business API credentials in tenant table

### Environment Variables
See `.env.example`. NEVER commit `.env`. Critical:
- `JWT_SECRET` (64+ chars) - Token signing
- `PASSWORD_SALT` (32+ chars) - PBKDF2 hashing (100k iterations)
- `GEMINI_API_KEY` - AI brain
- `DATABASE_URL` - Async PostgreSQL connection string
- `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_PASSWORD` - Platform owner credentials

## Common Pitfalls

### 1. Enum Case Mismatch
Database uses lowercase (`"en"`, `"new"`). Python Enum values also lowercase. NEVER use `.name` (gives uppercase).
```python
# WRONG
lead.language = Language.EN.name  # "EN" - breaks DB constraint

# CORRECT
lead.language = Language.EN  # "en" - implicit .value
```

### 2. Tenant Isolation Breach
```python
# WRONG - returns leads from ALL tenants
leads = await session.execute(select(Lead))

# CORRECT
leads = await session.execute(
    select(Lead).where(Lead.tenant_id == tenant_id)
)
```

### 3. Redis Unavailable
Always check `redis_manager.redis_client` before use. Bot works without Redis (degrades to DB-only state).

### 4. WhatsApp Verify Token vs Access Token
- `WHATSAPP_VERIFY_TOKEN` in `.env` (webhook registration only)
- `tenant.whatsapp_access_token` in database (actual API calls - long "EAAT..." token)

### 5. Deployment Without Migration
After enum changes, ALWAYS run migration script before `docker-compose up`:
```bash
docker-compose run --rm backend python migrate_enums_to_lowercase.py
docker-compose build --no-cache backend
docker-compose up -d
```

## Key Files for Context

- `README.md` - Product overview + quick start
- `DEPLOYMENT_GUIDE.md` - VPS deployment steps (commit-specific)
- `RAG_IMPLEMENTATION_GUIDE.md` - Knowledge base retrieval system
- `HIGH_VELOCITY_SALES_FEATURES.md` - Hot lead alert + ghost protocol
- `MULTI_VERTICAL_ROUTING_GUIDE.md` - Expo/realty routing via deep links
- `docker-compose.yml` - Service orchestration (db, redis, backend, frontend, nginx)

## API Patterns

### Authentication
JWT bearer tokens via `HTTPBearer()`. Use `get_current_tenant()` dependency:
```python
@router.get("/api/tenants/{tenant_id}/leads")
async def get_leads(tenant_id: int, current_tenant: Tenant = Depends(get_current_tenant)):
    if current_tenant.id != tenant_id and not current_tenant.is_super_admin:
        raise HTTPException(403, "Forbidden")
```

### APIRouter Modules
Separated in `backend/api/`:
- `broadcast.py` - Bulk messaging to leads
- `catalogs.py` - Property/project management
- `lotteries.py` - Expo/event lotteries
- `admin.py` - Super admin operations

Mounted in `main.py`: `app.include_router(broadcast.router)`

### Webhook Handling
- Telegram: `/webhook/telegram/{bot_token}` (POST)
- WhatsApp: `/webhook/whatsapp` (GET for verification, POST for messages)
- Verify token: `WHATSAPP_VERIFY_TOKEN` matches `hub.verify_token`

## Feature Flags System
Per-tenant feature access via `TenantFeature` table:
```python
from feature_flags import has_feature, require_feature
from database import FeatureFlag

if await has_feature(tenant_id, FeatureFlag.RAG_SYSTEM):
    knowledge = await get_tenant_context_for_ai(tenant_id, "golden visa")

# Or enforce:
await require_feature(tenant_id, FeatureFlag.VOICE_AI)  # Raises 403 if disabled
```

## When Editing Files

- **brain.py**: Add sales psychology, not generic AI. Inject urgency/scarcity. Translations required for all strings.
- **database.py**: Always use async session. Add tenant_id foreign key. Index frequently queried columns.
- **telegram_bot.py**: Pure interface layer - NO business logic. Delegate to brain.py. Handle button callbacks via `inline_keyboards.py`.
- **whatsapp_bot.py**: Check `whatsapp_providers.py` for Meta vs Twilio detection. Adapt buttons via provider.
- **main.py**: Use Pydantic models. Add CORS origins. Background tasks via APScheduler (not asyncio.create_task for scheduled jobs).
- **Frontend components**: Use Mantine UI + Tailwind. Zustand for state. API calls via axios with JWT header.

---

*Last updated: December 2025 - Reflects codebase at commit 8327f00 (working lowercase enum state)*
