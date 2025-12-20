# 🚀 Deployment Commands - ArtinSmartRealty Platform
**Last Updated**: 2024-01-15

---

## ✅ Critical Bugs Fixed (Ready to Deploy)

### Bug Fixes Applied:
1. ✅ **Missing Dependencies** - Added `aiohttp` and `pydub`
2. ✅ **Regex Timeout** - Removed invalid timeout parameter  
3. ✅ **WhatsApp Integration** - Router V3 headers integrated
4. ✅ **Telegram Bot** - Budget, rent detection, duplicate loop fixed

---

## 🐳 Docker Deployment (Recommended)

### Step 1: Rebuild Backend with Fixed Dependencies
```powershell
cd I:\ArtinRealtySmartPro\ArtinSmartRealty

# Rebuild backend container (includes aiohttp + pydub fixes)
docker-compose build --no-cache backend

# Rebuild router V3 container
docker-compose build --no-cache router
```

### Step 2: Start All Services
```powershell
# Start database and Redis first
docker-compose up -d db redis

# Wait 10 seconds for database to initialize
Start-Sleep -Seconds 10

# Start backend (will run migrations automatically)
docker-compose up -d backend

# Start router V3
docker-compose up -d router

# Start WAHA (WhatsApp API)
docker-compose up -d waha

# Start frontend
docker-compose up -d frontend

# Start nginx reverse proxy
docker-compose up -d nginx
```

### Step 3: Verify All Services Running
```powershell
# Check service status
docker-compose ps

# Should show:
# - db (PostgreSQL) - healthy
# - redis - healthy
# - backend - healthy
# - router - healthy
# - waha - healthy
# - frontend - healthy
# - nginx - healthy

# View logs
docker-compose logs -f backend
docker-compose logs -f router
```

### Step 4: Test Health Endpoints
```powershell
# Backend health
curl http://localhost:8000/health

# Router health
curl http://localhost:8001/health

# Frontend (should return HTML)
curl http://localhost:3000

# WAHA health
curl http://localhost:3001/api/health
```

---

## 🧪 Testing WhatsApp Deep Link Flow

### Configure WAHA Webhook to Router
```powershell
# Set WAHA to forward messages to router
curl -X POST http://localhost:3001/api/sessions/default/webhooks `
  -H "Content-Type: application/json" `
  -d '{
    "url": "http://router:8001/webhook/waha",
    "events": ["message"]
  }'

# Verify webhook configured
curl http://localhost:3001/api/sessions/default/webhooks
```

### Generate QR Code for WAHA Session
```powershell
# Get QR code to connect WhatsApp
curl http://localhost:3001/api/sessions/default/auth/qr
# Scan QR with WhatsApp on your phone
```

### Test 1: Deep Link Creation
```powershell
# Generate deep link via router API
curl -X POST http://localhost:8001/router/generate-link `
  -H "Content-Type: application/json" `
  -d '{
    "tenant_id": 1,
    "vertical": "realty",
    "gateway_number": "971557357753",
    "custom_message": ""
  }'

# Output will include:
# - deep_link: wa.me/971557357753?text=start_realty_1
# - qr_code_base64: (image data)
```

### Test 2: Simulate User Clicking Link
```powershell
# Send test message to router (simulates WAHA webhook)
curl -X POST http://localhost:8001/webhook/waha `
  -H "Content-Type: application/json" `
  -d '{
    "event": "message",
    "session": "default",
    "payload": {
      "from": "971501234567@c.us",
      "body": "start_realty_1",
      "hasMedia": false
    }
  }'

# Check router logs
docker-compose logs router | Select-String "Deep link detected"
# Should see: "🔗 Deep link detected: vertical=realty, tenant=1"

# Check backend logs
docker-compose logs backend | Select-String "X-Tenant-ID"
# Should see: "🔀 Routed message for Tenant 1"
```

### Test 3: Verify Session in Redis
```powershell
# Connect to Redis
docker-compose exec redis redis-cli -n 1

# Check router session
redis> GET whatsapp_session:971501234567@c.us
# Should return JSON: {"tenant_id":"1","vertical":"realty",...}

# Check vertical mode (backend)
redis> SELECT 0
redis> GET user:971501234567@c.us:mode
# Should return: "realty"

# Check TTL
redis> TTL whatsapp_session:971501234567@c.us
# Should return: ~86400 (24 hours)
```

