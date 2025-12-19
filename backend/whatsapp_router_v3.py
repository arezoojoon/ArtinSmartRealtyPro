"""
WhatsApp Gateway Router V3 - Multi-Tenant + Multi-Vertical Deep Link Router
===========================================================================

ARCHITECTURE:
- یک شماره واتساپ gateway برای 1000+ tenant
- Support برای multiple verticals: Realty, Expo, Support
- Session management با Redis (24h TTL)
- Personal vs Bot message filtering
- Deep link format: wa.me/{gateway}?text=start_{vertical}_{tenant_id}

FLOW:
1. User clicks link: wa.me/971557357753?text=start_realty_123
2. Router detects: vertical=realty, tenant=123
3. Creates session in Redis (24h expiry)
4. Routes message to backend with headers: X-Tenant-ID, X-Vertical-Mode
5. All subsequent messages from this user → same tenant (until session expires)
6. Personal messages (no session, no start_) → ignored

PERSONAL MESSAGE FILTERING:
- Friend sends: "سلام کجایی؟"
  → No session? No start_? → IGNORE (log only)
  → You respond manually from your phone
- Customer clicks deep link: start_realty_123
  → Creates session → Bot responds
- Customer continues: "میخوام ملک ببینم"
  → Has session? → Bot processes
"""

import os
import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, Request, BackgroundTasks, Header, HTTPException
import httpx
import redis.asyncio as aioredis

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RouterV3")

# Configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000/api/webhook/waha")
WAHA_API_URL = os.getenv("WAHA_API_URL", "http://waha:3000/api")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "waha_artinsmartrealty_secure_key_2024")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/1")
SESSION_TTL = int(os.getenv("SESSION_TTL", "86400"))  # 24 hours

# FastAPI app
app = FastAPI(title="WhatsApp Gateway Router V3", version="3.0.0")

# Redis connection
redis_client: Optional[aioredis.Redis] = None


