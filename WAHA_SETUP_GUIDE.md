# 🚀 راهنمای نصب Waha WhatsApp API

## چیست Waha؟

Waha یک پروژه متن‌باز است که دقیقاً مثل «واتساپ وب» عمل می‌کند، اما به جای اینکه توی مرورگر باز شود، توی یک کانتینر داکر روی سرور شما اجرا می‌شود و بهتون API می‌دهد.

### مزایا:
- ✅ **رایگان**: بدون هزینه برای پیام‌ها
- ✅ **بدون نیاز به تایید متا**: کاری به فیس‌بوک ندارد
- ✅ **سریع**: در عرض 5 دقیقه بالا می‌آید
- ✅ **روی هر شماره‌ای**: می‌تونی روی شماره شخصی خودت راه‌اندازی‌اش کنی

---

## مراحل نصب

### مرحله 1: اضافه کردن Waha به docker-compose.yml

سرویس Waha به `docker-compose.yml` اضافه شده است:

```yaml
waha:
  image: devlikeapro/waha:latest
  container_name: artinrealty-waha
  restart: unless-stopped
  environment:
    - WHATSAPP_DEFAULT_ENGINE=WEBJS
    - WHATSAPP_RESTART_ON_FAIL=True
    - WHATSAPP_AUTOREFRESH_QR=True
    - WHATSAPP_HOOK_EVENTS=message,message.any
    - WHATSAPP_HOOK_URL=http://backend:8000/api/webhook/waha
  ports:
    - "3001:3000"  # دسترسی از بیرون روی پورت 3001
  volumes:
    - waha_data:/app/.waha
  networks:
    - artinrealty-network
```

### مرحله 2: اجرای سرویس

```bash
# SSH به سرور
ssh root@srv1151343.hstgr.io
cd /opt/ArtinSmartRealty

# Pull و start کردن Waha
docker-compose up -d waha

# چک کردن لاگ‌ها
docker-compose logs -f waha
```

### مرحله 3: اسکن QR Code

دو روش برای اسکن QR code دارید:

#### روش 1: از طریق Dashboard (راحت‌تر)

1. در مرورگر به آدرس زیر بروید:
   ```
   http://SERVER_IP:3001/api/dashboard
   ```

2. QR Code را روی صفحه می‌بینید.

3. گوشی خودتان را بردارید:
   - واتساپ را باز کنید
   - Settings → Linked Devices
   - Link a Device
   - QR Code را اسکن کنید

#### روش 2: از طریق Terminal (برای تکنیکی‌ها)

```bash
# QR Code در لاگ‌ها ظاهر می‌شود
docker-compose logs -f waha | grep "QR"
```

---

## Deep Links برای Verticals مختلف

بعد از اسکن کردن، این لینک‌ها را در اینستاگرام یا وبسایت قرار دهید:

### 🏠 لینک املاک (Realty)
```
https://wa.me/971505037158?text=start_realty
```

### ✈️ لینک تراول (Travel/Expo)
```
https://wa.me/971505037158?text=start_travel
```

### 🎪 لینک اکسپو (Events/Exhibitions)
```
https://wa.me/971505037158?text=start_expo
```

### 🏥 لینک کلینیک (Medical Tourism)
```
https://wa.me/971505037158?text=start_clinic
```

**توجه**: شماره `971505037158` را با شماره‌ای که QR code را اسکن کردید جایگزین کنید.

---

## نحوه کار Deep Links

1. **مشتری روی لینک کلیک می‌کند** (مثلاً `start_travel`)
2. **واتساپ باز می‌شود** با متن پیش‌فرض
3. **مشتری دکمه Send را می‌زند**
4. **Waha پیام را دریافت می‌کند** و به backend می‌فرستد
5. **VerticalRouter تشخیص می‌دهد** که vertical کدام است
6. **شماره مشتری در Redis ذخیره می‌شود** (24 ساعت)
7. **از این به بعد تمام پیام‌ها** به همان vertical می‌رود

---

## ساختار Webhook

Waha پیام‌ها را به این فرمت می‌فرستد:

```json
{
  "event": "message",
  "session": "default",
  "payload": {
    "from": "971505037158@c.us",
    "body": "start_realty",
    "hasMedia": false,
    "_data": {
      "notifyName": "Ahmad"
    }
  }
}
```

