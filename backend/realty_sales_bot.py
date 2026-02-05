"""
WhatsApp AI Sales Bot - Realty Sales Bot Handler
=================================================

Production-ready WhatsApp bot for Dubai real estate market.
Uses WAHA (WhatsApp HTTP API) for message handling.

Entry: Only via deep link (START_REAL_ESTATE)
Languages: EN, AR, FA, RU
Flows: Rent, Investment, Residency
"""

import os
import re
import logging
import random
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
import redis.asyncio as aioredis

from realty_flows import (
    RealtyFlow, RealtyState, PropertyCategory, VisaType,
    RealtySession, FlowController,
    RENT_BUDGET_RANGES, INVEST_BUDGET_RANGES, RESIDENCY_MINIMUMS,
    build_rent_query_filters, build_investment_query_filters,
    build_residency_query_filters, is_valid_realty_deep_link
)
from translations_realty import (
    RealtyLanguage, LANGUAGE_BUTTONS, REALTY_TRANSLATIONS,
    get_translation, get_button_text
)
from database import (
    TenantProperty, async_session, Tenant, Lead,
    PropertyType as DBPropertyType, TransactionType
)
from sqlalchemy import select, and_, or_


logger = logging.getLogger(__name__)

# Configuration
WAHA_API_URL = os.getenv("WAHA_API_URL", "http://waha:3000/api")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "waha_artinsmartrealty_secure_key_2024")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/1")
SESSION_TTL = int(os.getenv("SESSION_TTL", "86400"))  # 24 hours
DEFAULT_TENANT_ID = int(os.getenv("REALTY_BOT_TENANT_ID", "1"))


