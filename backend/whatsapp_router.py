"""
WhatsApp Gateway Router - Multi-Tenant Deep Link Router
========================================================

سیستم روتینگ پیام‌های واتساپ برای چند تنانت:
- یک شماره واتساپ (Gateway) مشترک بین ۱۰۰۰+ ایجنت
- هر ایجنت دیپ لینک خاص خودش رو به مشتری میده
- مشتری با کلیک روی لینک به یک تنانت قفل میشه
- تمام پیام‌های بعدی اون مشتری به همون تنانت روت میشه
"""

import os
import json
import re
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, BackgroundTasks, Header
import httpx

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Router")

# Configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000/api/webhook/waha")
WAHA_API_URL = os.getenv("WAHA_API_URL", "http://waha:3000/api")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "waha_artinsmartrealty_secure_key_2024")
DB_FILE = Path("/app/data/user_tenant_map.json")

# Ensure data directory exists
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

# FastAPI app
app = FastAPI(title="WhatsApp Gateway Router", version="2.0.0")


# --- Health Check Endpoint ---
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "router"}


# --- حافظه ماندگار (Persistent Storage) ---
def load_map():
    """بارگذاری نقشه user → tenant از فایل"""
    if not DB_FILE.exists():
        return {}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading map: {e}")
        return {}


def save_map(phone: str, tenant_id: int):
    """ذخیره قفل کاربر به تنانت"""
    data = load_map()
    # حذف @c.us برای یکدست سازی
    clean_phone = phone.replace('@c.us', '')
    data[clean_phone] = str(tenant_id)
    
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"🔒 LOCKED: User {clean_phone} → Tenant {tenant_id}")
    except Exception as e:
        logger.error(f"Error saving map: {e}")


def get_tenant_for_user(phone: str) -> Optional[str]:
    """پیدا کردن تنانت قفل شده برای یک کاربر"""
    clean_phone = phone.replace('@c.us', '')
    mapping = load_map()
    return mapping.get(clean_phone)


