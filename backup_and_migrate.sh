#!/bin/bash
# ArtinSmartRealty - Complete Backup & Migration Script
# Created: Dec 17, 2025
# Purpose: Backup database, uploads, and configuration for server migration

set -e  # Exit on error

BACKUP_DIR="/root/artinrealty_backup_$(date +%Y%m%d_%H%M%S)"
PROJECT_DIR="/opt/ArtinSmartRealtyPro/ArtinSmartRealty"

echo "======================================"
echo "ArtinSmartRealty Backup & Migration"
echo "======================================"
echo "Backup Directory: $BACKUP_DIR"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"
cd "$PROJECT_DIR"

echo "[1/7] Backing up PostgreSQL database..."
docker exec artinrealty-db pg_dump -U postgres artinrealty > "$BACKUP_DIR/database.sql"
echo "✅ Database backed up: $(du -sh $BACKUP_DIR/database.sql | cut -f1)"

echo ""
echo "[2/7] Backing up Redis data..."
docker exec artinrealty-redis redis-cli SAVE
docker cp artinrealty-redis:/data/dump.rdb "$BACKUP_DIR/redis_dump.rdb"
echo "✅ Redis data backed up"

echo ""
echo "[3/7] Backing up uploaded files (property images, PDFs)..."
mkdir -p "$BACKUP_DIR/uploads"
# Copy from Docker volume
docker cp artinrealty-backend:/app/uploads "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  No uploads directory found (this is OK for new installations)"
docker cp artinrealty-backend:/app/pdf_reports "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  No PDF reports found"
echo "✅ Files backed up"

echo ""
echo "[4/7] Backing up environment configuration..."
cp .env "$BACKUP_DIR/env_backup" 2>/dev/null || echo "⚠️  No .env file found"
cp docker-compose.yml "$BACKUP_DIR/"
cp nginx.conf "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  No nginx.conf in root"
echo "✅ Configuration files backed up"

echo ""
echo "[5/7] Exporting Docker images (optional - can rebuild instead)..."
docker save artinsmartrealtypro-backend:latest | gzip > "$BACKUP_DIR/backend_image.tar.gz" &
docker save artinsmartrealtypro-frontend:latest | gzip > "$BACKUP_DIR/frontend_image.tar.gz" &
wait
echo "✅ Docker images exported"

echo ""
echo "[6/7] Creating restoration guide..."
cat > "$BACKUP_DIR/RESTORE_INSTRUCTIONS.md" << 'RESTORE_EOF'
# ArtinSmartRealty - Restoration Guide

## Prerequisites on New Server
- Ubuntu 20.04+ / Debian 11+
- Docker & Docker Compose installed
- Git installed
- Minimum 2GB RAM, 20GB disk

## Step-by-Step Restoration

### 1. Clone Repository
```bash
cd /opt
git clone https://github.com/YOUR_USERNAME/ArtinRealtySmartPro.git
cd ArtinRealtySmartPro/ArtinSmartRealty
```

### 2. Restore Environment File
```bash
cp /path/to/backup/env_backup .env
```

**CRITICAL**: Update these in `.env`:
- `DATABASE_URL` - If using different DB password
- `JWT_SECRET` - Keep the same!
- `PASSWORD_SALT` - Keep the same!
- `GEMINI_API_KEY` - Keep the same

### 3. Restore Database
```bash
# Start PostgreSQL container only
docker-compose up -d db

# Wait 10 seconds for DB to initialize
sleep 10

# Restore database
docker exec -i artinrealty-db psql -U postgres -d artinrealty < /path/to/backup/database.sql
```

### 4. Restore Redis (Optional - Sessions only)
```bash
docker-compose up -d redis
docker cp /path/to/backup/redis_dump.rdb artinrealty-redis:/data/dump.rdb
docker-compose restart redis
```

