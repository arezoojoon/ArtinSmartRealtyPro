"""
ArtinSmartRealty V2 - WhatsApp Bot Interface
Handles WhatsApp Business API calls and passes everything to brain.py
Supports both Meta WhatsApp Cloud API and Twilio WhatsApp API
"""

import os
import logging
import httpx
from typing import Optional, Dict, List, Any
from datetime import datetime

from database import (
    Tenant, Lead, get_tenant_by_whatsapp_phone_id, get_or_create_lead,
    update_lead, ConversationState, book_slot, create_appointment,
    AppointmentType, async_session
)
from brain import Brain, BrainResponse
from whatsapp_providers import get_whatsapp_provider, WhatsAppProvider

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class WhatsAppBotHandler:
    """
    WhatsApp Bot Handler - Strict Interface to Brain
    Auto-detects and uses either Meta WhatsApp Cloud API or Twilio WhatsApp API.
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.brain = Brain(tenant)
        self.provider = get_whatsapp_provider(tenant)
        
        if not self.provider:
            logger.warning(f"No WhatsApp provider configured for tenant {tenant.id}")
    
    async def send_message(
        self,
        to_phone: str,
        message: str,
        buttons: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """Send a message via WhatsApp (auto-routes to configured provider)."""
        if not self.provider:
            logger.error(f"WhatsApp not configured for tenant {self.tenant.id}")
            return False
        
        return await self.provider.send_message(to_phone, message, buttons)
    
    async def _get_or_create_lead(self, from_phone: str, profile_name: Optional[str] = None) -> Lead:
        """Get or create lead from WhatsApp phone number."""
        lead = await get_or_create_lead(
            tenant_id=self.tenant.id,
            whatsapp_phone=from_phone,
            source="whatsapp"
        )
        
        # Update name if available and not set
        if profile_name and not lead.name:
            await update_lead(lead.id, name=profile_name)
            lead.name = profile_name
        
        # Set phone if not set
        if not lead.phone:
            await update_lead(lead.id, phone=from_phone)
            lead.phone = from_phone
        
        return lead
    
    async def _send_response(self, to_phone: str, response: BrainResponse, lead: Lead):
        """Send Brain response to user via WhatsApp."""
        await self.send_message(to_phone, response.message, response.buttons)
        
        # Update lead state if needed
        updates = response.lead_updates or {}
        if response.next_state:
            updates["conversation_state"] = response.next_state
        
        if updates:
            await update_lead(lead.id, **updates)
        
        # Handle ROI generation if requested
        if response.should_generate_roi:
            try:
                from roi_engine import generate_roi_pdf
                
                # Generate PDF
                pdf_bytes = await generate_roi_pdf(
                    tenant=self.tenant,
                    lead=lead,
                    property_value=lead.budget_max or lead.budget_min
                )
                
                # Upload PDF to WhatsApp and send
                # Note: WhatsApp requires media to be uploaded first, then sent by media_id
                # This is a simplified version - in production, upload PDF to a server first
                logger.info(f"ROI PDF generated ({len(pdf_bytes)} bytes) for lead {lead.id}")
                # TODO: Implement WhatsApp document sending via Media Upload API
                
            except Exception as e:
                logger.error(f"Failed to generate ROI PDF: {e}")
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Handle incoming WhatsApp webhook (supports both Meta and Twilio).
        Returns True if handled successfully.
        """
        if not self.provider:
            logger.error("No WhatsApp provider configured")
            return False
        
        try:
            # Parse webhook using provider
            parsed = self.provider.parse_webhook(payload)
            if not parsed:
                return False
            
            from_phone = parsed.get("from_phone")
            profile_name = parsed.get("profile_name")
            message_type = parsed.get("message_type")
            text = parsed.get("text")
            
            # Get or create lead
            lead = await self._get_or_create_lead(from_phone, profile_name)
            
            # Process text message
            if text:
                response = await self.brain.process_message(lead, text, "")
                await self._send_response(from_phone, response, lead)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle webhook: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
            elif message_type == "image":
                # Handle image - find similar properties
                image_info = message.get("image", {})
                image_id = image_info.get("id")
                
                if image_id:
                    try:
                        # Send processing message
                        from brain import Language
                        lang = lead.language or Language.EN
                        processing_msg = self.brain.get_text("image_processing", lang)
                        await self.send_message(from_phone, processing_msg)
                        
                        # Download and process image
                        image_url = await self._get_media_url(image_id)
                        if not image_url:
                            error_msg = self.brain.get_text("image_error", lang)
                            await self.send_message(from_phone, error_msg)
                            return True
                        
                        # Download image data
                        import httpx
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            headers = {"Authorization": f"Bearer {self.tenant.whatsapp_access_token}"}
                            img_response = await client.get(image_url, headers=headers)
                            
                            if img_response.status_code == 200:
                                image_data = img_response.content
                                
                                # Validate size (max 20MB)
                                if len(image_data) > 20 * 1024 * 1024:
                                    await self.send_message(from_phone, "Image too large (max 20MB)")
                                    return True
                                
                                # Process through brain
                                from brain import process_image_message
                                description, response = await process_image_message(
                                    tenant=self.tenant,
                                    lead=lead,
                                    image_data=image_data,
                                    file_extension="jpg"
                                )
                                await self._send_response(from_phone, response, lead)
                            else:
                                logger.error(f"Failed to download image: {img_response.status_code}")
                                error_msg = self.brain.get_text("image_error", lang)
                                await self.send_message(from_phone, error_msg)
                    except Exception as e:
                        logger.error(f"Error processing WhatsApp image: {e}")
                        error_msg = self.brain.get_text("image_error", lang)
                        await self.send_message(from_phone, error_msg)
            
            elif message_type == "audio":
                # Handle voice message
                audio_info = message.get("audio", {})
                audio_id = audio_info.get("id")
                
                if audio_id:
                    try:
                        # Download and process voice
                        audio_url = await self._get_media_url(audio_id)
                        if not audio_url:
                            from brain import Language
                            lang = lead.language or Language.EN
                            error_msg = self.brain.get_text("voice_error", lang)
                            await self.send_message(from_phone, error_msg)
                            return True
                        
                        # Download audio data
                        import httpx
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            headers = {"Authorization": f"Bearer {self.tenant.whatsapp_access_token}"}
                            audio_response = await client.get(audio_url, headers=headers)
                            
                            if audio_response.status_code == 200:
                                audio_data = audio_response.content
                                
                                # Validate size (max 16MB for Gemini)
                                if len(audio_data) > 16 * 1024 * 1024:
                                    await self.send_message(from_phone, "Voice message too large (max 16MB)")
                                    return True
                                
                                # Process through brain
                                from brain import process_voice_message
                                transcript, response = await process_voice_message(
                                    tenant=self.tenant,
                                    lead=lead,
                                    audio_data=audio_data,
                                    file_extension="ogg"
                                )
                                await self._send_response(from_phone, response, lead)
                            else:
                                logger.error(f"Failed to download audio: {audio_response.status_code}")
                                from brain import Language
                                lang = lead.language or Language.EN
                                error_msg = self.brain.get_text("voice_error", lang)
                                await self.send_message(from_phone, error_msg)
                    except Exception as e:
                        logger.error(f"Error processing WhatsApp voice: {e}")
                        from brain import Language
                        lang = lead.language or Language.EN
                        error_msg = self.brain.get_text("voice_error", lang)
                        await self.send_message(from_phone, error_msg)
            
            elif message_type == "location":
                # Handle location sharing
                location = message.get("location", {})
                lat = location.get("latitude")
                lon = location.get("longitude")
                
                if lat and lon:
                    location_text = f"📍 Location: {lat}, {lon}"
                    response = await self.brain.process_message(lead, location_text)
                    await self._send_response(from_phone, response, lead)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling WhatsApp webhook: {e}")
            return False
    
    async def _get_media_url(self, media_id: str) -> Optional[str]:
        """Get download URL for a media file."""
        if not self.tenant.whatsapp_access_token:
            return None
        
        url = f"{self.api_base}/{media_id}"
        headers = {
            "Authorization": f"Bearer {self.tenant.whatsapp_access_token}"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("url")
        except httpx.HTTPError as e:
            logger.error(f"Failed to get media URL: {e}")
            return None
    
    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[List[Dict]] = None
    ) -> bool:
        """Send a WhatsApp template message (for initiating conversations)."""
        if not self.tenant.whatsapp_phone_number_id or not self.tenant.whatsapp_access_token:
            logger.error(f"WhatsApp not configured for tenant {self.tenant.id}")
            return False
        
        url = f"{self.api_base}/{self.tenant.whatsapp_phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.tenant.whatsapp_access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"Template message sent to {to_phone}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send template message: {e}")
            return False