# --- ارسال پیام از طریق WAHA ---
async def send_waha_message(phone: str, message: str):
    """ارسال پیام واتساپ"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{WAHA_API_URL}/sendText",
                headers={
                    "X-Api-Key": WAHA_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "session": "default",
                    "chatId": phone if "@c.us" in phone else f"{phone}@c.us",
                    "text": message
                }
            )
            response.raise_for_status()
            logger.info(f"📤 Sent message to {phone}")
    except Exception as e:
        logger.error(f"Error sending WAHA message: {e}")


# --- فوروارد به بک‌اند ---
async def forward_to_backend(data: dict, tenant_id: str):
    """ارسال پیام به بک‌اند با هدر Tenant-ID"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-ID": str(tenant_id),
                "X-Router-Source": "whatsapp-gateway"
            }
            
            response = await client.post(
                BACKEND_API_URL,
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Forwarded to Tenant {tenant_id}")
            else:
                logger.error(f"Backend error {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to forward to backend: {e}")


# --- وب‌هوک اصلی ---
@app.post("/webhook/waha")
async def waha_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    نقطه ورودی پیام‌های WAHA
    
    لاجیک:
    1. اگر پیام شامل start_realty_{ID} بود → قفل کاربر به اون تنانت
    2. اگر کاربر قبلاً قفل شده → روت کن به تنانت قفل شده
    3. اگر کاربر ناشناس → پیام راهنما بفرست
    """
    try:
        data = await request.json()
        payload = data.get("payload", {})
        event = data.get("event", "")
        
        # فقط پیام‌های دریافتی
        if event != "message":
            return {"status": "ignored", "reason": "not_message_event"}
        
        # استخراج شماره فرستنده
        from_number = payload.get("from", "")
        if not from_number or "@c.us" not in from_number:
            return {"status": "ignored", "reason": "no_sender"}
        
        phone = from_number.split("@")[0]
        body = payload.get("body", "").strip()
        
        logger.info(f"📨 Message from {phone}: {body[:50]}...")
        
        # 1️⃣ بررسی دیپ لینک (Deep Link Detection)
        # الگو: start_realty_2 یا start_realty_105
        match = re.search(r"start_realty_(\d+)", body, re.IGNORECASE)
        
        target_tenant_id = None
        
        if match:
            # دیپ لینک جدید! → قفل کاربر
            target_tenant_id = match.group(1)
            save_map(phone, int(target_tenant_id))
            logger.info(f"🔗 New Deep Link: Tenant {target_tenant_id}")
        else:
            # دیپ لینک نبود → چک کن قبلاً قفل شده؟
            target_tenant_id = get_tenant_for_user(phone)
        
        # 2️⃣ روتینگ
        if target_tenant_id:
            # پیام را به بک‌اند بفرست (با Tenant-ID در هدر)
            background_tasks.add_task(forward_to_backend, data, target_tenant_id)
            return {
                "status": "routed",
                "tenant_id": target_tenant_id,
                "user": phone
            }
        else:
            # کاربر ناشناس (هنوز دیپ لینک نزده)
            logger.warning(f"⛔ Unknown user {phone}. Sending help message.")
            
            # پیام راهنما (چند زبانه)
            help_msg = (
                "👋 مرحبا! لطفاً از لینک ارسالی توسط مشاور املاک خود استفاده کنید.\n\n"
                "Hello! Please use the link provided by your real estate agent.\n\n"
                "مرحبًا! يرجى استخدام الرابط الذي قدمه وكيل العقارات الخاص بك."
            )
            background_tasks.add_task(send_waha_message, from_number, help_msg)
            
            return {
                "status": "unknown_user",
                "user": phone,
                "action": "sent_help_message"
            }

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return {"status": "error", "detail": str(e)}


# --- API endpoints مدیریتی ---
@app.get("/health")
async def health_check():
    """وضعیت سلامت روتر"""
    mappings = load_map()
    return {
        "status": "healthy",
        "service": "whatsapp-gateway-router",
        "total_locked_users": len(mappings),
        "unique_tenants": len(set(mappings.values()))
    }


@app.get("/router/stats")
async def get_stats():
    """آمار روتینگ"""
    mappings = load_map()
    return {
        "total_locked_users": len(mappings),
        "unique_tenants": len(set(mappings.values())),
        "mappings": mappings
    }


@app.get("/router/user/{phone}")
async def get_user_tenant(phone: str):
    """چک کردن قفل یک کاربر"""
    clean_phone = phone.replace('+', '').replace('@c.us', '')
    tenant_id = get_tenant_for_user(clean_phone)
    
    return {
        "phone": clean_phone,
        "locked_to_tenant": tenant_id,
        "status": "active_session" if tenant_id else "no_session"
    }


@app.post("/router/unlock/{phone}")
async def unlock_user(phone: str):
    """باز کردن قفل یک کاربر (endpoint مدیریتی)"""
    clean_phone = phone.replace('+', '').replace('@c.us', '')
    mappings = load_map()
    
    if clean_phone in mappings:
        tenant_id = mappings[clean_phone]
        del mappings[clean_phone]
        
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
        
        logger.info(f"🔓 UNLOCKED: User {clean_phone} from Tenant {tenant_id}")
        
        return {
            "status": "unlocked",
            "phone": clean_phone,
            "was_locked_to": tenant_id
        }
    else:
        return {
            "status": "not_found",
            "phone": clean_phone
        }



@app.post("/router/generate-link")
async def generate_deep_link(request: Request):
    """
    ساخت اتوماتیک دیپ لینک واتساپ با شماره مشتری
    
    Body:
    {
        "tenant_id": 2,
        "customer_phone": "971501234567",
        "gateway_number": "971557357753",
        "message": "سلام" (optional)
    }
    
    Returns:
    {
        "deep_link": "https://wa.me/971557357753?text=start_realty_2",
        "qr_code_url": "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=...",
        "short_link": "https://wa.me/971557357753?text=start_realty_2"
    }
    """
    try:
        data = await request.json()
        tenant_id = data.get("tenant_id")
        customer_phone = data.get("customer_phone", "").replace("+", "")
        gateway_number = data.get("gateway_number", "971557357753").replace("+", "")
        custom_message = data.get("message", "")
        
        if not tenant_id:
            return {
                "status": "error",
                "detail": "tenant_id is required"
            }
        
        start_command = f"start_realty_{tenant_id}"
        if custom_message:
            message_text = f"{start_command}\n{custom_message}"
        else:
            message_text = start_command
        
        import urllib.parse
        encoded_message = urllib.parse.quote(message_text)
        
        deep_link = f"https://wa.me/{gateway_number}?text={encoded_message}"
        
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(deep_link)}"
        
        logger.info(f"📲 GENERATED LINK: Tenant {tenant_id} → Customer {customer_phone}")
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "customer_phone": customer_phone,
            "gateway_number": gateway_number,
            "deep_link": deep_link,
            "qr_code_url": qr_code_url,
            "short_link": deep_link,
            "preview_text": message_text
        }
        
    except Exception as e:
        logger.exception(f"Error generating link: {e}")
        return {
            "status": "error",
            "detail": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

