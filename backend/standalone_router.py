"""
ArtinSmartAgent - Standalone Multi-Vertical WhatsApp Router
استقلال کامل از بک‌اند - Router مستقل با حافظه دائمی

این سرویس:
- روی سرور جداگانه اجرا می‌شود (پورت 5000)
- پیام‌های WhatsApp را از WAHA دریافت می‌کند
- به ساب‌دامین‌های مختلف route می‌کند
- حافظه دائم دارد (JSON + Redis)
- پیام‌های شخصی را فیلتر می‌کند

استفاده:
    python standalone_router.py
    
    یا با Docker:
    docker run -p 5000:5000 -v ./user_routes.json:/app/user_routes.json artinrouter
"""

from fastapi import FastAPI, Request
import httpx
import uvicorn
import json
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("StandaloneRouter")

app = FastAPI(title="ArtinSmartAgent Router", version="1.0")

# ---------------------------------------------------------
# 1. تنظیمات سرویس‌ها (ساب‌دامین‌ها)
# ---------------------------------------------------------
SERVICES = {
    "realty": "https://realty.artinsmartagent.com/api/webhook/waha",
    "travel": "https://travel.artinsmartagent.com/api/webhook/waha",
    "expo":   "https://expo.artinsmartagent.com/api/webhook/waha",
    "clinic": "https://clinic.artinsmartagent.com/api/webhook/waha"
}

# فایل دیتابیس (JSON) برای حافظه دائمی
DB_FILE = os.getenv("ROUTES_DB_FILE", "user_routes.json")

# ---------------------------------------------------------
# 2. مدیریت حافظه (Load/Save Routes)
# ---------------------------------------------------------
def load_routes() -> Dict[str, Dict[str, Any]]:
    """
    بارگذاری روت‌های کاربران از فایل JSON.
    
    Returns:
        {
            "971501234567": {
                "service": "realty",
                "agent_id": "101",
                "timestamp": "2025-12-14T23:00:00"
            }
        }
    """
    if not os.path.exists(DB_FILE):
        logger.info(f"📁 Creating new routes database: {DB_FILE}")
        return {}
    
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"✅ Loaded {len(data)} user routes from {DB_FILE}")
            return data
    except Exception as e:
        logger.error(f"❌ Error loading routes: {e}")
        return {}

def save_route(phone: str, service: str, agent_id: Optional[str] = None):
    """
    ذخیره یا آپدیت روت یک کاربر.
    
    Args:
        phone: شماره تلفن (بدون @c.us)
        service: نام سرویس (realty, travel, expo, clinic)
        agent_id: شناسه ایجنت (اختیاری)
    """
    data = load_routes()
    
    route_info = {
        "service": service,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if agent_id:
        route_info["agent_id"] = agent_id
    
    data[phone] = route_info
    
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        agent_str = f" (Agent: {agent_id})" if agent_id else ""
        logger.info(f"✅ User {phone} LOCKED to {service}{agent_str}")
    except Exception as e:
        logger.error(f"❌ Error saving route: {e}")

def get_route(phone: str) -> Optional[Dict[str, Any]]:
    """
    دریافت روت ذخیره شده یک کاربر.
    
    Returns:
        {"service": "realty", "agent_id": "101", "timestamp": "..."}
        یا None اگر کاربر روتی نداشته باشد
    """
    routes = load_routes()
    return routes.get(phone)

# ---------------------------------------------------------
# 3. وب‌هوک اصلی (دریافت از WAHA)
# ---------------------------------------------------------
@app.post("/webhook")
async def waha_webhook(request: Request):
    """
    وب‌هوک اصلی - تمام پیام‌های WhatsApp از WAHA به اینجا می‌آید.
    
    فلوی کاری:
    1. چک کردن deep link (start_realty_*, start_travel_*, ...)
    2. چک کردن حافظه (آیا کاربر قبلاً لینک شده؟)
    3. فیلتر پیام‌های شخصی (اگر نه لینک زده و نه در حافظه باشد)
    """
    try:
        data = await request.json()
        payload = data.get("payload", {})
        
        # فیلتر پیام‌های سیستمی (status, ack, group messages)
        if "from" not in payload or "@c.us" not in payload.get("from", ""):
            return {"status": "ignored_system"}
        
        phone = payload["from"].split("@")[0]  # استخراج شماره
        body = payload.get("body", "").strip()
        command = body.lower()  # کوچک برای مقایسه راحت
        
        logger.info(f"📨 Message from {phone}: {body[:50]}...")
        
        # -------------------------------------------------------
        # سناریو 1: Deep Link Command (کلیک روی لینک)
        # -------------------------------------------------------
        target_service = None
        agent_id = None
        
        # تشخیص سرویس از روی پیشوند start_
        if command.startswith("start_realty"):
            target_service = "realty"
            # استخراج agent ID: start_realty_101 → agent_id = "101"
            parts = command.split("_")
            if len(parts) >= 3:
                agent_id = "_".join(parts[2:])  # پشتیبانی از ID با underscoreهای متعدد
        
        elif command.startswith("start_travel"):
            target_service = "travel"
            parts = command.split("_")
            if len(parts) >= 3:
                agent_id = "_".join(parts[2:])
        
        elif command.startswith("start_expo"):
            target_service = "expo"
            parts = command.split("_")
            if len(parts) >= 3:
                agent_id = "_".join(parts[2:])
        
        elif command.startswith("start_clinic"):
            target_service = "clinic"
            parts = command.split("_")
            if len(parts) >= 3:
                agent_id = "_".join(parts[2:])
        
        # اگر deep link تشخیص داده شد
        if target_service:
            save_route(phone, target_service, agent_id)
            await forward_to_service(target_service, data, agent_id)
            
            return {
                "status": "new_assignment",
                "phone": phone,
                "service": target_service,
                "agent_id": agent_id
            }
        
        # -------------------------------------------------------
        # سناریو 2: کاربر قبلی (Persistent Routing)
        # -------------------------------------------------------
        route = get_route(phone)
        
        if route:
            service_name = route.get("service")
            stored_agent_id = route.get("agent_id")
            
            if service_name in SERVICES:
                await forward_to_service(service_name, data, stored_agent_id)
                
                return {
                    "status": "forwarded",
                    "phone": phone,
                    "service": service_name,
                    "agent_id": stored_agent_id
                }
        
        # -------------------------------------------------------
        # سناریو 3: پیام شخصی (فیلتر شده)
        # -------------------------------------------------------
        logger.info(f"👤 Personal message from {phone} - IGNORED by bot")
        
        return {
            "status": "ignored_personal",
            "phone": phone,
            "reason": "No service route assigned"
        }
    
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------
# 4. Forward به ساب‌دامین‌ها
# ---------------------------------------------------------
async def forward_to_service(service_name: str, data: Dict, agent_id: Optional[str] = None):
    """
    ارسال پیام به سرویس مقصد.
    
    Args:
        service_name: نام سرویس (realty, travel, ...)
        data: کل پیلود دریافتی از WAHA
        agent_id: شناسه ایجنت (برای لاگ)
    """
    url = SERVICES.get(service_name)
    
    if not url:
        logger.error(f"❌ Unknown service: {service_name}")
        return
    
    # اضافه کردن metadata برای بک‌اند (اختیاری)
    if "metadata" not in data:
        data["metadata"] = {}
    
    data["metadata"]["routed_by"] = "standalone_router"
    data["metadata"]["agent_id"] = agent_id
    data["metadata"]["routed_at"] = datetime.utcnow().isoformat()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, timeout=15)
            
            agent_str = f" (Agent: {agent_id})" if agent_id else ""
            
            if response.status_code == 200:
                logger.info(f"📤 Forwarded to {service_name}{agent_str} - OK")
            else:
                logger.warning(f"⚠️ {service_name} returned {response.status_code}")
        
        except httpx.TimeoutException:
            logger.error(f"⏱️ Timeout forwarding to {service_name}")
        except httpx.ConnectError:
            logger.error(f"🔌 Connection failed to {service_name} at {url}")
        except Exception as e:
            logger.error(f"❌ Failed to forward to {service_name}: {e}")

