# Database Migration Guide

## 🚨 Emergency Fix (Run on Production Server NOW)

```bash
# SSH to production server and run:
cd /opt/ArtinSmartRealty
bash fix_production_db.sh

# Then restart backend:
docker-compose restart backend

# Monitor logs:
docker-compose logs -f backend
```

---

## 🔧 Proper Way: Using Alembic (For All Future Changes)

### 1. Install Dependencies (Local Development)

```bash
pip install alembic==1.13.0
```

### 2. Alembic Commands Reference

#### Initialize Alembic (Already Done)
```bash
alembic init alembic
```

#### Create a New Migration
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Or create empty migration template
alembic revision -m "description of changes"
```

#### Apply Migrations
```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade one version at a time
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history
```

### 3. Production Deployment Workflow

#### Option A: Manual Migration (Recommended for First Time)
```bash
# On production server
cd /opt/ArtinSmartRealty
bash fix_production_db.sh
docker-compose restart backend
```

#### Option B: Alembic Migration (For Future Changes)
```bash
# On production server
cd /opt/ArtinSmartRealty

# Install alembic in container
docker-compose exec backend pip install alembic==1.13.0

# Run migration inside container
docker-compose exec backend alembic upgrade head

# Restart backend
docker-compose restart backend
```

### 4. Development Workflow (Making Schema Changes)

```bash
# 1. Edit database.py models locally
# 2. Generate migration
alembic revision --autogenerate -m "add new feature columns"

# 3. Review generated migration in alembic/versions/
# 4. Test migration locally
alembic upgrade head

# 5. Commit migration file
git add alembic/versions/*.py
git commit -m "Add database migration for new feature"
git push

# 6. Deploy to production
ssh root@5.75.159.165
cd /opt/ArtinSmartRealty
git pull
docker-compose exec backend alembic upgrade head
docker-compose restart backend
```

---

## 📋 Migration Checklist

### Before Applying Migration:
- [ ] Backup production database
- [ ] Test migration on staging/local first
- [ ] Review generated SQL (alembic upgrade --sql head > migration.sql)
- [ ] Check for data loss (column drops, type changes)
- [ ] Schedule maintenance window if needed

### After Applying Migration:
- [ ] Verify columns exist (check with \d tablename in psql)
- [ ] Restart affected services
- [ ] Monitor error logs for 5 minutes
- [ ] Test key features (create lead, send message)
- [ ] Update documentation

---

## 🔍 Troubleshooting

### Issue: "Target database is not up to date"
```bash
# Stamp database with current version
alembic stamp head
```

### Issue: "Can't locate revision identified by 'xxxx'"
```bash
# View current stamp
alembic current

# Force stamp to specific revision
alembic stamp 001_sales_features
```

### Issue: Migration fails halfway
```bash
# Manually fix database to match expected state
# Then stamp the version
alembic stamp <revision_id>
```

### Issue: Need to rollback
```bash
# Downgrade one version
alembic downgrade -1

# Or downgrade to specific version
alembic downgrade 001_sales_features
```

---

## 📦 Docker Production Setup

### Add Alembic to Docker Image

Edit `Dockerfile`:
```dockerfile
# Add to requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy alembic configuration
COPY alembic.ini .
COPY alembic/ alembic/
```

### Auto-migrate on Container Start

Edit `docker-compose.yml`:
```yaml
services:
  backend:
    command: >
      sh -c "alembic upgrade head && 
             uvicorn main:app --host 0.0.0.0 --port 8000"
```

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `alembic revision --autogenerate -m "msg"` | Create migration from model changes |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Rollback last migration |
| `alembic current` | Show current database version |
| `alembic history` | Show all migrations |
| `alembic stamp head` | Mark database as up-to-date without running migrations |

---

## ✅ Current Status

**Migration Created**: `alembic/versions/001_sales_features.py`
- Adds `tenants.admin_chat_id` (VARCHAR 255)
- Adds `leads.ghost_reminder_sent` (BOOLEAN DEFAULT FALSE)

**Next Step**: Run `bash fix_production_db.sh` on production server!