class RealtySalesBot:
    """
    Production-ready WhatsApp AI Sales Bot for Dubai Real Estate.
    
    Key Features:
    - Deep link entry validation (START_REAL_ESTATE)
    - 4-language support (EN, AR, FA, RU)
    - Three main flows: Rent, Investment, Residency
    - Global "Back to Main Menu" navigation
    - Sales psychology messaging
    - Multimodal support (voice, images)
    """
    
    def __init__(self, tenant_id: int = DEFAULT_TENANT_ID):
        self.tenant_id = tenant_id
        self.redis_client: Optional[aioredis.Redis] = None
        self.tenant: Optional[Tenant] = None
        logger.info(f"🏠 RealtySalesBot initialized for tenant {tenant_id}")
    
    async def init_redis(self):
        """Initialize Redis connection"""
        if self.redis_client is None:
            try:
                self.redis_client = await aioredis.from_url(
                    REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("✅ Redis connected for RealtySalesBot")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
    
    async def load_tenant(self):
        """Load tenant from database"""
        if self.tenant is None:
            try:
                async with async_session() as session:
                    result = await session.execute(
                        select(Tenant).where(Tenant.id == self.tenant_id)
                    )
                    self.tenant = result.scalar_one_or_none()
                    if self.tenant:
                        logger.info(f"✅ Loaded tenant: {self.tenant.name}")
            except Exception as e:
                logger.error(f"❌ Failed to load tenant: {e}")
    
    # ==================== SESSION MANAGEMENT ====================
    
    def _session_key(self, phone: str) -> str:
        """Generate Redis key for session"""
        return f"realty_session:{phone}"
    
    async def get_session(self, phone: str) -> Optional[RealtySession]:
        """Get existing session from Redis"""
        await self.init_redis()
        if not self.redis_client:
            return None
        
        try:
            key = self._session_key(phone)
            data = await self.redis_client.hgetall(key)
            if data:
                return RealtySession.from_dict(data)
            return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    async def save_session(self, session: RealtySession):
        """Save session to Redis"""
        await self.init_redis()
        if not self.redis_client:
            return
        
        try:
            session.last_activity = datetime.utcnow().isoformat()
            key = self._session_key(session.phone)
            await self.redis_client.hset(key, mapping=session.to_dict())
            await self.redis_client.expire(key, SESSION_TTL)
            logger.debug(f"Session saved for {session.phone}")
        except Exception as e:
            logger.error(f"Error saving session: {e}")
    
    async def create_session(self, phone: str, profile_name: str) -> RealtySession:
        """Create new session for deep link entry"""
        session = RealtySession(
            phone=phone,
            profile_name=profile_name,
            entry_source="deeplink",
            current_state=RealtyState.LANGUAGE_SELECT,
            created_at=datetime.utcnow().isoformat(),
        )
        await self.save_session(session)
        logger.info(f"🔒 Created session for {phone} ({profile_name})")
        return session
    
    # ==================== MESSAGE SENDING ====================
    
    async def send_message(
        self, 
        to_phone: str, 
        message: str, 
        buttons: Optional[List[Dict[str, str]]] = None
    ):
        """Send WhatsApp message via WAHA API"""
        try:
            chat_id = to_phone if "@c.us" in to_phone else f"{to_phone}@c.us"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                if buttons and len(buttons) <= 3:
                    # Use buttons API
                    response = await client.post(
                        f"{WAHA_API_URL}/sendButtons",
                        headers={
                            "X-Api-Key": WAHA_API_KEY,
                            "Content-Type": "application/json"
                        },
                        json={
                            "session": "default",
                            "chatId": chat_id,
                            "text": message,
                            "buttons": [
                                {"id": btn.get("callback_data", btn["text"]), "text": btn["text"]}
                                for btn in buttons
                            ]
                        }
                    )
                else:
                    # Plain text message
                    response = await client.post(
                        f"{WAHA_API_URL}/sendText",
                        headers={
                            "X-Api-Key": WAHA_API_KEY,
                            "Content-Type": "application/json"
                        },
                        json={
                            "session": "default",
                            "chatId": chat_id,
                            "text": message
                        }
                    )
                
                response.raise_for_status()
                logger.info(f"📤 Message sent to {to_phone}")
                return True
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def send_interactive_list(
        self, 
        to_phone: str, 
        body: str,
        button_text: str,
        sections: List[Dict[str, Any]]
    ):
        """Send WhatsApp interactive list message"""
        try:
            chat_id = to_phone if "@c.us" in to_phone else f"{to_phone}@c.us"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{WAHA_API_URL}/sendList",
                    headers={
                        "X-Api-Key": WAHA_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "session": "default",
                        "chatId": chat_id,
                        "body": body,
                        "buttonText": button_text,
                        "sections": sections
                    }
                )
                response.raise_for_status()
                logger.info(f"📋 List sent to {to_phone}")
                return True
                
        except Exception as e:
            logger.error(f"Error sending list: {e}")
            # Fallback to text message
            await self.send_message(to_phone, body)
            return False
    
    # ==================== MAIN MESSAGE HANDLER ====================
    
    async def handle_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for message handling.
        
        Returns dict with status and action taken.
        """
        await self.init_redis()
        await self.load_tenant()
        
        # Extract message info
        from_number = payload.get("from", "")
        if "@c.us" in from_number:
            phone = from_number.split("@")[0]
        else:
            phone = from_number
        
        body = payload.get("body", "").strip()
        profile_name = payload.get("_data", {}).get("notifyName", "")
        has_media = payload.get("hasMedia", False)
        media_type = payload.get("type", "chat")
        
        logger.info(f"📨 Message from {phone} ({profile_name}): {body[:50]}...")
        
        # Get existing session
        session = await self.get_session(phone)
        
        # ===== ENTRY CONTROL =====
        if session is None:
            # No session - check for deep link
            if is_valid_realty_deep_link(body):
                # Valid deep link - create session
                session = await self.create_session(phone, profile_name)
                await self.send_language_selection(phone, profile_name)
                return {
                    "status": "new_session",
                    "action": "language_selection_sent",
                    "phone": phone
                }
            else:
                # Direct message without deep link - ignore or send neutral response
                logger.info(f"👤 DIRECT MESSAGE (no deep link): {phone}")
                # Optionally send static response (uncomment if needed)
                # await self.send_message(
                #     phone, 
                #     get_translation("direct_message_response", "EN")
                # )
                return {
                    "status": "ignored",
                    "reason": "no_deep_link",
                    "phone": phone
                }
        
        # ===== EXISTING SESSION - PROCESS MESSAGE =====
        session.messages_count += 1
        
        # Check for "Back to Main Menu"
        if FlowController.is_back_to_menu(body):
            session.reset_flow_data()
            session.current_state = RealtyState.INTENT_SELECT
            await self.save_session(session)
            await self.send_intent_selection(session)
            return {
                "status": "back_to_menu",
                "phone": phone
            }
        
        # Handle based on current state
        result = await self._handle_state(session, body, has_media, media_type, payload)
        await self.save_session(session)
        
        return result
    
    async def _handle_state(
        self, 
        session: RealtySession, 
        message: str,
        has_media: bool,
        media_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle message based on current conversation state"""
        state = RealtyState(session.current_state)
        
        # Handle media messages for active sessions
        if has_media:
            if media_type == "ptt" or media_type == "audio":
                return await self.handle_voice_message(session, payload)
            elif media_type == "image":
                return await self.handle_image_message(session, payload)
        
        # State handlers
        handlers = {
            RealtyState.LANGUAGE_SELECT: self._handle_language_selection,
            RealtyState.INTENT_SELECT: self._handle_intent_selection,
            
            # Rent Flow
            RealtyState.RENT_PROPERTY_TYPE: self._handle_rent_property_type,
            RealtyState.RENT_BUDGET: self._handle_rent_budget,
            RealtyState.RENT_AREA: self._handle_rent_area,
            RealtyState.RENT_RESULTS: self._handle_rent_results,
            
            # Investment Flow
            RealtyState.INVEST_TYPE: self._handle_invest_type,
            RealtyState.INVEST_BUDGET: self._handle_invest_budget,
            RealtyState.INVEST_RESULTS: self._handle_invest_results,
            
            # Residency Flow
            RealtyState.RESID_VISA_TYPE: self._handle_resid_visa_type,
            RealtyState.RESID_PROPERTY_TYPE: self._handle_resid_property_type,
            RealtyState.RESID_RESULTS: self._handle_resid_results,
            
            # Terminal
            RealtyState.CONSULTATION: self._handle_consultation,
            RealtyState.COMPLETED: self._handle_completed,
        }
        
        handler = handlers.get(state)
        if handler:
            return await handler(session, message)
        else:
            # Unknown state - reset to intent selection
            session.current_state = RealtyState.INTENT_SELECT
            await self.send_intent_selection(session)
            return {"status": "state_reset", "phone": session.phone}
    
    # ==================== LANGUAGE SELECTION ====================
    
    async def send_language_selection(self, phone: str, profile_name: str):
        """Send language selection options"""
        # Use greeting with profile name
        greeting = f"👋 {profile_name}!\n\n" if profile_name else "👋 "
        
        message = greeting + "Welcome to Dubai Real Estate!\n\nI'm your AI sales consultant. Please select your preferred language:\n\n"
        message += "مرحباً! اختر لغتك المفضلة:\n"
        message += "خوش آمدید! زبان خود را انتخاب کنید:\n"
        message += "Добро пожаловать! Выберите язык:"
        
        buttons = [
            {"text": "🇬🇧 English", "callback_data": "lang_en"},
            {"text": "🇦🇪 العربية", "callback_data": "lang_ar"},
            {"text": "🇮🇷 فارسی", "callback_data": "lang_fa"},
        ]
        
        await self.send_message(phone, message, buttons)
        
        # Send Russian as second message (WhatsApp limit: 3 buttons)
        await self.send_message(phone, "🇷🇺 Для русского языка напишите: RU")
    
    async def _handle_language_selection(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle language selection response"""
        message_lower = message.lower().strip()
        
        # Detect language
        lang = None
        if "en" in message_lower or "english" in message_lower:
            lang = "EN"
        elif "ar" in message_lower or "عربي" in message_lower or "arabic" in message_lower:
            lang = "AR"
        elif "fa" in message_lower or "فارسی" in message_lower or "persian" in message_lower or "farsi" in message_lower:
            lang = "FA"
        elif "ru" in message_lower or "русский" in message_lower or "russian" in message_lower:
            lang = "RU"
        
        if lang:
            session.language = lang
            session.current_state = RealtyState.INTENT_SELECT
            
            # Send confirmation and intent menu
            confirm = get_translation("language_confirmed", lang)
            await self.send_message(session.phone, confirm)
            await self.send_intent_selection(session)
            
            return {"status": "language_selected", "language": lang, "phone": session.phone}
        else:
            # Invalid selection - resend options
            await self.send_language_selection(session.phone, session.profile_name)
            return {"status": "language_retry", "phone": session.phone}
    
    # ==================== INTENT SELECTION ====================
    
    async def send_intent_selection(self, session: RealtySession):
        """Send main intent selection menu"""
        lang = session.language
        
        message = get_translation("intent_select", lang)
        
        buttons = [
            {"text": get_button_text("btn_rent", lang), "callback_data": "intent_rent"},
            {"text": get_button_text("btn_investment", lang), "callback_data": "intent_invest"},
            {"text": get_button_text("btn_residency", lang), "callback_data": "intent_resid"},
        ]
        
        await self.send_message(session.phone, message, buttons)
    
    async def _handle_intent_selection(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle intent selection response"""
        flow = FlowController.get_flow_from_intent(message)
        
        if flow == RealtyFlow.RENT:
            session.current_flow = RealtyFlow.RENT
            session.current_state = RealtyState.RENT_PROPERTY_TYPE
            await self._send_rent_property_type(session)
            return {"status": "flow_started", "flow": "rent", "phone": session.phone}
            
        elif flow == RealtyFlow.INVESTMENT:
            session.current_flow = RealtyFlow.INVESTMENT
            session.current_state = RealtyState.INVEST_TYPE
            await self._send_invest_type(session)
            return {"status": "flow_started", "flow": "investment", "phone": session.phone}
            
        elif flow == RealtyFlow.RESIDENCY:
            session.current_flow = RealtyFlow.RESIDENCY
            session.current_state = RealtyState.RESID_VISA_TYPE
            await self._send_resid_visa_type(session)
            return {"status": "flow_started", "flow": "residency", "phone": session.phone}
        
        else:
            # Invalid selection
            error_msg = get_translation("error_invalid_selection", session.language)
            await self.send_message(session.phone, error_msg)
            await self.send_intent_selection(session)
            return {"status": "intent_retry", "phone": session.phone}
    
    # ==================== RENT FLOW ====================
    
    async def _send_rent_property_type(self, session: RealtySession):
        """Send rent property type question"""
        lang = session.language
        message = get_translation("rent_property_type", lang)
        
        buttons = [
            {"text": get_button_text("btn_residential", lang), "callback_data": "rent_residential"},
            {"text": get_button_text("btn_commercial", lang), "callback_data": "rent_commercial"},
            {"text": get_button_text("btn_back_to_menu", lang), "callback_data": "MAIN_MENU"},
        ]
        
        await self.send_message(session.phone, message, buttons)
    
    async def _handle_rent_property_type(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle rent property type response"""
        message_lower = message.lower()
        
        if any(x in message_lower for x in ["residential", "مسکونی", "سكني", "жилая", "res"]):
            session.property_type = PropertyCategory.RESIDENTIAL
        elif any(x in message_lower for x in ["commercial", "تجاری", "تجاري", "коммерческ", "com"]):
            session.property_type = PropertyCategory.COMMERCIAL
        else:
            error_msg = get_translation("error_invalid_selection", session.language)
            await self.send_message(session.phone, error_msg)
            await self._send_rent_property_type(session)
            return {"status": "rent_type_retry", "phone": session.phone}
        
        session.current_state = RealtyState.RENT_BUDGET
        await self._send_rent_budget(session)
        return {"status": "rent_type_selected", "type": session.property_type, "phone": session.phone}
    
    async def _send_rent_budget(self, session: RealtySession):
        """Send rent budget question"""
        lang = session.language
        message = get_translation("rent_budget", lang)
        
        budget_options = get_translation("rent_budget_options", lang)
        
        # Create list sections
        sections = [{
            "title": "Monthly Budget",
            "rows": [
                {"id": f"rent_budget_{i}", "title": opt}
                for i, opt in enumerate(budget_options)
            ]
        }]
        
        await self.send_interactive_list(
            session.phone,
            message,
            "Select Budget",
            sections
        )
    
    async def _handle_rent_budget(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle rent budget response"""
        lang = session.language
        budget_options = get_translation("rent_budget_options", lang)
        
        # Try to match budget option
        budget_index = None
        for i, opt in enumerate(budget_options):
            if opt in message or f"rent_budget_{i}" in message:
                budget_index = i
                break
        
        # Try to parse numeric value
        if budget_index is None:
            numbers = re.findall(r'[\d,]+', message.replace(',', ''))
            if numbers:
                amount = int(numbers[0])
                for i, (min_val, max_val, _) in RENT_BUDGET_RANGES.items():
                    if max_val is None:
                        if amount >= min_val:
                            budget_index = i
                            break
                    elif min_val <= amount < max_val:
                        budget_index = i
                        break
        
        if budget_index is not None:
            min_val, max_val, _ = RENT_BUDGET_RANGES.get(budget_index, (0, None, ""))
            session.budget_min = min_val
            session.budget_max = max_val
            session.budget_index = budget_index
            session.current_state = RealtyState.RENT_AREA
            await self._send_rent_area(session)
            return {"status": "rent_budget_selected", "budget_index": budget_index, "phone": session.phone}
        else:
            error_msg = get_translation("error_invalid_selection", session.language)
            await self.send_message(session.phone, error_msg)
            await self._send_rent_budget(session)
            return {"status": "rent_budget_retry", "phone": session.phone}
    
    async def _send_rent_area(self, session: RealtySession):
        """Send rent area question"""
        lang = session.language
        message = get_translation("rent_area", lang)
        
        buttons = [
            {"text": get_button_text("btn_back_to_menu", lang), "callback_data": "MAIN_MENU"},
        ]
        
        await self.send_message(session.phone, message, buttons)
    
    async def _handle_rent_area(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle rent area response"""
        # Accept any text as area preference
        session.location_preference = message.strip()
        session.current_state = RealtyState.RENT_RESULTS
        
        # Search and show results
        await self._show_rent_results(session)
        return {"status": "rent_area_selected", "area": session.location_preference, "phone": session.phone}
    
    async def _show_rent_results(self, session: RealtySession):
        """Query database and show rent results"""
        lang = session.language
        
        # Show searching message
        searching_msg = get_translation("rent_searching", lang,
            property_type=session.property_type or "All",
            budget=f"{session.budget_min:,} - {session.budget_max:,} AED" if session.budget_max else f"{session.budget_min:,}+ AED",
            area=session.location_preference or "Any"
        )
        await self.send_message(session.phone, searching_msg)
        
        # Query properties
        properties = await self._query_rent_properties(session)
        
        if properties:
            for prop in properties[:3]:  # Show max 3 properties
                await self._send_property_card(session, prop, show_roi=False)
        else:
            no_results = get_translation("no_results", lang)
            await self.send_message(session.phone, no_results)
        
        # Offer next steps
        buttons = [
            {"text": get_button_text("btn_schedule_viewing", lang), "callback_data": "schedule"},
            {"text": get_button_text("btn_more_properties", lang), "callback_data": "more"},
            {"text": get_button_text("btn_back_to_menu", lang), "callback_data": "MAIN_MENU"},
        ]
        
        next_steps = "What would you like to do next?" if lang == "EN" else get_translation("btn_need_help", lang)
        await self.send_message(session.phone, next_steps, buttons)
    
    async def _handle_rent_results(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle response after showing rent results"""
        message_lower = message.lower()
        
        if any(x in message_lower for x in ["schedule", "viewing", "رزرو", "حجز", "просмотр"]):
            session.current_state = RealtyState.CONSULTATION
            await self._send_consultation_options(session)
            return {"status": "rent_to_consultation", "phone": session.phone}
        elif any(x in message_lower for x in ["more", "بیشتر", "المزيد", "ещё"]):
            await self._show_rent_results(session)
            return {"status": "rent_more_results", "phone": session.phone}
        else:
            # Show results again
            await self._show_rent_results(session)
            return {"status": "rent_results_retry", "phone": session.phone}
    
    # ==================== INVESTMENT FLOW ====================
    
    async def _send_invest_type(self, session: RealtySession):
        """Send investment type question"""
        lang = session.language
        message = get_translation("invest_type", lang)
        
        buttons = [
            {"text": get_button_text("btn_residential", lang), "callback_data": "invest_residential"},
            {"text": get_button_text("btn_commercial", lang), "callback_data": "invest_commercial"},
            {"text": get_button_text("btn_land", lang), "callback_data": "invest_land"},
        ]
        
        await self.send_message(session.phone, message, buttons)
    
    async def _handle_invest_type(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle investment type response"""
        message_lower = message.lower()
        
        if any(x in message_lower for x in ["residential", "مسکونی", "سكني", "жилая"]):
            session.investment_type = PropertyCategory.RESIDENTIAL
        elif any(x in message_lower for x in ["commercial", "تجاری", "تجاري", "коммерч"]):
            session.investment_type = PropertyCategory.COMMERCIAL
        elif any(x in message_lower for x in ["land", "زمین", "أرض", "земля"]):
            session.investment_type = PropertyCategory.LAND
        else:
            error_msg = get_translation("error_invalid_selection", session.language)
            await self.send_message(session.phone, error_msg)
            await self._send_invest_type(session)
            return {"status": "invest_type_retry", "phone": session.phone}
        
        session.current_state = RealtyState.INVEST_BUDGET
        await self._send_invest_budget(session)
        return {"status": "invest_type_selected", "type": session.investment_type, "phone": session.phone}
    
    async def _send_invest_budget(self, session: RealtySession):
        """Send investment budget question"""
        lang = session.language
        message = get_translation("invest_budget", lang)
        
        budget_options = get_translation("invest_budget_options", lang)
        
        sections = [{
            "title": "Investment Budget",
            "rows": [
                {"id": f"invest_budget_{i}", "title": opt}
                for i, opt in enumerate(budget_options)
            ]
        }]
        
        await self.send_interactive_list(
            session.phone,
            message,
            "Select Budget",
            sections
        )
    
    async def _handle_invest_budget(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle investment budget response"""
        lang = session.language
        budget_options = get_translation("invest_budget_options", lang)
        
        budget_index = None
        for i, opt in enumerate(budget_options):
            if opt in message or f"invest_budget_{i}" in message:
                budget_index = i
                break
        
        if budget_index is None:
            # Try numeric parsing
            numbers = re.findall(r'[\d,\.]+', message.replace(',', '').replace('M', '000000').replace('K', '000'))
            if numbers:
                amount = int(float(numbers[0]))
                for i, (min_val, max_val, _) in INVEST_BUDGET_RANGES.items():
                    if max_val is None:
                        if amount >= min_val:
                            budget_index = i
                            break
                    elif min_val <= amount < max_val:
                        budget_index = i
                        break
        
        if budget_index is not None:
            min_val, max_val, _ = INVEST_BUDGET_RANGES.get(budget_index, (0, None, ""))
            session.budget_min = min_val
            session.budget_max = max_val
            session.budget_index = budget_index
            session.current_state = RealtyState.INVEST_RESULTS
            await self._show_invest_results(session)
            return {"status": "invest_budget_selected", "budget_index": budget_index, "phone": session.phone}
        else:
            error_msg = get_translation("error_invalid_selection", session.language)
            await self.send_message(session.phone, error_msg)
            await self._send_invest_budget(session)
            return {"status": "invest_budget_retry", "phone": session.phone}
    
    async def _show_invest_results(self, session: RealtySession):
        """Query and show investment results with ROI"""
        lang = session.language
        
        searching_msg = get_translation("invest_searching", lang,
            property_type=session.investment_type or "All",
            budget=f"{session.budget_min:,} - {session.budget_max:,} AED" if session.budget_max else f"{session.budget_min:,}+ AED"
        )
        await self.send_message(session.phone, searching_msg)
        
        properties = await self._query_invest_properties(session)
        
        if properties:
            for prop in properties[:3]:
                await self._send_property_card(session, prop, show_roi=True)
        else:
            no_results = get_translation("no_results", lang)
            await self.send_message(session.phone, no_results)
        
        buttons = [
            {"text": get_button_text("btn_contact_agent", lang), "callback_data": "contact"},
            {"text": get_button_text("btn_more_properties", lang), "callback_data": "more"},
            {"text": get_button_text("btn_back_to_menu", lang), "callback_data": "MAIN_MENU"},
        ]
        
        await self.send_message(session.phone, "📊 Interested in any of these investments?", buttons)
    
    async def _handle_invest_results(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle response after showing investment results"""
        message_lower = message.lower()
        
        if any(x in message_lower for x in ["contact", "agent", "تماس", "وكيل", "агент"]):
            session.current_state = RealtyState.CONSULTATION
            await self._send_consultation_options(session)
            return {"status": "invest_to_consultation", "phone": session.phone}
        elif any(x in message_lower for x in ["more", "بیشتر", "المزيد", "ещё"]):
            await self._show_invest_results(session)
            return {"status": "invest_more_results", "phone": session.phone}
        else:
            await self._show_invest_results(session)
            return {"status": "invest_results_retry", "phone": session.phone}
    
    # ==================== RESIDENCY FLOW ====================
    
    async def _send_resid_visa_type(self, session: RealtySession):
        """Send residency visa type question"""
        lang = session.language
        message = get_translation("resid_visa_type", lang)
        
        buttons = [
            {"text": get_button_text("btn_2year_visa", lang), "callback_data": "visa_2year"},
            {"text": get_button_text("btn_golden_visa", lang), "callback_data": "visa_golden"},
            {"text": get_button_text("btn_back_to_menu", lang), "callback_data": "MAIN_MENU"},
        ]
        
        await self.send_message(session.phone, message, buttons)
    
    async def _handle_resid_visa_type(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle visa type response"""
        message_lower = message.lower()
        
        if any(x in message_lower for x in ["2", "two", "year", "سنتين", "دو ساله", "2 год"]):
            session.visa_type = VisaType.TWO_YEAR
        elif any(x in message_lower for x in ["golden", "10", "ten", "ذهبية", "گلدن", "золот"]):
            session.visa_type = VisaType.GOLDEN_VISA
        else:
            error_msg = get_translation("error_invalid_selection", session.language)
            await self.send_message(session.phone, error_msg)
            await self._send_resid_visa_type(session)
            return {"status": "resid_visa_retry", "phone": session.phone}
        
        session.current_state = RealtyState.RESID_PROPERTY_TYPE
        await self._send_resid_property_type(session)
        return {"status": "resid_visa_selected", "visa": session.visa_type, "phone": session.phone}
    
    async def _send_resid_property_type(self, session: RealtySession):
        """Send residency property type question"""
        lang = session.language
        message = get_translation("resid_property_type", lang)
        
        buttons = [
            {"text": get_button_text("btn_residential", lang), "callback_data": "resid_residential"},
            {"text": get_button_text("btn_commercial", lang), "callback_data": "resid_commercial"},
            {"text": get_button_text("btn_land", lang), "callback_data": "resid_land"},
        ]
        
        await self.send_message(session.phone, message, buttons)
    
    async def _handle_resid_property_type(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle residency property type response"""
        message_lower = message.lower()
        
        if any(x in message_lower for x in ["residential", "مسکونی", "سكني", "жилая"]):
            session.property_type = PropertyCategory.RESIDENTIAL
        elif any(x in message_lower for x in ["commercial", "تجاری", "تجاري", "коммерч"]):
            session.property_type = PropertyCategory.COMMERCIAL
        elif any(x in message_lower for x in ["land", "زمین", "أرض", "земля"]):
            session.property_type = PropertyCategory.LAND
        else:
            error_msg = get_translation("error_invalid_selection", session.language)
            await self.send_message(session.phone, error_msg)
            await self._send_resid_property_type(session)
            return {"status": "resid_type_retry", "phone": session.phone}
        
        session.current_state = RealtyState.RESID_RESULTS
        await self._show_resid_results(session)
        return {"status": "resid_type_selected", "type": session.property_type, "phone": session.phone}
    
    async def _show_resid_results(self, session: RealtySession):
        """Query and show residency-eligible properties"""
        lang = session.language
        
        min_price = RESIDENCY_MINIMUMS.get(VisaType(session.visa_type), 750000)
        visa_name = "2-Year Visa" if session.visa_type == VisaType.TWO_YEAR else "Golden Visa (10-Year)"
        
        searching_msg = get_translation("resid_searching", lang,
            visa_type=visa_name,
            property_type=session.property_type or "All",
            min_price=f"{min_price:,} AED"
        )
        await self.send_message(session.phone, searching_msg)
        
        properties = await self._query_resid_properties(session)
        
        if properties:
            for prop in properties[:3]:
                await self._send_property_card(session, prop, show_roi=True, show_residency_badge=True)
        else:
            no_results = get_translation("no_results", lang)
            await self.send_message(session.phone, no_results)
        
        buttons = [
            {"text": get_button_text("btn_schedule_viewing", lang), "callback_data": "schedule"},
            {"text": get_button_text("btn_more_properties", lang), "callback_data": "more"},
            {"text": get_button_text("btn_back_to_menu", lang), "callback_data": "MAIN_MENU"},
        ]
        
        await self.send_message(session.phone, "🛂 Ready to secure your UAE residency?", buttons)
    
    async def _handle_resid_results(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle response after showing residency results"""
        message_lower = message.lower()
        
        if any(x in message_lower for x in ["schedule", "viewing", "رزرو", "حجز", "просмотр"]):
            session.current_state = RealtyState.CONSULTATION
            await self._send_consultation_options(session)
            return {"status": "resid_to_consultation", "phone": session.phone}
        elif any(x in message_lower for x in ["more", "بیشتر", "المزيد", "ещё"]):
            await self._show_resid_results(session)
            return {"status": "resid_more_results", "phone": session.phone}
        else:
            await self._show_resid_results(session)
            return {"status": "resid_results_retry", "phone": session.phone}
    
    # ==================== CONSULTATION ====================
    
    async def _send_consultation_options(self, session: RealtySession):
        """Send consultation scheduling options"""
        lang = session.language
        message = get_translation("schedule_consultation", lang)
        
        # Generate available slots (simplified for demo)
        slots = [
            "Today 2:00 PM",
            "Today 5:00 PM",
            "Tomorrow 10:00 AM",
            "Tomorrow 2:00 PM",
            "Tomorrow 5:00 PM",
        ]
        
        sections = [{
            "title": "Available Slots",
            "rows": [
                {"id": f"slot_{i}", "title": slot}
                for i, slot in enumerate(slots)
            ]
        }]
        
        await self.send_interactive_list(
            session.phone,
            message,
            "Select Time",
            sections
        )
    
    async def _handle_consultation(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle consultation scheduling"""
        lang = session.language
        
        # Accept any time selection
        agent_name = self.tenant.name if self.tenant else "Our Agent"
        
        confirm = get_translation("consultation_confirmed", lang,
            date="Today",
            time=message if len(message) < 30 else "Scheduled",
            agent_name=agent_name
        )
        
        await self.send_message(session.phone, confirm)
        
        session.current_state = RealtyState.COMPLETED
        return {"status": "consultation_scheduled", "phone": session.phone}
    
    async def _handle_completed(
        self, 
        session: RealtySession, 
        message: str
    ) -> Dict[str, Any]:
        """Handle any message after completion"""
        # Allow user to start over
        session.current_state = RealtyState.INTENT_SELECT
        await self.send_intent_selection(session)
        return {"status": "restart", "phone": session.phone}
    
    # ==================== PROPERTY QUERIES ====================
    
    async def _query_rent_properties(self, session: RealtySession) -> List[Dict[str, Any]]:
        """Query database for rental properties"""
        try:
            async with async_session() as db_session:
                query = select(TenantProperty).where(
                    TenantProperty.tenant_id == self.tenant_id,
                    TenantProperty.is_active == True
                )
                
                # Add filters based on session data
                if session.property_type == PropertyCategory.RESIDENTIAL:
                    query = query.where(TenantProperty.property_type.in_([
                        DBPropertyType.APARTMENT, DBPropertyType.VILLA, 
                        DBPropertyType.STUDIO, DBPropertyType.PENTHOUSE, DBPropertyType.TOWNHOUSE
                    ]))
                elif session.property_type == PropertyCategory.COMMERCIAL:
                    query = query.where(TenantProperty.property_type == DBPropertyType.COMMERCIAL)
                
                # Filter for rental properties
                query = query.where(TenantProperty.transaction_type == TransactionType.RENT)
                
                if session.budget_max:
                    # Filter by price (annual rent value)
                    query = query.where(TenantProperty.price <= session.budget_max * 12)  # Annual
                
                if session.location_preference:
                    query = query.where(
                        TenantProperty.location.ilike(f"%{session.location_preference}%")
                    )
                
                query = query.limit(5)
                result = await db_session.execute(query)
                properties = result.scalars().all()
                
                return [self._property_to_dict(p) for p in properties]
                
        except Exception as e:
            logger.error(f"Error querying rent properties: {e}")
            return []
    
    async def _query_invest_properties(self, session: RealtySession) -> List[Dict[str, Any]]:
        """Query database for investment properties"""
        try:
            async with async_session() as db_session:
                query = select(TenantProperty).where(
                    TenantProperty.tenant_id == self.tenant_id,
                    TenantProperty.is_active == True
                )
                
                if session.investment_type == PropertyCategory.RESIDENTIAL:
                    query = query.where(TenantProperty.property_type.in_([
                        DBPropertyType.APARTMENT, DBPropertyType.VILLA, DBPropertyType.PENTHOUSE
                    ]))
                elif session.investment_type == PropertyCategory.COMMERCIAL:
                    query = query.where(TenantProperty.property_type == DBPropertyType.COMMERCIAL)
                elif session.investment_type == PropertyCategory.LAND:
                    query = query.where(TenantProperty.property_type == DBPropertyType.LAND)
                
                # Filter for purchase (investment) properties
                query = query.where(TenantProperty.transaction_type == TransactionType.BUY)
                
                if session.budget_min:
                    query = query.where(TenantProperty.price >= session.budget_min)
                if session.budget_max:
                    query = query.where(TenantProperty.price <= session.budget_max)
                
                query = query.limit(5)
                result = await db_session.execute(query)
                properties = result.scalars().all()
                
                return [self._property_to_dict(p) for p in properties]
                
        except Exception as e:
            logger.error(f"Error querying invest properties: {e}")
            return []
    
    async def _query_resid_properties(self, session: RealtySession) -> List[Dict[str, Any]]:
        """Query database for residency-eligible properties"""
        min_price = RESIDENCY_MINIMUMS.get(VisaType(session.visa_type), 750000)
        
        try:
            async with async_session() as db_session:
                query = select(TenantProperty).where(
                    TenantProperty.tenant_id == self.tenant_id,
                    TenantProperty.is_active == True,
                    TenantProperty.price >= min_price
                )
                
                if session.property_type == PropertyCategory.RESIDENTIAL:
                    query = query.where(TenantProperty.property_type.in_([
                        DBPropertyType.APARTMENT, DBPropertyType.VILLA, DBPropertyType.PENTHOUSE
                    ]))
                elif session.property_type == PropertyCategory.COMMERCIAL:
                    query = query.where(TenantProperty.property_type == DBPropertyType.COMMERCIAL)
                elif session.property_type == PropertyCategory.LAND:
                    query = query.where(TenantProperty.property_type == DBPropertyType.LAND)
                
                # Filter for Golden Visa when applicable
                if session.visa_type == VisaType.GOLDEN_VISA:
                    query = query.where(TenantProperty.golden_visa_eligible == True)
                
                query = query.limit(5)
                result = await db_session.execute(query)
                properties = result.scalars().all()
                
                return [self._property_to_dict(p) for p in properties]
                
        except Exception as e:
            logger.error(f"Error querying resid properties: {e}")
            return []
    
    def _property_to_dict(self, prop: TenantProperty) -> Dict[str, Any]:
        """Convert property model to dictionary"""
        return {
            "id": prop.id,
            "title": prop.name,  # Use 'name' field from TenantProperty
            "location": prop.location,  # Use 'location' field
            "price": prop.price,
            "size": prop.area_sqft,  # Use 'area_sqft' field
            "bedrooms": prop.bedrooms,
            "property_type": str(prop.property_type.value) if prop.property_type else "unknown",
            "is_featured": prop.is_featured or False,
            "is_urgent": prop.is_urgent or False,
            "rental_yield": prop.rental_yield or 7.5,
            "golden_visa_eligible": prop.golden_visa_eligible or False,
        }

    
    # ==================== PROPERTY PRESENTATION ====================
    
    async def _send_property_card(
        self, 
        session: RealtySession, 
        prop: Dict[str, Any],
        show_roi: bool = False,
        show_residency_badge: bool = False
    ):
        """Send formatted property card with sales psychology"""
        lang = session.language
        
        # Build urgency message
        urgency = self._build_urgency_message(prop, lang)
        
        # Build ROI section
        roi_section = ""
        if show_roi:
            roi_data = self._calculate_roi(prop)
            roi_section = get_translation("roi_section", lang,
                yield_percent=f"{roi_data['yield_percent']:.1f}",
                monthly_income=f"{roi_data['monthly_income']:,.0f}",
                payback_years=f"{roi_data['payback_years']:.1f}",
                appreciation="8"  # Fixed appreciation for demo
            )
        
        # Build residency badge
        badge = ""
        if show_residency_badge:
            badge = get_translation("resid_eligible_badge", lang) + "\n\n"
        
        # Format property card
        card = badge + get_translation("property_card", lang,
            title=prop.get("title", "Property"),
            location=prop.get("location", "Dubai"),
            price=f"{prop.get('price', 0):,}",
            size=f"{prop.get('size', 0):,}",
            bedrooms=prop.get("bedrooms", "N/A"),
            urgency_message=urgency,
            roi_section=roi_section
        )
        
        await self.send_message(session.phone, card)
    
    def _build_urgency_message(self, prop: Dict[str, Any], lang: str) -> str:
        """Build scarcity/urgency messaging"""
        parts = []
        
        # Units left
        price = prop.get("price", 0)
        if price > 5000000:
            units = random.randint(1, 2)
        elif price > 2000000:
            units = random.randint(2, 4)
        else:
            units = random.randint(3, 6)
        
        parts.append(get_translation("scarcity_units", lang, units=units))
        
        # Views today
        views = random.randint(3, 12)
        parts.append(get_translation("scarcity_views", lang, views=views))
        
        # Time pressure
        parts.append(get_translation("scarcity_time", lang))
        
        return " • ".join(parts)
    
    def _calculate_roi(self, prop: Dict[str, Any]) -> Dict[str, float]:
        """Calculate ROI metrics for property"""
        price = prop.get("price", 1000000)
        yield_percent = prop.get("rental_yield", 7.5)
        
        annual_income = price * (yield_percent / 100)
        monthly_income = annual_income / 12
        payback_years = price / annual_income if annual_income > 0 else 0
        
        return {
            "annual_income": annual_income,
            "monthly_income": monthly_income,
            "payback_years": payback_years,
            "yield_percent": yield_percent
        }
    
    # ==================== MULTIMODAL HANDLING ====================
    
    async def handle_voice_message(
        self, 
        session: RealtySession, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle voice message from user"""
        lang = session.language
        
        # Send processing message
        processing_msg = get_translation("voice_processing", lang)
        await self.send_message(session.phone, processing_msg)
        
        # TODO: Implement actual speech-to-text using Gemini
        # For now, acknowledge and ask for text input
        
        error_msg = "🎤 Voice processing is being set up. Please type your message for now."
        await self.send_message(session.phone, error_msg)
        
        return {"status": "voice_received", "phone": session.phone}
    
    async def handle_image_message(
        self, 
        session: RealtySession, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle image message from user"""
        lang = session.language
        
        # Send analyzing message
        analyzing_msg = get_translation("image_analyzing", lang)
        await self.send_message(session.phone, analyzing_msg)
        
        # TODO: Implement actual image analysis using Gemini Vision
        # For now, acknowledge and continue flow
        
        response = "📸 I see your image! Let me help you find similar properties. What's your budget range?"
        await self.send_message(session.phone, response)
        
        return {"status": "image_received", "phone": session.phone}


# ==================== SINGLETON INSTANCE ====================

_bot_instance: Optional[RealtySalesBot] = None


def get_realty_sales_bot(tenant_id: int = DEFAULT_TENANT_ID) -> RealtySalesBot:
    """Get or create RealtySalesBot instance"""
    global _bot_instance
    if _bot_instance is None or _bot_instance.tenant_id != tenant_id:
        _bot_instance = RealtySalesBot(tenant_id)
    return _bot_instance


# ==================== EXPORT ====================

__all__ = [
    "RealtySalesBot",
    "get_realty_sales_bot",
]
