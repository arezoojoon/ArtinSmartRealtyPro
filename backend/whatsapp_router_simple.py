"""
WhatsApp Gateway Router - Multi-Tenant Deep Link Router
========================================================
مغز متفکر سیستم - هدایت پیام‌ها به ایجنت‌های مختلف
"""

import os
import json
import re
import logging
import httpx
from fastapi import FastAPI, Request, BackgroundTasks

# تنظیمات
app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Router")

# فایل دیتابیس برای ذخیره اتصال مشتری به ایجنت
DB_FILE = "user_tenant_map.json"
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000/api/webhook/whatsapp")

# --- مدیریت حافظه (Load/Save) ---
def load_map():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_map(phone, tenant_id):
    data = load_map()
    data[phone] = str(tenant_id)
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)
    logger.info(f"🔒 User {phone} LOCKED to Tenant {tenant_id}")

# --- لاجیک اصلی ---
@app.post("/webhook/waha")
async def waha_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        payload = data.get("payload", {})
        
        # 1. استخراج شماره فرستنده
        if "from" not in payload or "@c.us" not in payload["from"]:
            return {"status": "ignored"}
            
        phone = payload["from"].split("@")[0]
        body = payload.get("body", "").strip()
        
        # 2. بررسی دیپ‌لینک (Deep Link Detection)
        # مثال: start_realty_2 یا start_realty_105
        match = re.search(r"start_realty_(\d+)", body, re.IGNORECASE)
        
        target_tenant_id = None
        
        if match:
            # اگر لینک زد، تننت جدید را استخراج و قفل کن
            target_tenant_id = match.group(1)
            save_map(phone, target_tenant_id)
            logger.info(f"🔗 New Deep Link Detected: Tenant {target_tenant_id}")
        else:
            # اگر لینک نزد، ببین قبلاً مال کی بوده؟
            mapping = load_map()
            target_tenant_id = mapping.get(phone)

        # 3. هدایت پیام (Routing)
        if target_tenant_id:
            # پیام را به بک‌اند اصلی بفرست + هدر مخصوص
            background_tasks.add_task(forward_to_backend, data, target_tenant_id)
            return {"status": f"routed_to_{target_tenant_id}"}
        else:
            # کاربر ناشناس (هنوز لینک نزده)
            logger.warning(f"⛔ Unknown user {phone}. Ignoring.")
            # اینجا می‌تونی یک پیام پیش‌فرض بفرستی: "لطفا از لینک ایجنت خود استفاده کنید"
            return {"status": "unknown_user"}

    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error"}

async def forward_to_backend(data, tenant_id):
    async with httpx.AsyncClient() as client:
        try:
            # نکته کلیدی: Tenant-ID را در هدر می‌فرستیم
            headers = {"X-Tenant-ID": str(tenant_id)}
            await client.post(BACKEND_API_URL, json=data, headers=headers)
            logger.info(f"✅ Forwarded to Tenant {tenant_id}")
        except Exception as e:
            logger.error(f"Failed to forward to backend: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    mapping = load_map()
    return {
        "status": "healthy",
        "service": "whatsapp-gateway-router",
        "total_locked_users": len(mapping),
        "unique_tenants": len(set(mapping.values()))
    }

@app.get("/router/stats")
async def get_stats():
    """دریافت آمار روتر"""
    mapping = load_map()
    return {
        "total_users": len(mapping),
        "mappings": mapping
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
