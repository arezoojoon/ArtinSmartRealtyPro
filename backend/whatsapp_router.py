"""
WhatsApp Gateway Router for Multi-Tenant SaaS Platform

Architecture:
- Single WhatsApp number (Gateway) shared by 1000+ tenants
- Deep links format: https://wa.me/971557357753?text=start_realty_{tenant_id}
- Persistent user-to-tenant mapping (locked after first contact)
- Routes messages to correct tenant's backend handler

Author: ArtinSmartRealty Platform
"""

import re
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Router instance
router = APIRouter(prefix="/api/gateway", tags=["WhatsApp Gateway"])

# Persistent mapping file
MAPPING_FILE = Path(__file__).parent / "data" / "user_tenant_mapping.json"
MAPPING_FILE.parent.mkdir(exist_ok=True)


class UserTenantMapping:
    """Manages persistent user-to-tenant mapping"""
    
    def __init__(self, file_path: Path = MAPPING_FILE):
        self.file_path = file_path
        self.mappings: Dict[str, int] = self._load_mappings()
    
    def _load_mappings(self) -> Dict[str, int]:
        """Load mappings from JSON file"""
        if not self.file_path.exists():
            logger.info(f"Creating new mapping file: {self.file_path}")
            self._save_mappings({})
            return {}
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} user-tenant mappings")
                return data
        except Exception as e:
            logger.error(f"Failed to load mappings: {e}")
            return {}
    
    def _save_mappings(self, mappings: Dict[str, int]):
        """Save mappings to JSON file"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(mappings, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(mappings)} mappings to disk")
        except Exception as e:
            logger.error(f"Failed to save mappings: {e}")
    
    def lock_user_to_tenant(self, phone_number: str, tenant_id: int) -> bool:
        """
        Lock a user to a specific tenant (first contact wins)
        
        Args:
            phone_number: User's WhatsApp phone number
            tenant_id: Tenant ID to lock to
            
        Returns:
            True if new mapping created, False if already existed
        """
        # Normalize phone number (remove +, spaces, hyphens)
        normalized_phone = re.sub(r'[^\d]', '', phone_number)
        
        if normalized_phone in self.mappings:
            existing_tenant = self.mappings[normalized_phone]
            if existing_tenant != tenant_id:
                logger.warning(
                    f"User {normalized_phone} already locked to tenant {existing_tenant}, "
                    f"ignoring lock attempt to tenant {tenant_id}"
                )
            return False
        
        # Create new mapping
        self.mappings[normalized_phone] = tenant_id
        self._save_mappings(self.mappings)
        
        logger.info(f"🔒 Locked user {normalized_phone} to tenant {tenant_id}")
        return True
    
    def get_tenant_for_user(self, phone_number: str) -> Optional[int]:
        """
        Get the locked tenant ID for a user
        
        Args:
            phone_number: User's WhatsApp phone number
            
        Returns:
            Tenant ID if found, None otherwise
        """
        normalized_phone = re.sub(r'[^\d]', '', phone_number)
        return self.mappings.get(normalized_phone)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mapping statistics"""
        tenant_counts = {}
        for tenant_id in self.mappings.values():
            tenant_counts[tenant_id] = tenant_counts.get(tenant_id, 0) + 1
        
        return {
            "total_users": len(self.mappings),
            "total_tenants": len(tenant_counts),
            "users_per_tenant": tenant_counts,
            "last_updated": datetime.now().isoformat()
        }


# Global mapping instance
user_tenant_map = UserTenantMapping()


class WahaWebhookPayload(BaseModel):
    """Waha webhook payload structure"""
    event: str
    session: str
    payload: Dict[str, Any]


def extract_tenant_from_deep_link(message_text: str) -> Optional[int]:
    """
    Extract tenant_id from deep link start command
    
    Formats supported:
    - start_realty_123
    - start_realty_2
    - START_REALTY_99 (case insensitive)
    
    Args:
        message_text: The message body text
        
    Returns:
        Tenant ID if found, None otherwise
    """
    if not message_text:
        return None
    
    # Regex pattern: start_realty_{tenant_id}
    pattern = r'^start_realty_(\d+)$'
    match = re.match(pattern, message_text.strip().lower())
    
    if match:
        tenant_id = int(match.group(1))
        logger.info(f"✅ Extracted tenant_id={tenant_id} from deep link")
        return tenant_id
    
    return None


def get_phone_number_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract phone number from Waha payload
    
    Args:
        payload: Waha webhook payload
        
    Returns:
        Phone number if found, None otherwise
    """
    # Waha structure: payload.from (sender phone)
    sender = payload.get('from', '')
    
    # Remove @c.us suffix if present
    phone = sender.replace('@c.us', '')
    
    if phone:
        logger.debug(f"Extracted phone number: {phone}")
        return phone
    
    logger.warning("Could not extract phone number from payload")
    return None


def get_message_text_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract message text from Waha payload
    
    Args:
        payload: Waha webhook payload
        
    Returns:
        Message text if found, None otherwise
    """
    # Waha structure: payload.body (message text)
    text = payload.get('body', '')
    
    return text if text else None


