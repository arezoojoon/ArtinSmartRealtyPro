# 🚀 دستورات استقرار نهایی روی سرور Production

**سرور**: 72.62.93.119  
**کاربر**: root  
**رمز عبور**: 8;YdR.y3J1Uy08TZ-yKo

---

## مرحله 1: اتصال SSH به سرور

```bash
ssh root@72.62.93.119
# رمز عبور: 8;YdR.y3J1Uy08TZ-yKo
```

---

## مرحله 2: رفتن به پوشه پروژه

```bash
cd ~/ArtinSmartRealty || cd /root/ArtinSmartRealty || cd /var/www/ArtinSmartRealty

# بررسی وضعیت
pwd
ls -la
```

---

## مرحله 3: دریافت آخرین تغییرات از GitHub

```bash
# بررسی وضعیت Git
git status
git branch

# دریافت آخرین commit ها
git fetch origin
git pull origin main

# تایید آخرین commit
git log -1 --oneline
# باید ببینید: "🚀 Production Ready: WhatsApp Router V3 + Security Hardening"
```

---

## مرحله 4: Backup فعلی (اختیاری اما توصیه می‌شود)

```bash
# ذخیره وضعیت فعلی
docker-compose ps > backup_$(date +%Y%m%d_%H%M%S).txt

# Backup دیتابیس (اختیاری)
docker-compose exec -T db pg_dump -U postgres artinrealty_db > backup_db_$(date +%Y%m%d_%H%M%S).sql
```

---

## مرحله 5: توقف سرویس‌های فعلی

```bash
# توقف با حفظ volumes (دیتا پاک نمی‌شود)
docker-compose down

# بررسی که همه متوقف شدند
docker ps
# خروجی باید خالی باشد
```

---

## مرحله 6: Build کردن Image های جدید

```bash
# Build با no-cache برای اطمینان از وابستگی‌های جدید
docker-compose build --no-cache backend router

# بررسی سایز و تاریخ image ها
docker images | grep artinrealty
```

---

## مرحله 7: راه‌اندازی دیتابیس و Redis

```bash
# ابتدا دیتابیس و Redis را start کنید
docker-compose up -d db redis

# منتظر بمانید تا آماده شوند
sleep 15

# بررسی health
docker-compose ps db redis
docker-compose logs db | tail -20
```

---

## مرحله 8: اجرای Migration های دیتابیس

```bash
# اجرای migration ها (مهم!)
docker-compose run --rm backend alembic upgrade head

# بررسی نتیجه
echo "✅ Migrations applied"
```

---

## مرحله 9: راه‌اندازی همه سرویس‌ها

```bash
# Start کردن همه سرویس‌ها
docker-compose up -d

# بررسی وضعیت
docker-compose ps

# باید ببینید:
# - backend: healthy
# - router: healthy  
# - db: healthy
# - redis: healthy
# - frontend: healthy
# - nginx: healthy (اگر تنظیم شده)
```

---

## مرحله 10: Health Check ها

```bash
# Backend health
curl http://localhost:8000/health
# انتظار: {"status": "healthy", ...}

# Router health
curl http://localhost:8001/health
# انتظار: {"status": "healthy", "redis": "connected", ...}

# Router stats
curl http://localhost:8001/router/stats | jq
# انتظار: {"active_sessions": 0, ...}

# Frontend
curl -I http://localhost:3000
# انتظار: HTTP/1.1 200 OK
```

---

## مرحله 11: بررسی Logs

```bash
# Backend logs (آخرین 50 خط)
docker-compose logs --tail=50 backend

# Router logs
docker-compose logs --tail=50 router

# همه logs به صورت real-time
docker-compose logs -f

# فیلتر ERROR ها
docker-compose logs backend | grep ERROR
docker-compose logs router | grep ERROR
```

---

## مرحله 12: تست عملکردی

### تست 1: Login به داشبورد
```bash
# بررسی که API کار می‌کند
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@artinsmartagent.com","password":"SuperARTIN2588357!"}'

# باید یک JWT token برگرداند
```

### تست 2: بررسی Telegram Bot
```bash
# لاگ‌های تلگرام
docker-compose logs backend | grep "Telegram bot"
# باید ببینید: "✅ Telegram bots started for X tenants"
```

