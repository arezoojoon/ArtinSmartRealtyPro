"""
WhatsApp Provider Abstraction Layer
Supports both Meta WhatsApp Cloud API and Twilio WhatsApp API
"""

import os
import logging
import httpx
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod
from database import Tenant

logger = logging.getLogger(__name__)


class WhatsAppProvider(ABC):
    """Base class for WhatsApp providers."""
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
    
    @abstractmethod
    async def send_message(
        self, 
        to_phone: str, 
        message: str, 
        buttons: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """Send a message via WhatsApp."""
        pass
    
    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse incoming webhook payload.
        Returns standardized message dict or None.
        """
        pass


class MetaWhatsAppProvider(WhatsAppProvider):
    """Meta (Facebook) WhatsApp Cloud API Provider."""
    
    def __init__(self, tenant: Tenant):
        super().__init__(tenant)
        self.api_base = "https://graph.facebook.com/v18.0"
    
    async def send_message(
        self,
        to_phone: str,
        message: str,
        buttons: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """Send message via Meta WhatsApp Cloud API."""
        if not self.tenant.whatsapp_phone_number_id or not self.tenant.whatsapp_access_token:
            logger.error(f"Meta WhatsApp not configured for tenant {self.tenant.id}")
            return False
        
        url = f"{self.api_base}/{self.tenant.whatsapp_phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.tenant.whatsapp_access_token}",
            "Content-Type": "application/json"
        }
        
        # Build payload based on buttons
        if buttons and len(buttons) <= 3:
            payload = self._build_interactive_buttons(to_phone, message, buttons)
        elif buttons:
            payload = self._build_interactive_list(to_phone, message, buttons)
        else:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_phone,
                "type": "text",
                "text": {"preview_url": False, "body": message}
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"[Meta] Message sent to {to_phone}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"[Meta] Failed to send message: {e}")
            return False
    
    def _build_interactive_buttons(self, to_phone: str, body_text: str, buttons: List[Dict[str, str]]) -> Dict:
        """Build Meta interactive button payload."""
        button_rows = []
        for btn in buttons[:3]:
            button_rows.append({
                "type": "reply",
                "reply": {
                    "id": btn["callback_data"],
                    "title": btn["text"][:20]
                }
            })
        
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {"buttons": button_rows}
            }
        }
    
    def _build_interactive_list(self, to_phone: str, body_text: str, buttons: List[Dict[str, str]]) -> Dict:
        """Build Meta interactive list payload."""
        rows = []
        for btn in buttons[:10]:
            rows.append({
                "id": btn["callback_data"],
                "title": btn["text"][:24],
                "description": ""
            })
        
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": body_text},
                "action": {
                    "button": "Select Option",
                    "sections": [{"title": "Options", "rows": rows}]
                }
            }
        }
    
    def parse_webhook(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Meta WhatsApp webhook."""
        try:
            entry = payload.get("entry", [])
            if not entry:
                return None
            
            changes = entry[0].get("changes", [])
            if not changes:
                return None
            
            value = changes[0].get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                return None
            
            message = messages[0]
            from_phone = message.get("from")
            message_type = message.get("type")
            
            # Get profile name
            contacts = value.get("contacts", [])
            profile_name = None
            if contacts:
                profile = contacts[0].get("profile", {})
                profile_name = profile.get("name")
            
            # Extract message content
            text_content = None
            if message_type == "text":
                text_content = message.get("text", {}).get("body")
            elif message_type == "interactive":
                interactive = message.get("interactive", {})
                if interactive.get("type") == "button_reply":
                    text_content = interactive.get("button_reply", {}).get("id")
                elif interactive.get("type") == "list_reply":
                    text_content = interactive.get("list_reply", {}).get("id")
            
            return {
                "from_phone": from_phone,
                "profile_name": profile_name,
                "message_type": message_type,
                "text": text_content
            }
        except Exception as e:
            logger.error(f"[Meta] Failed to parse webhook: {e}")
            return None


class TwilioWhatsAppProvider(WhatsAppProvider):
    """Twilio WhatsApp API Provider."""
    
    def __init__(self, tenant: Tenant):
        super().__init__(tenant)
        # Twilio credentials stored in tenant fields:
        # - whatsapp_twilio_account_sid
        # - whatsapp_twilio_auth_token
        # - whatsapp_twilio_from_number (e.g., "whatsapp:+14155238886")
    
    async def send_message(
        self,
        to_phone: str,
        message: str,
        buttons: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """Send message via Twilio WhatsApp API."""
        # Get Twilio credentials from tenant or env
        account_sid = getattr(self.tenant, 'whatsapp_twilio_account_sid', None) or os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = getattr(self.tenant, 'whatsapp_twilio_auth_token', None) or os.getenv('TWILIO_AUTH_TOKEN')
        from_number = getattr(self.tenant, 'whatsapp_twilio_from_number', None) or os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        if not all([account_sid, auth_token, from_number]):
            logger.error(f"Twilio WhatsApp not configured for tenant {self.tenant.id}")
            return False
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        
        # Twilio doesn't support interactive buttons natively, append as text
        full_message = message
        if buttons:
            full_message += "\n\n" + "\n".join([f"{i+1}. {btn['text']}" for i, btn in enumerate(buttons[:10])])
        
        # Ensure phone has whatsapp: prefix
        to_phone_formatted = to_phone if to_phone.startswith("whatsapp:") else f"whatsapp:{to_phone}"
        
        data = {
            "From": from_number,
            "To": to_phone_formatted,
            "Body": full_message
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data=data,
                    auth=(account_sid, auth_token)
                )
                response.raise_for_status()
                logger.info(f"[Twilio] Message sent to {to_phone}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"[Twilio] Failed to send message: {e}")
            return False
    
    def parse_webhook(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Twilio WhatsApp webhook (form-encoded)."""
        try:
            # Twilio sends form data, not JSON
            # Expected fields: From, Body, ProfileName, etc.
            from_phone = payload.get("From", "").replace("whatsapp:", "")
            text_content = payload.get("Body")
            profile_name = payload.get("ProfileName")
            
            if not from_phone or not text_content:
                return None
            
            return {
                "from_phone": from_phone,
                "profile_name": profile_name,
                "message_type": "text",
                "text": text_content
            }
        except Exception as e:
            logger.error(f"[Twilio] Failed to parse webhook: {e}")
            return None


def get_whatsapp_provider(tenant: Tenant) -> Optional[WhatsAppProvider]:
    """
    Factory function to get the appropriate WhatsApp provider.
    Auto-detects based on tenant configuration.
    """
    # Check for Twilio credentials first (easier to set up for testing)
    has_twilio = (
        getattr(tenant, 'whatsapp_twilio_account_sid', None) or os.getenv('TWILIO_ACCOUNT_SID')
    )
    
    # Check for Meta credentials
    has_meta = tenant.whatsapp_phone_number_id and tenant.whatsapp_access_token
    
    if has_twilio:
        logger.info(f"Using Twilio WhatsApp provider for tenant {tenant.id}")
        return TwilioWhatsAppProvider(tenant)
    elif has_meta:
        logger.info(f"Using Meta WhatsApp provider for tenant {tenant.id}")
        return MetaWhatsAppProvider(tenant)
    else:
        logger.warning(f"No WhatsApp provider configured for tenant {tenant.id}")
        return None
