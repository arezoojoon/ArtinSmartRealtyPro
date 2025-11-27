# حل مشکل SSL/Certbot با Docker

## مشکل فعلی:
```
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Unknown error)
```

**علت**: Nginx داخل Docker در حال استفاده از پورت 80 است و certbot نمی‌تواند به آن متصل شود.

---

## راه‌حل 1: استفاده از اسکریپت خودکار (ساده‌ترین)

```bash
cd /opt/ArtinSmartRealty
chmod +x setup_ssl.sh
./setup_ssl.sh realty.artinsmartagent.com hr.damroodi@gmail.com
```

این اسکریپت:
- Nginx را موقتاً متوقف می‌کند
- SSL certificate می‌گیرد
- فایل nginx با SSL می‌سازد
- Nginx را ری‌استارت می‌کند

---

## راه‌حل 2: دستی (مرحله به مرحله)

### مرحله 1: متوقف کردن Nginx
```bash
docker compose stop nginx
```

### مرحله 2: گرفتن SSL Certificate
```bash
# ایجاد دایرکتوری‌ها
mkdir -p certbot/conf
mkdir -p certbot/www

# اجرای Certbot
docker run -it --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  -p 80:80 \
  certbot/certbot certonly \
  --standalone \
  --email hr.damroodi@gmail.com \
  --agree-tos \
  --no-eff-email \
  -d realty.artinsmartagent.com
```

### مرحله 3: بروزرسانی docker-compose.yml

فایل `docker-compose.yml` را ویرایش کنید و به سرویس nginx این volume‌ها را اضافه کنید:

```yaml
  nginx:
    image: nginx:alpine
    container_name: artinrealty-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certbot/conf:/etc/letsencrypt      # اضافه کنید
      - ./certbot/www:/var/www/certbot       # اضافه کنید
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    networks:
      - artinrealty-network
```

### مرحله 4: بروزرسانی nginx.conf

فایل `nginx.conf` را ویرایش کنید و HTTPS را فعال کنید:

```nginx
# در قسمت HTTP server، فقط redirect بگذارید:
server {
    listen 80;
    server_name realty.artinsmartagent.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server را uncomment کنید:
server {
    listen 443 ssl http2;
    server_name realty.artinsmartagent.com;

    ssl_certificate /etc/letsencrypt/live/realty.artinsmartagent.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/realty.artinsmartagent.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # همان location blocks قبلی...
    location /api { ... }
    location /webhook { ... }
    location /health { ... }
    location / { ... }
}
```

### مرحله 5: ری‌استارت
```bash
docker compose up -d
```

---

## راه‌حل 3: بدون SSL (موقت - فقط برای تست)

اگر فعلاً نمی‌خواهید SSL داشته باشید:

1. دامنه را مستقیماً به IP متصل کنید
2. از HTTP استفاده کنید (بدون HTTPS)
3. Webhook را با HTTP ست کنید:

```bash
curl -X POST "https://api.telegram.org/bot7941411336:AAGpkPMhg5Wa5RkWDD06sM3UbJ5veWwVgSs/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"http://realty.artinsmartagent.com/webhook/telegram/7941411336:AAGpkPMhg5Wa5RkWDD06sM3UbJ5veWwVgSs"}'
```

⚠️ **توجه**: Telegram برای production نیاز به HTTPS دارد!

---

## تست کردن SSL

```bash
# چک کردن certificate
openssl s_client -connect realty.artinsmartagent.com:443 -servername realty.artinsmartagent.com

# یا ساده‌تر:
curl -I https://realty.artinsmartagent.com/health
```

---

## تمدید خودکار SSL (بعد از نصب)

برای تمدید خودکار، یک cron job بسازید:

```bash
# ویرایش crontab
crontab -e

# اضافه کنید (هر روز ساعت 3 صبح):
0 3 * * * cd /opt/ArtinSmartRealty && docker compose exec certbot renew --quiet && docker compose restart nginx
```

یا در docker-compose.yml یک سرویس certbot اضافه کنید:

```yaml
  certbot:
    image: certbot/certbot
    container_name: artinrealty-certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
```

---

## چک‌لیست نهایی

- [ ] SSL certificate گرفته شد
- [ ] docker-compose.yml بروز شد (certbot volumes)
- [ ] nginx.conf بروز شد (HTTPS فعال شد)
- [ ] سرویس‌ها ری‌استارت شدند
- [ ] HTTPS کار می‌کند: `curl https://realty.artinsmartagent.com/health`
- [ ] Webhook با HTTPS ست شد
- [ ] Bot تلگرام تست شد با /start

---

**توصیه**: از راه‌حل 1 (اسکریپت خودکار) استفاده کنید، ساده‌ترین است! 🚀