### 5. Restore Uploaded Files
```bash
# Start backend container to create volumes
docker-compose up -d backend
sleep 5

# Copy files
docker cp /path/to/backup/uploads artinrealty-backend:/app/
docker cp /path/to/backup/pdf_reports artinrealty-backend:/app/
docker-compose restart backend
```

### 6. Start Full Stack
```bash
docker-compose up -d
```

### 7. Verify Deployment
```bash
# Check all containers
docker-compose ps

# Test backend
curl http://localhost:8000/health

# Check logs
docker-compose logs -f backend
```

### 8. Configure DNS & SSL (Production)
```bash
# Update DNS A record to point to new server IP
# Example: artinsmartrealty.com -> NEW_SERVER_IP

# Generate SSL certificate (if using Let's Encrypt)
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d artinsmartrealty.com -d www.artinsmartrealty.com
```

### 9. Update Telegram Webhooks (if using webhooks)
```python
# Run this in Python or via API call
import requests
BOT_TOKEN = "your_bot_token"
NEW_URL = "https://artinsmartrealty.com/api/telegram/webhook"
requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook", json={"url": NEW_URL})
```

## Verification Checklist
- [ ] Database has all tenants
- [ ] Super admin can login
- [ ] Tenants can login
- [ ] Telegram bot responds
- [ ] WhatsApp bot responds
- [ ] Property images load
- [ ] PDF reports generate
- [ ] Email notifications work

## Troubleshooting

### Database Connection Errors
```bash
# Check DB is running
docker logs artinrealty-db --tail 50

# Verify password matches .env
docker exec -it artinrealty-db psql -U postgres -d artinrealty
```

### Frontend Shows Old Data
```bash
# Hard rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend

# Clear browser cache: Ctrl+Shift+R
```

### Telegram Bot Not Responding
```bash
# Check backend logs
docker logs artinrealty-backend --tail 100 | grep -i telegram

# Verify bot token in database:
docker exec -it artinrealty-db psql -U postgres -d artinrealty -c "SELECT id, name, telegram_bot_token FROM tenants;"
```

## Performance Optimization (Post-Migration)

### Enable Firewall
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Setup Auto-Backups (Cron Job)
```bash
sudo crontab -e

# Add this line (daily backup at 3 AM):
0 3 * * * /opt/ArtinSmartRealtyPro/ArtinSmartRealty/backup_and_migrate.sh
```

### Monitor Disk Usage
```bash
df -h  # Check disk space
docker system prune -a  # Clean unused Docker resources
```

## Support
Contact: info@artinsmartagent.com
Docs: https://github.com/YOUR_USERNAME/ArtinRealtySmartPro
RESTORE_EOF

echo "✅ Restoration guide created"

echo ""
echo "[7/7] Creating compressed archive..."
cd /root
tar -czf "artinrealty_backup_$(date +%Y%m%d_%H%M%S).tar.gz" "$(basename $BACKUP_DIR)"
ARCHIVE_SIZE=$(du -sh artinrealty_backup_*.tar.gz | tail -1 | cut -f1)
echo "✅ Archive created: $ARCHIVE_SIZE"

echo ""
echo "======================================"
echo "✅ BACKUP COMPLETE!"
echo "======================================"
echo ""
echo "📦 Backup Location: $BACKUP_DIR"
echo "📦 Compressed Archive: /root/artinrealty_backup_*.tar.gz"
echo "📄 Restoration Guide: $BACKUP_DIR/RESTORE_INSTRUCTIONS.md"
echo ""
echo "🚀 MIGRATION STEPS:"
echo "1. Copy archive to new server:"
echo "   scp /root/artinrealty_backup_*.tar.gz root@NEW_SERVER_IP:/root/"
echo ""
echo "2. On new server, extract and restore:"
echo "   cd /root"
echo "   tar -xzf artinrealty_backup_*.tar.gz"
echo "   cd artinrealty_backup_*"
echo "   cat RESTORE_INSTRUCTIONS.md  # Follow these steps"
echo ""
echo "3. Update DNS to point to new server IP"
echo ""
echo "======================================"