### Test 4: Personal Message Filtering
```powershell
# Send message without deep link
curl -X POST http://localhost:8001/webhook/waha `
  -H "Content-Type: application/json" `
  -d '{
    "event": "message",
    "session": "default",
    "payload": {
      "from": "971509876543@c.us",
      "body": "سلام کجایی؟",
      "hasMedia": false
    }
  }'

# Check router logs
docker-compose logs router | Select-String "PERSONAL MESSAGE"
# Should see: "👤 PERSONAL MESSAGE (ignored)"
```

### Test 5: Session Continuation
```powershell
# After deep link (Test 2), send follow-up message
curl -X POST http://localhost:8001/webhook/waha `
  -H "Content-Type: application/json" `
  -d '{
    "event": "message",
    "session": "default",
    "payload": {
      "from": "971501234567@c.us",
      "body": "میخوام ملک ببینم",
      "hasMedia": false
    }
  }'

# Check router logs
docker-compose logs router | Select-String "Session found"
# Should see: "📂 ACTIVE SESSION: 971501234567 → Tenant 1 (realty)"
```

---

## 📊 Monitoring Commands

### View Real-Time Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f router
docker-compose logs -f waha

# Filter by keyword
docker-compose logs backend | Select-String "ERROR"
docker-compose logs router | Select-String "Deep link"
```

### Check Service Health
```powershell
# Backend stats
curl http://localhost:8000/health | ConvertFrom-Json

# Router stats
curl http://localhost:8001/router/stats | ConvertFrom-Json

# Container resource usage
docker stats --no-stream
```

### Database Queries
```powershell
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d artinrealty

# Check tenant count
SELECT COUNT(*) FROM tenants;

# Check lead count
SELECT tenant_id, COUNT(*) FROM leads GROUP BY tenant_id;

# Check active sessions (from app)
SELECT COUNT(*) FROM leads WHERE last_interaction_at > NOW() - INTERVAL '1 hour';
```

### Redis Inspection
```powershell
# Connect to Redis
docker-compose exec redis redis-cli

# Database 0 (backend sessions)
SELECT 0
KEYS user:*:mode
DBSIZE

# Database 1 (router sessions)  
SELECT 1
KEYS whatsapp_session:*
DBSIZE

# Monitor live commands
MONITOR
```

---

## 🔧 Troubleshooting

### Issue: Backend Won't Start
```powershell
# Check logs
docker-compose logs backend | Select-String "ERROR"

# Common causes:
# 1. Database not ready
docker-compose up -d db
Start-Sleep -Seconds 10
docker-compose restart backend

# 2. Missing environment variables
cat .env
# Verify: DATABASE_URL, JWT_SECRET, GEMINI_API_KEY

# 3. Migration failed
docker-compose run --rm backend alembic upgrade head
```

### Issue: Router Returns "Redis connection failed"
```powershell
# Check Redis
docker-compose ps redis
# If not running:
docker-compose up -d redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Restart router
docker-compose restart router
```

### Issue: WAHA Not Connecting
```powershell
# Check WAHA logs
docker-compose logs waha | Select-String "ERROR"

# Regenerate QR code
curl http://localhost:3001/api/sessions/default/auth/qr

# Restart session
curl -X DELETE http://localhost:3001/api/sessions/default/auth/logout
curl http://localhost:3001/api/sessions/default/start
```

### Issue: Webhook Not Receiving Messages
```powershell
# Verify webhook configured
curl http://localhost:3001/api/sessions/default/webhooks

# Should show:
# {
#   "url": "http://router:8001/webhook/waha",
#   "events": ["message"]
# }

# If not configured, set it:
curl -X POST http://localhost:3001/api/sessions/default/webhooks `
  -H "Content-Type: application/json" `
  -d '{
    "url": "http://router:8001/webhook/waha",
    "events": ["message"]
  }'
```

---

## 📝 Environment Variables Checklist