# ---------------------------------------------------------
# 5. Health Check & Stats
# ---------------------------------------------------------
@app.get("/health")
async def health_check():
    """بررسی سلامت سرویس"""
    routes = load_routes()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": list(SERVICES.keys()),
        "total_users": len(routes)
    }

@app.get("/stats")
async def get_stats():
    """آمار استفاده از سرویس‌ها"""
    routes = load_routes()
    
    stats = {
        "total_users": len(routes),
        "by_service": {},
        "by_agent": {},
        "recent_users": []
    }
    
    # شمارش بر اساس سرویس و ایجنت
    for phone, route_data in routes.items():
        service = route_data.get("service", "unknown")
        agent = route_data.get("agent_id", "default")
        
        # Count by service
        if service not in stats["by_service"]:
            stats["by_service"][service] = 0
        stats["by_service"][service] += 1
        
        # Count by agent
        agent_key = f"{service}_{agent}"
        if agent_key not in stats["by_agent"]:
            stats["by_agent"][agent_key] = 0
        stats["by_agent"][agent_key] += 1
    
    # لیست 10 کاربر اخیر
    sorted_routes = sorted(
        routes.items(),
        key=lambda x: x[1].get("timestamp", ""),
        reverse=True
    )
    
    stats["recent_users"] = [
        {
            "phone": phone[-4:],  # فقط 4 رقم آخر (امنیت)
            "service": data.get("service"),
            "agent_id": data.get("agent_id"),
            "timestamp": data.get("timestamp")
        }
        for phone, data in sorted_routes[:10]
    ]
    
    return stats

@app.get("/routes")
async def list_routes():
    """لیست تمام روت‌ها (برای دیباگ)"""
    routes = load_routes()
    
    # پنهان کردن شماره‌های کامل
    sanitized = {
        f"***{phone[-4:]}": data
        for phone, data in routes.items()
    }
    
    return {
        "total": len(routes),
        "routes": sanitized
    }

# ---------------------------------------------------------
# 6. Root Endpoint
# ---------------------------------------------------------
@app.get("/")
async def root():
    """صفحه خانه"""
    return {
        "service": "ArtinSmartAgent Router",
        "version": "1.0",
        "description": "Multi-vertical WhatsApp message router with persistent memory",
        "endpoints": {
            "webhook": "/webhook (POST)",
            "health": "/health (GET)",
            "stats": "/stats (GET)",
            "routes": "/routes (GET)"
        },
        "supported_services": list(SERVICES.keys())
    }

# ---------------------------------------------------------
# 7. اجرا
# ---------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("ROUTER_PORT", 5000))
    host = os.getenv("ROUTER_HOST", "0.0.0.0")
    
    logger.info("=" * 60)
    logger.info("🚀 ArtinSmartAgent Standalone Router")
    logger.info("=" * 60)
    logger.info(f"📡 Listening on: {host}:{port}")
    logger.info(f"📁 Routes database: {DB_FILE}")
    logger.info(f"🎯 Active services: {', '.join(SERVICES.keys())}")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
