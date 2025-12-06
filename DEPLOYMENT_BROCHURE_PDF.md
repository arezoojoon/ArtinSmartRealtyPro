# Deployment Instructions - Add brochure_pdf Field

## خطا
وقتی PDF آپلود می‌شه، فایل آپلود میشه ولی فیلد `brochure_pdf` در دیتابیس ذخیره نمیشه.

## علت
فیلد `brochure_pdf` در جدول `tenant_properties` وجود نداره.

## راه حل
اجرای migration برای اضافه کردن ستون جدید.

---

## دستورات Deployment

### 1️⃣ Pull آخرین تغییرات
```bash
ssh root@srv1151343.hstgr.io
cd /root/ArtinSmartRealty
git pull origin main
```

### 2️⃣ اجرای Migration
```bash
# وارد container postgres شوید
docker-compose exec postgres psql -U artinrealty -d artinrealty

# اجرای دستور SQL
ALTER TABLE tenant_properties ADD COLUMN IF NOT EXISTS brochure_pdf VARCHAR(512);

# خروج از postgres
\q
```

### 3️⃣ Restart Backend
```bash
docker-compose restart backend
```

### 4️⃣ تست
1. وارد پنل بشید: https://realty.artinsmartagent.com
2. یک property ویرایش کنید
3. PDF آپلود کنید
4. Save کنید
5. دوباره Edit کنید - باید نشانگر "PDF uploaded successfully" رو ببینید

---

## تغییرات انجام شده

**Backend:**
- `backend/database.py`: اضافه شدن فیلد `brochure_pdf` به model `TenantProperty`
- `migrations/add_brochure_pdf.sql`: SQL script
- `migrations/add_brochure_pdf_migration.py`: Python migration script

**Files:**
- Commit: `4b110fb`

---

## بررسی موفقیت Migration

```sql
-- چک کنید ستون اضافه شده
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name='tenant_properties' AND column_name='brochure_pdf';
```

باید نتیجه زیر رو ببینید:
```
 column_name  | data_type 
--------------+-----------
 brochure_pdf | character varying
```

---

## بعد از Migration

فیچر PDF Upload به طور کامل کار می‌کنه:
1. ✅ آپلود فایل PDF (تا 10MB)
2. ✅ استخراج خودکار اطلاعات (قیمت، اتاق، متراژ، لوکیشن)
3. ✅ Auto-fill فرم
4. ✅ ذخیره URL در دیتابیس
5. ✅ نمایش badge موفقیت