Backend این را parse می‌کند و به lead مناسب route می‌کند.

---

## Vertical Routing Logic

کد در `backend/vertical_router.py`:

```python
class VerticalMode(str, Enum):
    REALTY = "realty"      # املاک
    EXPO = "expo"          # نمایشگاه/تراول
    SUPPORT = "support"    # پشتیبانی
    NONE = "none"          # هیچکدام

DEEP_LINK_PATTERNS = {
    VerticalMode.REALTY: [
        r'\bstart[_\s-]?realty\b',
        r'\brealestate\b',
        r'\bproperty\b',
    ],
    VerticalMode.EXPO: [
        r'\bstart[_\s-]?expo\b',
        r'\bstart[_\s-]?travel\b',
        r'\bstart[_\s-]?clinic\b',
    ],
}
```

---

## تست کردن

### Test 1: ارسال پیام از واتساپ

1. شماره‌ای که QR code را اسکن کرده در واتساپ باز کنید
2. پیام بفرستید: `start_realty`
3. در لاگ backend ببینید:

```bash
docker-compose logs -f backend | grep "Deep link"

# خروجی:
# INFO - Deep link detected: realty (pattern: start_realty)
# INFO - Set user 971501234567 to mode: realty
```

### Test 2: چک کردن Redis Session

```bash
docker-compose exec redis redis-cli

# در redis-cli:
KEYS user:*:mode
GET user:971505037158:mode
# خروجی: "realty"
```

---

## عیب‌یابی

### مشکل 1: QR Code ظاهر نمیشه

```bash
# چک کنید Waha اجرا شده باشد
docker ps | grep waha

# اگر نبود، دوباره start کنید
docker-compose up -d waha

# لاگ‌ها را ببینید
docker-compose logs waha
```

### مشکل 2: پیام‌ها دریافت نمیشه

```bash
# چک کنید webhook URL درست باشد
docker-compose exec waha curl http://backend:8000/health

# باید 200 OK برگردونه
```

### مشکل 3: QR Code expire شد

```bash
# Restart کنید Waha
docker-compose restart waha

# QR جدید ظاهر میشه
docker-compose logs -f waha
```

---

## مقایسه با Meta/Twilio

| ویژگی | Waha | Meta | Twilio |
|------|------|------|--------|
| هزینه | رایگان | رایگان (محدود) | 0.005$/msg |
| نیاز به تایید | خیر | بله (Business) | بله |
| زمان راه‌اندازی | 5 دقیقه | 2-5 روز | 1 روز |
| محدودیت پیام | نامحدود | 1000/روز | نامحدود |
| دکمه interactive | خیر | بله | محدود |
| Voice message | بله | بله | بله |
| Image support | بله | بله | بله |

---

## Best Practices

### 1. Backup Session

```bash
# Backup کردن Waha session (هر هفته یکبار)
docker-compose exec waha tar -czf /tmp/waha-backup.tar.gz /app/.waha
docker cp artinrealty-waha:/tmp/waha-backup.tar.gz ./backups/
```

### 2. Monitoring

```bash
# چک کردن health Waha
curl http://SERVER_IP:3001/health

# باید برگردونه:
# {"status": "ok"}
```

### 3. Multi-Device Support

اگر میخواید چند شماره مختلف داشته باشید:

```bash
# Session جدید بسازید
curl -X POST http://localhost:3001/api/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"name": "tenant_123"}'

# QR Code جدید می‌گیرید
```

---

## لینک‌های مفید

- 📚 **Waha Documentation**: https://waha.devlike.pro
- 💻 **GitHub Repo**: https://github.com/devlikeapro/waha
- 🐛 **Issues**: https://github.com/devlikeapro/waha/issues
- 💬 **Telegram Support**: https://t.me/waha_devlike

---

## نتیجه

حالا شما یک سیستم WhatsApp کاملاً رایگان و بدون محدودیت دارید که:

- ✅ Deep links دارد (start_realty, start_expo, etc.)
- ✅ Multi-vertical routing دارد (هر user به vertical خودش route میشه)
- ✅ Session persistence دارد (Redis)
- ✅ Voice/Image support دارد
- ✅ بدون نیاز به تایید Meta کار می‌کنه

**تمام!** 🎉
