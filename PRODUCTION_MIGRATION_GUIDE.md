# 🚨 URGENT: Production Database Migration Required

**Date:** December 4, 2025  
**Issue:** Backend service crashing due to missing database columns  
**Error:** `column tenants.admin_chat_id does not exist`

---

## Problem Summary

Your code is already deployed to production and includes references to two new database columns that don't exist yet:

1. **`tenants.admin_chat_id`** - For Hot Lead Alerts & Morning Coffee Reports
2. **`leads.ghost_reminder_sent`** - For Ghost Protocol tracking

The backend service is crashing on startup because SQLAlchemy tries to query these columns before they exist.

---

## ✅ Solution: Manual SQL Migration

Since Alembic is not accessible in your Docker container, you need to add these columns manually via PostgreSQL.

### Step 1: SSH to Production Server

```bash
ssh root@srv1151343
```

### Step 2: Navigate to Project Directory

```bash
cd /opt/ArtinSmartRealty
```

### Step 3: Start Database Container (if not running)

```bash
docker-compose up -d db
sleep 5
```

### Step 4: Connect to PostgreSQL

```bash
docker-compose exec db psql -U postgres -d postgres
```

### Step 5: Execute SQL Migrations

```sql
-- Add admin_chat_id column to tenants table
ALTER TABLE tenants 
ADD COLUMN IF NOT EXISTS admin_chat_id VARCHAR(255);

-- Add ghost_reminder_sent column to leads table  
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS ghost_reminder_sent BOOLEAN DEFAULT FALSE;

-- Verify columns were added
\d tenants
\d leads

-- Exit psql
\q
```

### Step 6: Restart Backend Service

```bash
docker-compose restart backend
```

### Step 7: Monitor Logs for Success

```bash
docker-compose logs -f backend
```

**Expected output:**
```
✅ Database initialized
✅ [Morning Coffee] APScheduler started
📱 Starting Telegram bot for tenant...
INFO: Application startup complete.
```

---

## 📋 Complete Command Sequence (Copy-Paste Ready)

If you want to execute everything in one go:

```bash
# Connect to production server
ssh root@srv1151343

# Navigate to project
cd /opt/ArtinSmartRealty

# Start database container
docker-compose up -d db
sleep 5

# Add missing columns
docker-compose exec db psql -U postgres -d postgres -c "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS admin_chat_id VARCHAR(255);"

docker-compose exec db psql -U postgres -d postgres -c "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ghost_reminder_sent BOOLEAN DEFAULT FALSE;"

# Verify schema
docker-compose exec db psql -U postgres -d postgres -c "\d tenants"
docker-compose exec db psql -U postgres -d postgres -c "\d leads"

# Restart services
docker-compose restart backend

# Monitor startup
docker-compose logs -f backend
```

---

## 🔍 Verification Checklist

### After Migration:

- [ ] Backend service starts without errors
- [ ] No "column does not exist" errors in logs
- [ ] Telegram bots are active
- [ ] APScheduler started for Morning Coffee Report

### Test Hot Lead Alert:

1. Send `/set_admin` to your bot
2. Test with a friend/test account:
   - Send `/start`
   - Select a goal (Investment/Living/Residency)
   - Share phone number
3. Verify you receive notification:
   ```
   🚨 لید داغ (Hot Lead)!
   👤 نام: Test User
   📱 شماره: +123...
   ```

---

## 🐛 If It Still Fails

### Error: "database 'artin_smart_realty' does not exist"

**Solution:** Use `postgres` as database name instead:

```bash
docker-compose exec db psql -U postgres -d postgres -c "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS admin_chat_id VARCHAR(255);"
```

### Error: "relation 'tenants' does not exist"

**Problem:** Database hasn't been initialized  
**Solution:** Let backend create tables first, then add columns

### Error: Permission denied

**Solution:** Ensure you're running as `root` or have proper permissions

---

## 📊 Database Schema Reference

### Before Migration

```sql
-- tenants table (missing column)
CREATE TABLE tenants (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  ...
  primary_color VARCHAR(20),
  -- admin_chat_id is MISSING
  subscription_status VARCHAR(50),
  ...
);

-- leads table (missing column)
CREATE TABLE leads (
  id SERIAL PRIMARY KEY,
  ...
  source VARCHAR(100),
  last_interaction TIMESTAMP,
  -- ghost_reminder_sent is MISSING
  created_at TIMESTAMP,
  ...
);
```

### After Migration

```sql
-- tenants table (with new column)
CREATE TABLE tenants (
  ...
  primary_color VARCHAR(20),
  admin_chat_id VARCHAR(255),  -- ✅ ADDED
  subscription_status VARCHAR(50),
  ...
);

-- leads table (with new column)
CREATE TABLE leads (
  ...
  source VARCHAR(100),
  last_interaction TIMESTAMP,
  ghost_reminder_sent BOOLEAN DEFAULT FALSE,  -- ✅ ADDED
  created_at TIMESTAMP,
  ...
);
```

---

## 🚀 What Happens After Successful Migration

### 1. Hot Lead Alert System Activates

- Admin can send `/set_admin` to register for notifications
- Every phone capture triggers instant alert
- Works 24/7 across all tenants

### 2. Ghost Protocol Starts Running

- Background task checks every 30 minutes
- Auto-follows up with inactive leads after 2 hours
- Soft touch: "My colleague found the property you wanted"

### 3. Morning Coffee Report Scheduler Initialized

- APScheduler starts with cron job
- Daily at 8:00 AM, sends summary to admin
- Metrics: conversations, new leads, high-value alerts

### 4. Scarcity Tactics Already Active

- No database changes needed
- Urgency messages automatically appended to listings
- Tracks engagement in `urgency_score` field

---

## 📞 Support

If you encounter any issues during migration:

1. **Check container status:**
   ```bash
   docker-compose ps
   ```

2. **View full error logs:**
   ```bash
   docker-compose logs backend | tail -100
   ```

3. **Restart all services:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Nuclear option (last resort):**
   ```bash
   docker-compose down -v  # WARNING: Deletes all data
   docker-compose up -d --build
   ```

---

## ✅ Success Indicators

After migration completes, you should see in logs:

```
🚀 Starting ArtinSmartRealty V2...
✅ Database initialized
✅ [Morning Coffee] APScheduler started - Reports scheduled for 08:00 AM daily
📱 Starting Telegram bot for tenant 1...
🔄 Ghost Protocol background task started for tenant 1
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

**No "column does not exist" errors!**

---

## 🎯 Next Steps After Migration

1. **Register as Admin:**
   - Send `/set_admin` to your bot
   - Verify you get confirmation message

2. **Test Features:**
   - Hot Lead Alert: Simulate phone capture
   - Ghost Protocol: Wait 2 hours after creating test lead
   - Morning Coffee: Wait until 8:00 AM next day

3. **Monitor Production:**
   - Check logs daily for Ghost Protocol activity
   - Verify admin receives morning reports
   - Track hot lead notifications

---

**Good luck with the migration! Your bot is ready to become a 24/7 sales machine.** 🚀