# ==================== WEBHOOK VERIFICATION ====================

def verify_webhook(mode: str, token: str, challenge: str, verify_token: str) -> Optional[str]:
    """
    Verify WhatsApp webhook subscription.
    Called when Meta sends a GET request to verify the webhook.
    """
    if mode == "subscribe" and token == verify_token:
        logger.info("WhatsApp webhook verified")
        return challenge
    else:
        logger.warning(f"WhatsApp webhook verification failed: mode={mode}")
        return None


# ==================== MULTI-TENANT BOT MANAGER ====================

class WhatsAppBotManager:
    """
    Manages WhatsApp bots for multiple tenants.
    Unlike Telegram, WhatsApp uses webhooks so we don't need to maintain connections.
    """
    
    def __init__(self):
        self.handlers: Dict[str, WhatsAppBotHandler] = {}  # phone_number_id -> handler
    
    async def get_handler(self, phone_number_id: str) -> Optional[WhatsAppBotHandler]:
        """Get or create handler for a tenant by phone number ID."""
        if phone_number_id in self.handlers:
            return self.handlers[phone_number_id]
        
        # Load tenant from database
        tenant = await get_tenant_by_whatsapp_phone_id(phone_number_id)
        if not tenant:
            logger.warning(f"No tenant found for WhatsApp phone ID: {phone_number_id}")
            return None
        
        handler = WhatsAppBotHandler(tenant)
        self.handlers[phone_number_id] = handler
        return handler
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> bool:
        """Route webhook to appropriate handler."""
        try:
            entry = payload.get("entry", [])
            if not entry:
                return False
            
            changes = entry[0].get("changes", [])
            if not changes:
                return False
            
            value = changes[0].get("value", {})
            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            
            if not phone_number_id:
                logger.warning("No phone_number_id in webhook payload")
                return False
            
            handler = await self.get_handler(phone_number_id)
            if not handler:
                return False
            
            return await handler.handle_webhook(payload)
            
        except Exception as e:
            logger.error(f"Error routing WhatsApp webhook: {e}")
            return False


# Global bot manager instance
whatsapp_bot_manager = WhatsAppBotManager()