@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection on startup"""
    global redis_client
    try:
        redis_client = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Redis connected for router sessions")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.warning("⚠️ Router will operate in degraded mode (stateless)")


@app.on_event("shutdown")
async def shutdown_event():
    """Close Redis connection on shutdown"""
    global redis_client
    if redis_client:
        await redis_client.close()


# --- Session Management (Redis-based with TTL) ---
async def create_session(phone: str, tenant_id: int, vertical: str) -> bool:
    """Create user session with 24h expiry"""
    if not redis_client:
        logger.warning("Redis unavailable - session not saved")
        return False
    
    try:
        session_key = f"whatsapp_session:{phone}"
        session_data = {
            "tenant_id": str(tenant_id),
            "vertical": vertical,
            "created_at": datetime.utcnow().isoformat(),
            "phone": phone
        }
        
        # Save with TTL
        await redis_client.hset(session_key, mapping=session_data)
        await redis_client.expire(session_key, SESSION_TTL)
        
        logger.info(f"🔒 SESSION CREATED: {phone} → Tenant {tenant_id} ({vertical}) [TTL: 24h]")
        return True
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return False


async def get_session(phone: str) -> Optional[Dict[str, str]]:
    """Get active session for user"""
    if not redis_client:
        return None
    
    try:
        session_key = f"whatsapp_session:{phone}"
        session_data = await redis_client.hgetall(session_key)
        
        if session_data:
            logger.info(f"📂 ACTIVE SESSION: {phone} → Tenant {session_data.get('tenant_id')} ({session_data.get('vertical')})")
            return session_data
        return None
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return None


async def delete_session(phone: str) -> bool:
    """Delete user session (unlock)"""
    if not redis_client:
        return False
    
    try:
        session_key = f"whatsapp_session:{phone}"
        deleted = await redis_client.delete(session_key)
        
        if deleted:
            logger.info(f"🔓 SESSION DELETED: {phone}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return False


# --- Deep Link Parser ---
def parse_deep_link(message: str) -> Optional[Dict[str, str]]:
    """
    Parse deep link from message
    
    Patterns:
    - start_realty_123
    - start_expo_456
    - start_support_789
    
    Returns: {"vertical": "realty", "tenant_id": "123"} or None
    """
    # Multi-vertical pattern
    pattern = r"start[_\s-]?(realty|expo|support)[_\s-]?(\d+)"
    match = re.search(pattern, message, re.IGNORECASE)
    
    if match:
        vertical = match.group(1).lower()
        tenant_id = match.group(2)
        return {
            "vertical": vertical,
            "tenant_id": tenant_id
        }
    return None


# --- WAHA Message Sender ---
async def send_waha_message(phone: str, message: str):
    """Send WhatsApp message via WAHA API"""
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
            logger.info(f"📤 Message sent to {phone}")
            return True
    except Exception as e:
        logger.error(f"Error sending WAHA message: {e}")
        return False


# --- Backend Forwarder ---
async def forward_to_backend(data: dict, tenant_id: int, vertical: str):
    """Forward message to backend with tenant/vertical headers"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-ID": str(tenant_id),
                "X-Vertical-Mode": vertical,
                "X-Router-Source": "whatsapp-gateway-v3"
            }
            
            response = await client.post(
                BACKEND_API_URL,
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Forwarded to Tenant {tenant_id} ({vertical})")
                return True
            else:
                logger.error(f"Backend error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to forward to backend: {e}")
            return False


# --- Main Webhook ---
@app.post("/webhook/waha")
async def waha_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    WAHA webhook endpoint with personal message filtering
    
    LOGIC:
    1. Parse incoming message
    2. Check for deep link (start_{vertical}_{tenant})
    3. If deep link → create session → route to backend
    4. If no deep link → check existing session
    5. If session exists → route to backend
    6. If no session AND no deep link → IGNORE (personal message)
    """
    try:
        data = await request.json()
        payload = data.get("payload", {})
        event = data.get("event", "")
        
        # Only process message events
        if event != "message":
            return {"status": "ignored", "reason": "not_message_event"}
        
        # Extract sender info
        from_number = payload.get("from", "")
        if not from_number or "@c.us" not in from_number:
            return {"status": "ignored", "reason": "no_sender"}
        
        phone = from_number.split("@")[0]
        body = payload.get("body", "").strip()
        profile_name = payload.get("_data", {}).get("notifyName", "")
        
        logger.info(f"📨 Message from {phone} ({profile_name}): {body[:50]}...")
        
        # 🔍 STEP 1: Check for deep link
        deep_link = parse_deep_link(body)
        
        if deep_link:
            # NEW deep link detected!
            vertical = deep_link["vertical"]
            tenant_id = int(deep_link["tenant_id"])
            
            # Create session
            await create_session(phone, tenant_id, vertical)
            
            # Route to backend
            background_tasks.add_task(forward_to_backend, data, tenant_id, vertical)
            
            return {
                "status": "routed_new_session",
                "tenant_id": tenant_id,
                "vertical": vertical,
                "user": phone,
                "action": "deep_link_detected"
            }
        
        # 🔍 STEP 2: Check existing session
        session = await get_session(phone)
        
        if session:
            # User has active session → route to their tenant
            tenant_id = int(session["tenant_id"])
            vertical = session["vertical"]
            
            background_tasks.add_task(forward_to_backend, data, tenant_id, vertical)
            
            return {
                "status": "routed_existing_session",
                "tenant_id": tenant_id,
                "vertical": vertical,
                "user": phone,
                "action": "session_found"
            }
        
        # 🚫 STEP 3: No deep link AND no session → PERSONAL MESSAGE
        logger.info(f"👤 PERSONAL MESSAGE (ignored): {phone} - \"{body[:30]}...\"")
        
        # Optional: Send help message ONCE (store in Redis with 7-day TTL)
        help_sent_key = f"help_sent:{phone}"
        if redis_client:
            help_sent = await redis_client.get(help_sent_key)
            if not help_sent:
                # Send help message
                help_msg = (
                    "👋 مرحبا! لطفاً از لینک ارسالی توسط مشاور املاک خود استفاده کنید.\n\n"
                    "Hello! Please use the link provided by your real estate agent.\n\n"
                    "مرحبًا! يرجى استخدام الرابط الذي قدمه وكيل العقارات."
                )
                background_tasks.add_task(send_waha_message, from_number, help_msg)
                
                # Mark as sent (7-day TTL)
                await redis_client.set(help_sent_key, "1", ex=604800)
                
                return {
                    "status": "personal_message_ignored",
                    "user": phone,
                    "action": "help_message_sent_once"
                }
        
        return {
            "status": "personal_message_ignored",
            "user": phone,
            "action": "no_action"
        }

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return {"status": "error", "detail": str(e)}


# --- Health & Stats Endpoints ---
@app.get("/health")
async def health_check():
    """Health check with session stats"""
    redis_status = "connected" if redis_client else "disconnected"
    
    stats = {
        "status": "healthy",
        "service": "whatsapp-gateway-router-v3",
        "redis": redis_status,
        "session_ttl": f"{SESSION_TTL}s ({SESSION_TTL // 3600}h)"
    }
    
    # Get active sessions count
    if redis_client:
        try:
            session_keys = await redis_client.keys("whatsapp_session:*")
            stats["active_sessions"] = len(session_keys)
        except:
            stats["active_sessions"] = "error"
    
    return stats


@app.get("/router/stats")
async def get_router_stats():
    """Detailed routing statistics"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    try:
        # Get all active sessions
        session_keys = await redis_client.keys("whatsapp_session:*")
        
        sessions = []
        tenant_counts = {}
        vertical_counts = {}
        
        for key in session_keys:
            session_data = await redis_client.hgetall(key)
            if session_data:
                sessions.append(session_data)
                
                tenant_id = session_data.get("tenant_id")
                vertical = session_data.get("vertical", "unknown")
                
                tenant_counts[tenant_id] = tenant_counts.get(tenant_id, 0) + 1
                vertical_counts[vertical] = vertical_counts.get(vertical, 0) + 1
        
        return {
            "total_active_sessions": len(sessions),
            "unique_tenants": len(tenant_counts),
            "sessions_by_tenant": tenant_counts,
            "sessions_by_vertical": vertical_counts,
            "session_ttl": SESSION_TTL,
            "recent_sessions": sessions[:10]  # Last 10 sessions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/router/user/{phone}")
async def get_user_session(phone: str):
    """Check user's active session"""
    clean_phone = phone.replace('+', '').replace('@c.us', '')
    session = await get_session(clean_phone)
    
    if session:
        return {
            "phone": clean_phone,
            "has_session": True,
            "tenant_id": session.get("tenant_id"),
            "vertical": session.get("vertical"),
            "created_at": session.get("created_at"),
            "status": "active"
        }
    else:
        return {
            "phone": clean_phone,
            "has_session": False,
            "status": "no_session"
        }


@app.delete("/router/user/{phone}")
async def unlock_user(phone: str):
    """Unlock user (delete session)"""
    clean_phone = phone.replace('+', '').replace('@c.us', '')
    success = await delete_session(clean_phone)
    
    if success:
        return {
            "status": "unlocked",
            "phone": clean_phone,
            "message": "Session deleted successfully"
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.post("/router/generate-link")
async def generate_deep_link(request: Request):
    """
    Generate WhatsApp deep link with QR code
    
    Body:
    {
        "tenant_id": 123,
        "vertical": "realty",  # realty | expo | support
        "gateway_number": "971557357753",
        "custom_message": "سلام" (optional)
    }
    """
    try:
        data = await request.json()
        tenant_id = data.get("tenant_id")
        vertical = data.get("vertical", "realty")
        gateway_number = data.get("gateway_number", "971557357753").replace("+", "")
        custom_message = data.get("custom_message", "")
        
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id is required")
        
        if vertical not in ["realty", "expo", "support"]:
            raise HTTPException(status_code=400, detail="vertical must be: realty, expo, or support")
        
        # Build start command
        start_command = f"start_{vertical}_{tenant_id}"
        
        if custom_message:
            message_text = f"{start_command}\n{custom_message}"
        else:
            message_text = start_command
        
        # URL encode
        import urllib.parse
        encoded_message = urllib.parse.quote(message_text)
        
        deep_link = f"https://wa.me/{gateway_number}?text={encoded_message}"
        
        # QR Code URL
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(deep_link)}"
        
        logger.info(f"📲 GENERATED LINK: Tenant {tenant_id} ({vertical})")
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "vertical": vertical,
            "gateway_number": gateway_number,
            "deep_link": deep_link,
            "qr_code_url": qr_code_url,
            "preview_text": message_text,
            "usage": f"Share this link with customers. When they click and send the message, they'll be connected to your {vertical} bot."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating link: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
