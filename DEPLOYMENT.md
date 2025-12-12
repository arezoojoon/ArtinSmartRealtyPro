# Deployment Guide

## Production Deployment

### Prerequisites

- VPS/Cloud server with:
  - Ubuntu 20.04+ or Debian 11+
  - Minimum 2 CPU cores, 4GB RAM
  - 20GB+ storage
  - Docker 20.10+ installed
  - Domain name (optional, for SSL)

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 2: Clone Repository

```bash
cd /opt
sudo git clone https://github.com/arezoojoon/ArtinSmartRealtyPro.git
cd ArtinSmartRealtyPro
```

### Step 3: Configure Environment

```bash
cp .env.example .env
nano .env
```

**Required configurations:**

```env
# Database (use strong password!)
DB_PASSWORD=your_production_db_password_here

# AI
GEMINI_API_KEY=your_gemini_api_key

# Security (CRITICAL - change these!)
JWT_SECRET=$(openssl rand -hex 32)
PASSWORD_SALT=$(openssl rand -hex 16)

# Admin account
SUPER_ADMIN_EMAIL=admin@yourcompany.com
SUPER_ADMIN_PASSWORD=YourStrongPassword123!

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# WhatsApp (choose WAHA or Twilio)
WAHA_API_URL=http://waha:3000
# OR
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
```

### Step 4: Deploy

```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy to production
./deploy.sh prod
```

This will:
1. Build Docker images
2. Initialize database
3. Run migrations
4. Seed Dubai knowledge base
5. Create admin account
6. Start all services

### Step 5: Setup SSL (Optional but Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already configured in nginx container)
```

### Step 6: Verify Deployment

```bash
# Check services
docker-compose ps

# View logs
docker-compose logs -f backend

# Test health endpoint
curl http://localhost/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "bots": "running"
}
```

---

## Configuration

### Nginx (Reverse Proxy)

Edit `nginx.conf` if needed:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://frontend:80;
    }
    
    location /api {
        proxy_pass http://backend:8000;
    }
}
```

### Database Backup

```bash
# Manual backup
docker-compose exec db pg_dump -U postgres artinrealty > backup_$(date +%Y%m%d).sql

# Automated daily backups (add to crontab)
0 2 * * * cd /opt/ArtinSmartRealtyPro && docker-compose exec -T db pg_dump -U postgres artinrealty > /backups/artinrealty_$(date +\%Y\%m\%d).sql
```

### Monitoring

```bash
# View real-time logs
docker-compose logs -f backend

# Check resource usage
docker stats

# Database size
docker-compose exec db psql -U postgres -d artinrealty -c "SELECT pg_size_pretty(pg_database_size('artinrealty'));"
```

---

## Updates & Maintenance

### Update Application

```bash
cd /opt/ArtinSmartRealtyPro
git pull origin main
docker-compose up -d --build backend
docker-compose logs -f backend
```

### Restart Services

```bash
# Restart specific service
docker-compose restart backend

# Restart all
docker-compose restart

# Stop all
docker-compose down

# Start all
docker-compose up -d
```

### Database Migration

```bash
# Run new migrations
docker-compose exec backend alembic upgrade head

# Rollback one migration
docker-compose exec backend alembic downgrade -1
```

---

## Troubleshooting

### Bot Not Responding

```bash
# Check bot logs
docker-compose logs backend | grep "telegram\|whatsapp"

# Restart backend
docker-compose restart backend

# Verify webhook
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
```

### Database Connection Issues

```bash
# Check database status
docker-compose ps db

# Test connection
docker-compose exec backend python -c "from database import engine; import asyncio; asyncio.run(engine.connect())"

# Reset database (DANGER!)
docker-compose down -v
docker-compose up -d
```

### High Memory Usage

```bash
# Check memory
docker stats

# Restart Redis (clears cache)
docker-compose restart redis

# Clear old PDF reports
docker-compose exec backend find /app/pdf_reports -mtime +30 -delete
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong JWT_SECRET (32+ characters)
- [ ] Enable SSL/HTTPS
- [ ] Configure firewall (ufw)
- [ ] Regular database backups
- [ ] Update Docker images monthly
- [ ] Monitor logs for suspicious activity
- [ ] Use environment variables (never hardcode secrets)

---

## Support

For deployment issues:
- Check logs: `docker-compose logs -f`
- GitHub Issues: https://github.com/arezoojoon/ArtinSmartRealtyPro/issues
- Email: support@artinsmartrealty.com