### Required in `.env` file:
```env
# CRITICAL - Must be set for security
JWT_SECRET=<64+ characters>  # Generate: openssl rand -base64 64
PASSWORD_SALT=<32+ characters>

# Google Gemini API (FREE tier)
GEMINI_API_KEY=<your_key_from_google_ai_studio>

# Database
DB_PASSWORD=<secure_password>
DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@db:5432/artinrealty

# Super Admin
SUPER_ADMIN_EMAIL=admin@artinsmartrealty.com
SUPER_ADMIN_PASSWORD=<change_in_production>

# WhatsApp (Meta Cloud API - optional)
WHATSAPP_VERIFY_TOKEN=<simple_string_for_webhook>
# Note: Access token stored in database per tenant

# WAHA (Self-hosted WhatsApp - recommended)
WAHA_API_KEY=waha_artinsmartrealty_secure_key_2024

# Redis
REDIS_URL=redis://redis:6379/0
SESSION_TTL=86400  # 24 hours

# Nginx (production)
DOMAIN=yourdomain.com
SSL_EMAIL=admin@yourdomain.com
```

---

## 🎯 Post-Deployment Checklist

### Immediate Verification (First 5 Minutes):
- [ ] All containers running (`docker-compose ps` shows "healthy")
- [ ] Backend health endpoint returns 200 (`curl http://localhost:8000/health`)
- [ ] Router health endpoint returns 200 (`curl http://localhost:8001/health`)
- [ ] Frontend loads in browser (`http://localhost:3000`)
- [ ] Database accessible (`docker-compose exec db psql -U postgres -d artinrealty`)
- [ ] Redis accessible (`docker-compose exec redis redis-cli ping`)

### Functional Testing (First 30 Minutes):
- [ ] Login to dashboard works (super admin credentials)
- [ ] Create test tenant via dashboard
- [ ] Generate WhatsApp deep link
- [ ] Scan WAHA QR code with phone
- [ ] Click deep link → Send message
- [ ] Verify bot responds
- [ ] Check session in Redis
- [ ] Test personal message ignored
- [ ] Telegram bot responds (if configured)

### Performance Checks (First Hour):
- [ ] API response time < 500ms (`curl -w "%{time_total}\n" http://localhost:8000/health`)
- [ ] Router response time < 200ms
- [ ] Database queries under load (10+ concurrent requests)
- [ ] Redis hit rate > 80%
- [ ] No memory leaks (check `docker stats` after 1 hour)

### Security Validation (First Day):
- [ ] JWT tokens expire after 24 hours
- [ ] Password hashing works (PBKDF2 600k iterations)
- [ ] CORS restricted to allowed origins (not wildcard)
- [ ] Rate limiting active (test 100 requests/minute)
- [ ] Input sanitization working (test XSS/SQL injection)
- [ ] Tenant isolation verified (tenant 1 can't see tenant 2 data)

---

## 🚨 Emergency Rollback

### If Critical Bug Found After Deployment:
```powershell
# Option 1: Rollback backend only
docker-compose stop backend
docker-compose run --rm -v ${PWD}/backend:/backup backend cp -r /app /backup/backup_$(date +%Y%m%d_%H%M%S)
git checkout HEAD~1 backend/
docker-compose build backend
docker-compose up -d backend

# Option 2: Full rollback
docker-compose down
git stash
git checkout <previous_commit_hash>
docker-compose build
docker-compose up -d

# Option 3: Emergency hotfix
# Edit critical file directly:
docker-compose exec backend nano /app/brain.py
# Restart service:
docker-compose restart backend
```

---

## 📈 Next Steps After Deployment

1. **Monitor for 24 Hours**:
   - Check logs every 2 hours
   - Watch for errors/warnings
   - Verify no memory leaks
   - Check database performance

2. **User Acceptance Testing**:
   - Test with real tenants (not just admin)
   - Complete conversation flows
   - Property search end-to-end
   - Scheduling consultations
   - ROI calculator

3. **Load Testing**:
   - Simulate 100 concurrent users
   - Test webhook flood (1000 messages/minute)
   - Database query performance under load
   - Redis failover testing

4. **Security Audit**:
   - Penetration testing (OWASP Top 10)
   - JWT token validation
   - Input sanitization edge cases
   - Multi-tenant isolation verification

5. **Documentation**:
   - Update API documentation
   - Create user guide (agents)
   - Admin guide (tenant owners)
   - Troubleshooting guide

---

**Deployment Status**: ✅ Ready to Deploy
**Estimated Downtime**: 5-10 minutes (for rebuild)
**Rollback Plan**: Available (3 options)
**Critical Bugs Fixed**: Yes (all P0 bugs)
**Production Ready**: Yes (pending final testing)
