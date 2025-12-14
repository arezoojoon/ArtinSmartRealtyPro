# راه‌حل: دیتابیس اجرا نیست

خطای شما: `[WinError 1225] The remote computer refused the network connection`

این یعنی PostgreSQL در حال اجرا نیست!

## ✅ راه‌حل سریع

### گزینه 1: Docker (آسان‌ترین) 🐳

```powershell
# 1. ایجاد فایل .env
Copy-Item .env.example .env

# 2. ویرایش .env و تنظیم DB_PASSWORD
# (می‌توانید postgres نگه دارید برای development)

# 3. اجرای فقط دیتابیس
docker-compose up -d db

# 4. چک کردن وضعیت
docker-compose ps

# 5. اجرای migration
python migrate_property_images.py
```

### گزینه 2: PostgreSQL محلی

اگر PostgreSQL محلی نصب است:

```powershell
# 1. شروع PostgreSQL service
net start postgresql-x64-15

# 2. ایجاد دیتابیس
psql -U postgres -c "CREATE DATABASE artinrealty;"

# 3. ایجاد .env
Copy-Item .env.example .env

# 4. ویرایش .env
# DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/artinrealty

# 5. اجرای migration
python migrate_property_images.py
```

### گزینه 3: بدون Migration (موقت)

اگر نمی‌توانید دیتابیس راه‌اندازی کنید، فیلدها از قبل در schema تعریف شده‌اند!

```python
# در database.py خط 328-338
image_urls = Column(JSON, default=list)
image_files = Column(JSON, default=list)
primary_image = Column(String(512), nullable=True)
full_description = Column(Text, nullable=True)
is_urgent = Column(Boolean, default=False)
```

فقط کافیست دیتابیس را یکبار بسازید:

```powershell
# با SQLAlchemy
cd backend
python -c "from database import init_db; import asyncio; asyncio.run(init_db())"
```

## 🎯 توصیه

**برای Development:** استفاده از Docker
```powershell
docker-compose up -d db
```

**برای Production:** PostgreSQL server اختصاصی

## ✅ بعد از راه‌اندازی

وقتی دیتابیس اجرا شد، این دستور باید موفق شود:
```powershell
python migrate_property_images.py
```

نتیجه:
```
✅ Migration completed successfully!
```