@router.post("/waha")
async def handle_waha_webhook(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key")
):
    """
    Main WhatsApp Gateway Router Webhook
    
    Flow:
    1. Receive message from Waha
    2. Extract phone number and message text
    3. Check if message is a deep link (start_realty_{tenant_id})
    4. If deep link: Lock user to tenant
    5. If normal message: Look up locked tenant
    6. Route to appropriate tenant's backend handler
    """
    try:
        # Parse payload
        body = await request.json()
        logger.info(f"📨 Received Waha webhook: {body.get('event', 'unknown')}")
        
        # Extract event type
        event = body.get('event', '')
        
        # Only process message events
        if not event.startswith('message'):
            logger.debug(f"Ignoring non-message event: {event}")
            return {"status": "ignored", "reason": "not a message event"}
        
        # Extract payload
        payload = body.get('payload', {})
        
        # Extract phone number
        phone_number = get_phone_number_from_payload(payload)
        if not phone_number:
            logger.error("❌ Could not extract phone number from payload")
            return {"status": "error", "reason": "missing phone number"}
        
        # Extract message text
        message_text = get_message_text_from_payload(payload)
        if not message_text:
            logger.debug("No text in message (could be image/voice/etc)")
            message_text = ""  # Handle media messages
        
        # Step A: Check for deep link (new session)
        tenant_id_from_link = extract_tenant_from_deep_link(message_text)
        
        if tenant_id_from_link:
            # New session - lock user to tenant
            is_new = user_tenant_map.lock_user_to_tenant(phone_number, tenant_id_from_link)
            
            if is_new:
                logger.info(
                    f"🎯 NEW SESSION: User {phone_number} → Tenant {tenant_id_from_link}"
                )
            else:
                logger.info(
                    f"🔄 EXISTING SESSION: User {phone_number} already locked to tenant"
                )
            
            target_tenant_id = tenant_id_from_link
        
        else:
            # Step B: Normal message - look up locked tenant
            target_tenant_id = user_tenant_map.get_tenant_for_user(phone_number)
            
            if not target_tenant_id:
                logger.warning(
                    f"⚠️ User {phone_number} not locked to any tenant - ignoring message"
                )
                
                # Optional: Send generic response
                # TODO: Implement send_message to instruct user to use agent's link
                
                return {
                    "status": "ignored",
                    "reason": "user not associated with any tenant",
                    "action": "please_use_agent_link"
                }
            
            logger.info(
                f"📍 ROUTING: User {phone_number} → Tenant {target_tenant_id}"
            )
        
        # Step C: Forward to tenant's backend handler
        # Import here to avoid circular dependency
        from whatsapp_bot import handle_whatsapp_message
        from database import async_session, Tenant
        from sqlalchemy import select
        
        # Get tenant from database
        async with async_session() as session:
            result = await session.execute(
                select(Tenant).where(Tenant.id == target_tenant_id)
            )
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                logger.error(f"❌ Tenant {target_tenant_id} not found in database")
                return {
                    "status": "error",
                    "reason": f"tenant {target_tenant_id} not found"
                }
            
            # Call the existing WhatsApp bot handler with tenant context
            logger.info(f"🚀 Forwarding to whatsapp_bot.handle_whatsapp_message")
            
            # Modify payload to include tenant_id for handler
            enriched_payload = {
                **body,
                "_gateway_tenant_id": target_tenant_id,
                "_gateway_phone": phone_number,
                "_is_deep_link_start": bool(tenant_id_from_link)
            }
            
            # Forward to handler
            response = await handle_whatsapp_message(
                tenant=tenant,
                payload=enriched_payload
            )
            
            return {
                "status": "routed",
                "tenant_id": target_tenant_id,
                "phone_number": phone_number,
                "is_new_session": bool(tenant_id_from_link),
                "handler_response": response
            }
    
    except Exception as e:
        logger.error(f"❌ Gateway router error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_gateway_stats():
    """Get gateway routing statistics"""
    stats = user_tenant_map.get_stats()
    return {
        "status": "success",
        "gateway_stats": stats
    }


@router.get("/user/{phone_number}/tenant")
async def get_user_tenant(phone_number: str):
    """Get the locked tenant for a specific user"""
    tenant_id = user_tenant_map.get_tenant_for_user(phone_number)
    
    if tenant_id:
        return {
            "status": "found",
            "phone_number": phone_number,
            "tenant_id": tenant_id
        }
    else:
        return {
            "status": "not_found",
            "phone_number": phone_number,
            "tenant_id": None
        }


@router.delete("/user/{phone_number}/mapping")
async def delete_user_mapping(phone_number: str):
    """Delete a user's tenant mapping (admin only)"""
    normalized_phone = re.sub(r'[^\d]', '', phone_number)
    
    if normalized_phone in user_tenant_map.mappings:
        tenant_id = user_tenant_map.mappings[normalized_phone]
        del user_tenant_map.mappings[normalized_phone]
        user_tenant_map._save_mappings(user_tenant_map.mappings)
        
        logger.info(f"🗑️ Deleted mapping: {normalized_phone} → Tenant {tenant_id}")
        
        return {
            "status": "deleted",
            "phone_number": phone_number,
            "previous_tenant_id": tenant_id
        }
    else:
        return {
            "status": "not_found",
            "phone_number": phone_number
        }
