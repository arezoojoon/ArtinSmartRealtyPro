=====================================================
   ARTINSMARTREALTY - REAL PRODUCTION FIX DEPLOYMENT
=====================================================

## ISSUES FOUND & FIXED ✅

### Issue 1: Database Name Mismatch ❌
**ERROR**: `database "artinrealty_db" does not exist`
**ROOT CAUSE**: Docker creates DB named `artinrealty`, but your test commands used `artinrealty_db`
**FIX**: Database is correct - just use correct name: `artinrealty` (NOT `artinrealty_db`)

### Issue 2: Ghost Protocol V2 Error ❌
**ERROR**: `Neither 'BinaryExpression' object nor 'Comparator' object has an attribute 'astext'`
**ROOT CAUSE**: SQLAlchemy 2.0 doesn't support `.astext` - old syntax
**FIX**: Changed to JSON contains check `~Lead.conversation_data.contains({'fast_nudge_sent': True})`
**FILE**: `backend/telegram_bot.py` line 979

### Issue 3: Router Unhealthy ❌
**ERROR**: Router container showing "unhealthy" status
**ROOT CAUSE**: Missing `curl` in router container for Docker healthcheck
**FIX**: Added curl to Dockerfile.router_v3
**FILE**: `backend/Dockerfile.router_v3`

## DEPLOYMENT COMMANDS

SSH to your server and run:

```bash
cd /opt/ArtinSmartRealty

# Pull latest fixes from GitHub (commit fd84d00)
git pull origin main

# Rebuild services with fixes
docker-compose build --no-cache backend router

# Restart all services
docker-compose down
docker-compose up -d

# Wait 30 seconds for services to start
sleep 30

# VERIFY - Run these EXACT commands
docker-compose ps
docker-compose exec -T db psql -U postgres -d artinrealty -c "SELECT COUNT(*) FROM tenants;"
docker-compose exec -T db psql -U postgres -d artinrealty -c "SELECT COUNT(*) FROM leads;"
curl http://localhost:8000/health
curl http://localhost:8001/health
docker-compose logs --tail=100 backend | grep "Ghost Protocol"
docker-compose logs --tail=100 backend router | grep -i error
```

## EXPECTED RESULTS AFTER FIX

✅ Database queries work (using `artinrealty` not `artinrealty_db`)
✅ Router status shows "healthy" (not unhealthy)
✅ Ghost Protocol runs without `.astext` error
✅ All containers healthy

## ONE-LINE DEPLOYMENT (Quick Fix)

```bash
cd /opt/ArtinSmartRealty && git pull origin main && docker-compose build --no-cache backend router && docker-compose down && docker-compose up -d && sleep 30 && docker-compose ps && curl http://localhost:8000/health && curl http://localhost:8001/health
```

## VERIFICATION SCRIPT

Or use the automated script:

```bash
cd /opt/ArtinSmartRealty
bash DEPLOY_URGENT_FIXES.sh
```

This script will:
1. Pull latest code
2. Rebuild backend + router
3. Restart all services
4. Run all verification commands
5. Show you real results

## WHAT WAS CHANGED

**Files Modified:**
- `backend/telegram_bot.py` - Fixed Ghost Protocol SQLAlchemy query
- `backend/Dockerfile.router_v3` - Added curl for healthcheck
- `docker-compose.yml` - Already had correct command (no change needed)

**Git Commit**: fd84d00
**GitHub**: https://github.com/arezoojoon/ArtinSmartRealtyPro

## POST-DEPLOYMENT TESTING

After deployment, test these:

1. **Database Connection**:
   ```bash
   docker-compose exec -T db psql -U postgres -d artinrealty -c "SELECT * FROM tenants LIMIT 1;"
   ```

2. **Telegram Bot** (if configured):
   - Send message to any tenant's bot
   - Check logs: `docker-compose logs -f backend | grep Telegram`

3. **WhatsApp Router**:
   ```bash
   curl http://localhost:8001/router/stats
   ```

4. **Ghost Protocol** (wait 15 mins for next cycle):
   ```bash
   docker-compose logs -f backend | grep "Ghost Protocol"
   ```

## MONITORING

Watch logs in real-time:
```bash
docker-compose logs -f backend router
```

Filter errors only:
```bash
docker-compose logs -f backend router | grep -i "error\|exception\|failed"
```

=====================================================
             FIXES ARE READY TO DEPLOY
=====================================================