### تست 3: بررسی WhatsApp Router
```bash
# تست generate link
curl -X POST http://localhost:8001/router/generate-link \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": 1,
    "vertical": "realty",
    "gateway_number": "971557357753"
  }' | jq

# باید deep link تولید کند
```

### تست 4: بررسی Rate Limiting
```bash
# ارسال 10 request سریع
for i in {1..10}; do 
  curl -s http://localhost:8000/health > /dev/null
  echo "Request $i sent"
done

# همه باید 200 برگردانند (rate limit: 100/min)
```

---

## مرحله 13: Monitoring (30 دقیقه اول)

```bash
# نظارت زنده روی logs
docker-compose logs -f backend router

# هر 5 دقیقه یکبار health check
watch -n 300 'curl -s http://localhost:8000/health && echo "" && curl -s http://localhost:8001/health'

# بررسی منابع
docker stats --no-stream

# بررسی دیسک
df -h

# بررسی حافظه
free -h
```

---

## 🔥 Troubleshooting - اگر مشکلی پیش آمد

### مشکل 1: Backend start نمی‌شود
```bash
# بررسی logs
docker-compose logs backend | tail -50

# چک کردن .env
docker-compose exec backend cat /app/.env | grep -v PASSWORD

# Restart
docker-compose restart backend
```

### مشکل 2: Redis اتصال نداره
```bash
# بررسی Redis
docker-compose exec redis redis-cli ping
# باید: PONG

# Restart Redis
docker-compose restart redis

# Restart backend
docker-compose restart backend router
```

### مشکل 3: Migration fail شد
```bash
# اجرای دستی
docker-compose run --rm backend alembic upgrade head

# اگر باز هم failed:
docker-compose run --rm backend alembic current
docker-compose run --rm backend alembic history
```

### مشکل 4: Port 8000 در دسترس نیست
```bash
# بررسی چه چیزی روی port 8000 است
netstat -tlnp | grep 8000

# یا
lsof -i :8000

# Kill کردن process قدیمی
kill -9 <PID>
```

---

## ✅ Checklist نهایی

پس از deployment باید این موارد را تایید کنید:

- [ ] همه container ها healthy هستند: `docker-compose ps`
- [ ] Backend health: `curl http://localhost:8000/health`
- [ ] Router health: `curl http://localhost:8001/health`
- [ ] Frontend باز می‌شود: `curl -I http://localhost:3000`
- [ ] Login کار می‌کند
- [ ] لاگ‌ها ERROR ندارند: `docker-compose logs | grep ERROR`
- [ ] CPU usage < 80%: `docker stats`
- [ ] Memory usage < 80%: `free -h`
- [ ] Disk usage < 90%: `df -h`
- [ ] Telegram bot ها متصل هستند
- [ ] Router QR code تولید می‌کند

---

## 📊 دستورات مانیتورینگ مفید

```bash
# لاگ‌های 24 ساعت اخیر
docker-compose logs --since 24h backend > backend_24h.log

# تعداد ERROR ها
docker-compose logs backend | grep -c ERROR

# آخرین 100 request
docker-compose logs backend | grep "POST\|GET" | tail -100

# بررسی session های Redis
docker-compose exec redis redis-cli -n 1 KEYS "whatsapp_session:*" | wc -l

# بررسی database size
docker-compose exec db psql -U postgres -d artinrealty_db -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
"
```

---

## 🎉 وضعیت Deployment

**آخرین Commit**: `e04f1e4` - "Production Ready: WhatsApp Router V3 + Security Hardening"

**تغییرات کلیدی**:
- ✅ WhatsApp Router V3 با Redis session management
- ✅ Rate limiting روی همه webhook ها (100 req/min)
- ✅ Safe background task wrapper
- ✅ وابستگی‌های گمشده اضافه شدند (aiohttp, pydub)
- ✅ باگ regex timeout رفع شد
- ✅ Backend header integration برای router

**پیش‌نیازها**:
- Docker Compose نصب باشد
- Port های 8000, 8001, 3000, 5432, 6379 آزاد باشند
- حداقل 2GB RAM آزاد
- حداقل 10GB دیسک آزاد

---

**تاریخ**: 20 دسامبر 2024  
**آماده Production**: ✅ بله  
**تست شده**: ✅ محلی - ⏳ منتظر تست روی سرور  
**اولویت**: 🔥 High - Deploy فوری
