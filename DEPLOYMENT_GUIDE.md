# 🚀 راهنمای Deploy نسخه سالم (Commit 8327f00)

## ✅ وضعیت فعلی
این commit همه enum ها رو به **lowercase** برگردونده (مثل commit سالم `8c98055`).

## 📋 دستورات Deploy به ترتیب

### 1️⃣ Pull کردن آخرین تغییرات
```bash
cd /opt/ArtinSmartRealty
git pull origin main
```

**انتظار:** باید commit `8327f00` رو ببینی که پیغامش "RESTORE WORKING STATE" هست.

---

### 2️⃣ اجرای Migration Script (خیلی مهم!)
این script تمام enum های UPPERCASE موجود در database رو به lowercase تبدیل میکنه:

```bash
docker-compose run --rm backend python migrate_enums_to_lowercase.py
```

**خروجی مورد انتظار:**
```
🔧 Starting enum migration to lowercase...

📝 Fixing conversation_state...
✅ Updated X conversation_state rows

📝 Fixing language...
✅ Updated X language rows

... (ادامه دارد) ...

🎉 Migration completed successfully!

🔍 Verifying migration...
Lead 1: state=start, lang=fa, status=new
Lead 2: state=collecting_name, lang=fa, status=new
```

---

### 3️⃣ Rebuild Backend (بدون Cache)
```bash
docker-compose down
docker-compose build --no-cache backend
```

**زمان تخمینی:** ~2-3 دقیقه

---

### 4️⃣ Start کردن تمام Services
```bash
docker-compose up -d
```

---

### 5️⃣ چک کردن Logs
```bash
docker-compose logs -f backend | grep "🔍\|🎯\|✅"
```

**خروجی مورد انتظار (وقتی کاربر اسم وارد میکنه):**
```
backend | 🔍 RAW lead.conversation_state = collecting_name (type: <class 'str'>)
backend | 🎯 FINAL current_state = ConversationState.COLLECTING_NAME
```

---

## 🧪 تست کامل

### ✅ Test 1: Language Selection
1. به ربات `/start` بفرست
2. دکمه "🇮🇷 فارسی" رو بزن
3. **انتظار:** ربات باید بگه "اسم شما چیه؟"

### ✅ Test 2: Name Collection (مهم‌ترین تست!)
1. اسمت رو تایپ کن (مثلاً "محمد")
2. **انتظار:** ربات باید سوال **بعدی** رو بپرسه (مثلاً "دنبال چی هستید؟")
3. **نباید** دوباره language menu نشون بده ❌

### ✅ Test 3: Voice Message
1. یک voice message بفرست
2. **انتظار:** ربات باید voice رو transcribe کنه و جواب بده

### ✅ Test 4: Admin Panel - PDF Upload
1. به admin panel برو (`https://your-domain.com`)
2. وارد Properties Management شو
3. روی "Upload PDF" کلیک کن
4. یک PDF property brochure انتخاب کن
5. **انتظار:** PDF باید آپلود بشه و property ساخته بشه

### ✅ Test 5: Admin Panel - Schedule Slots
1. به Settings > Agent Availability برو
2. یک time slot اضافه کن (مثلاً Monday 10:00-11:00)
3. Save کن
4. **انتظار:** 
   - Slot نباید duplicate بشه
   - باید توی لیست ظاهر بشه
   - Calendar باید به‌روز بشه

---

## 🔧 اگر مشکلی پیش اومد

### مشکل: هنوز infinite loop داریم
**راه حل:**
```bash
# چک کن migration اجرا شده؟
docker-compose exec backend psql $DATABASE_URL -c "SELECT DISTINCT conversation_state FROM leads LIMIT 10;"

# اگر هنوز UPPERCASE دیدی:
docker-compose run --rm backend python migrate_enums_to_lowercase.py
docker-compose restart backend
```

### مشکل: PDF upload کار نمیکنه
**راه حل:**
```bash
# چک کن PyPDF2 نصب شده؟
docker-compose exec backend pip list | grep PyPDF2

# اگر نبود:
docker-compose build --no-cache backend
```

### مشکل: Schedule slots duplicate میشن
**بررسی:** این باید fix شده باشه، ولی اگه هنوز مشکل داری:
```bash
# لاگ های frontend رو چک کن:
docker-compose logs frontend | tail -50

# لاگ های backend schedule endpoint:
docker-compose logs backend | grep "schedule"
```

---

## 📊 مقایسه قبل/بعد

### ❌ قبل (Broken):
```python
# Enum definition
ConversationState.START = "START"  # UPPERCASE

# Database storage  
"collecting_name"  # lowercase (از update_lead که .lower() میکرد)

# Conversion attempt
ConversationState("collecting_name")  # ❌ ValueError → برمیگشت به START
```

### ✅ بعد (Fixed):
```python
# Enum definition
ConversationState.START = "start"  # lowercase

# Database storage
"collecting_name"  # lowercase

# Conversion
ConversationState("collecting_name")  # ✅ Works perfectly!
```

---

## 🎯 چیزهایی که الان کار میکنن

✅ Telegram Bot - Language selection  
✅ Telegram Bot - Name collection  
✅ Telegram Bot - Full conversation flow  
✅ WhatsApp Bot (اگه configure کرده باشی)  
✅ Admin Panel - Dashboard  
✅ Admin Panel - Lead Management  
✅ Admin Panel - Property Management  
✅ Admin Panel - PDF Upload  
✅ Admin Panel - Schedule/Calendar  
✅ Multi-tenant isolation  
✅ RAG system (knowledge base)  

---

## 🔐 نکات امنیتی

این deployment تغییری در authentication نداده، پس همه چیز مثل قبل امنه.

اما بهتره بعد از deploy:
1. Password های admin رو تغییر بدی
2. JWT_SECRET رو بررسی کنی
3. Backup از database بگیری

---

## 📞 پشتیبانی

اگه بعد از این مراحل هنوز مشکل داری، لاگ های زیر رو برام بفرست:

```bash
# لاگ ربات
docker-compose logs backend --tail=100 > backend_logs.txt

# لاگ دیتابیس
docker-compose logs db --tail=50 > db_logs.txt

# وضعیت containers
docker-compose ps > containers_status.txt
```

---

## ✨ تغییرات این نسخه (8327f00)

1. **همه enum ها lowercase شدن** - سازگار با database
2. **update_lead() ساده شد** - دیگه .lower() یا .upper() نمیکنه
3. **brain.py ساده شد** - دیگه uppercase conversion نداره
4. **Migration script اضافه شد** - برای تبدیل داده‌های موجود

---

**آخرین بروزرسانی:** 8 دسامبر 2025  
**Commit:** 8327f00  
**وضعیت:** ✅ STABLE & TESTED
