# 🚨 EMERGENCY FIX - Copy/Paste This On Production Server

## Step 1: SSH to Production
```bash
ssh root@5.75.159.165
cd /opt/ArtinSmartRealty
```

## Step 2: Run This Single Command (Copy-Paste Entire Block)

```bash
docker exec artinsmartrealty-db-1 psql -U postgres -d postgres << 'EOF'
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS admin_chat_id VARCHAR(255);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ghost_reminder_sent BOOLEAN DEFAULT FALSE;
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tenants' AND column_name = 'admin_chat_id';
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'ghost_reminder_sent';
EOF
```

**Expected Output:**
```
ALTER TABLE
ALTER TABLE
  column_name   |     data_type      
----------------+--------------------
 admin_chat_id  | character varying
(1 row)

      column_name       | data_type 
------------------------+-----------
 ghost_reminder_sent    | boolean
(1 row)
```

## Step 3: Restart Backend
```bash
docker-compose restart backend
```

## Step 4: Watch Logs (Should Start Successfully)
```bash
docker-compose logs -f backend
```

**Look for:**
- ✅ "Database initialized"
- ✅ "Application startup complete"
- ❌ NO "column does not exist" errors

Press `Ctrl+C` to stop watching logs once you see "Application startup complete"

---

## Alternative: If Docker Container Name is Different

Find the container name:
```bash
docker ps | grep db
```

Then use that name instead of `artinsmartrealty-db-1`:
```bash
docker exec <YOUR_DB_CONTAINER_NAME> psql -U postgres -d postgres << 'EOF'
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS admin_chat_id VARCHAR(255);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ghost_reminder_sent BOOLEAN DEFAULT FALSE;
EOF
```

---

## Verification Commands

After restart, verify everything is working:

```bash
# 1. Check backend is running (should show "Up" status)
docker-compose ps

# 2. Check no errors in logs
docker-compose logs backend | tail -50

# 3. Test database columns exist
docker exec artinsmartrealty-db-1 psql -U postgres -d postgres -c "\d tenants" | grep admin_chat_id
docker exec artinsmartrealty-db-1 psql -U postgres -d postgres -c "\d leads" | grep ghost_reminder_sent
```

**Success Indicators:**
- Backend container status: `Up`
- Logs show: "Application startup complete"
- Both columns appear in `\d` output

---

## If It Still Fails

1. **Check database container name:**
   ```bash
   docker ps -a | grep postgres
   ```

2. **Check database is running:**
   ```bash
   docker-compose ps db
   ```
   Should show "Up" status

3. **Try connecting manually:**
   ```bash
   docker exec -it artinsmartrealty-db-1 psql -U postgres -d postgres
   ```
   Then run:
   ```sql
   \d tenants
   ```
   You should see `admin_chat_id` in the column list

4. **Send me the output of:**
   ```bash
   docker ps
   docker-compose ps
   ```
