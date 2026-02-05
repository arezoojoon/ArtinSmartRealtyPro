"""
Telegram AI Sales Bot - Realty Sales Bot Handler
=================================================

Mirror of WhatsApp Bot for consistency across platforms.
Adapts WhatsApp UI elements (Lists/Buttons) to Telegram Inline Keyboards.

Flows: Rent, Investment, Residency
Languages: EN, AR, FA, RU
"""

import logging
import re
import json
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    InputMediaPhoto
)
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from realty_flows import (
    RealtyFlow, RealtyState, PropertyCategory, VisaType,
    RealtySession, FlowController,
    RENT_BUDGET_RANGES, INVEST_BUDGET_RANGES, RESIDENCY_MINIMUMS
)
from translations_realty import (
    RealtyLanguage, get_translation, get_button_text
)
from database import (
    TenantProperty, async_session, Tenant, Lead,
    PropertyType as DBPropertyType, TransactionType
)
from sqlalchemy import select

logger = logging.getLogger(__name__)

class RealtyTelegramBot:
    """
    Telegram implementation of the Realty Sales Bot.
    Mirrors logic of RealtySalesBot but adapts UI for Telegram.
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.tenant_id = tenant.id
        # We use the existing redis connection from the main bot
        from redis_manager import redis_manager
        self.redis = redis_manager
    
    # ==================== HELPER METHODS ====================
    
    async def get_session(self, user_id: str, profile_name: str = "") -> RealtySession:
        """Get or create session from Redis"""
        session_key = f"realty_session_tg:{user_id}"
        
        # Try to load existing
        if self.redis.redis_client:
            data = await self.redis.redis_client.hgetall(session_key)
            if data:
                # Add profile name if missing
                if not data.get("profile_name") and profile_name:
                    data["profile_name"] = profile_name
                return RealtySession.from_dict(data)
        
        # Create new if not exists
        session = RealtySession(
            phone=user_id,  # store telegram ID as phone for compatibility
            profile_name=profile_name,
            entry_source="telegram_start",
            messages_count=0
        )
        return session

    async def save_session(self, session: RealtySession):
        """Save session to Redis"""
        if not self.redis.redis_client:
            return
            
        session_key = f"realty_session_tg:{session.phone}"
        data = session.to_dict()
        
        # Convert all to strings for Redis hash
        str_data = {k: str(v) if v is not None else "" for k, v in data.items()}
        
        await self.redis.redis_client.hset(session_key, mapping=str_data)
        await self.redis.redis_client.expire(session_key, 86400)  # 24h TTL

    async def send_message(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        text: str, 
        buttons: Optional[List[Dict[str, str]]] = None,
        image_url: Optional[str] = None
    ):
        """Send message with optional buttons/image"""
        chat_id = update.effective_chat.id
        reply_markup = None
        
        if buttons:
            keyboard = []
            row = []
            for btn in buttons:
                request_contact = btn.get("request_contact", False)
                
                # Telegram Inline Buttons don't support request_contact directly like ReplyKeyboard
                # But for consistency with WhatsApp flow which relies entirely on callbacks,
                # we will stick to InlineButtons. 
                # If we really need contact, we'd switch to ReplyKeyboardMarkup, 
                # but standardized flow mostly uses callbacks.
                
                b = InlineKeyboardButton(
                    text=btn["text"],
                    callback_data=btn["callback_data"]
                )
                row.append(b)
                
                # Grid layout: 2 buttons per row, unless long text
                if len(row) == 2 or len(btn["text"]) > 15:
                    keyboard.append(row)
                    row = []
            
            if row:
                keyboard.append(row)
            reply_markup = InlineKeyboardMarkup(keyboard)
            
        try:
            # If we have an image
            if image_url:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=image_url,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            # If we are in specific states, we might want to edit the previous message 
            # to avoid clutter, but for now safe bet is sending new message 
            # or editing if it's a callback query
            elif update.callback_query:
                # Try to edit if no image involved
                 await context.bot.send_message( # Prefer new messages for better history visibility
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Error sending TG message: {e}")

    # ==================== MAIN HANDLER ====================

    async def handle_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main entry point for updates"""
        user = update.effective_user
        profile_name = user.first_name if user else "User"
        user_id = str(user.id)
        
        # Load Session
        session = await self.get_session(user_id, profile_name)
        
        # Handle Callback Query
        if update.callback_query:
            await update.callback_query.answer()
            data = update.callback_query.data
            
            # Global Back Handler
            if data == "MAIN_MENU": 
                session.reset_flow_data()
                session.current_state = RealtyState.INTENT_SELECT
                await self.save_session(session)
                await self.send_intent_selection(update, context, session)
                return

            # Proceed based on state
            await self._handle_state(session, data, update, context)
            
        # Handle Text Message
        elif update.message and update.message.text:
            text = update.message.text
            
            # Check commands
            if text == "/start":
                await self.send_language_selection(update, context, session)
                return
            
            # Global Back (Text)
            if FlowController.is_back_to_menu(text):
                session.reset_flow_data()
                session.current_state = RealtyState.INTENT_SELECT
                await self.save_session(session)
                await self.send_intent_selection(update, context, session)
                return

            await self._handle_state(session, text, update, context)
            
        await self.save_session(session)

    async def _handle_state(
        self, 
        session: RealtySession, 
        input_data: str, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Route input to specific state handlers"""
        state = RealtyState(session.current_state)
        
        handlers = {
            RealtyState.LANGUAGE_SELECT: self._handle_language_selection,
            RealtyState.INTENT_SELECT: self._handle_intent_selection,
            
            # Rent
            RealtyState.RENT_PROPERTY_TYPE: self._handle_rent_property_type,
            RealtyState.RENT_BUDGET: self._handle_rent_budget,
            RealtyState.RENT_AREA: self._handle_rent_area,
            RealtyState.RENT_RESULTS: self._handle_rent_results,
            
            # Invest
            RealtyState.INVEST_TYPE: self._handle_invest_type,
            RealtyState.INVEST_BUDGET: self._handle_invest_budget,
            RealtyState.INVEST_RESULTS: self._handle_invest_results,
             
            # Resid
            RealtyState.RESID_VISA_TYPE: self._handle_resid_visa_type,
            RealtyState.RESID_PROPERTY_TYPE: self._handle_resid_property_type,
            RealtyState.RESID_RESULTS: self._handle_resid_results,
            
            # Terminal
            RealtyState.CONSULTATION: self._handle_consultation,
            RealtyState.COMPLETED: self._handle_completed,
        }
        
        handler = handlers.get(state)
        if handler:
            await handler(session, input_data, update, context)
        else:
            # Fallback
            await self.send_intent_selection(update, context, session)

    # ==================== LANGUAGE ====================
    
    async def send_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        session.current_state = RealtyState.LANGUAGE_SELECT
        
        msg = (
            "👋 Welcome to Dubai Real Estate!\n\n"
            "I'm your AI sales consultant. Please select your preferred language:\n\n"
            "مرحباً! اختر لغتك المفضلة:\n"
            "خوش آمدید! زبان خود را انتخاب کنید:\n"
            "Добро пожаловать! Выберите язык:"
        )
        buttons = [
            {"text": "🇬🇧 English", "callback_data": "lang_en"},
            {"text": "🇦🇪 العربية", "callback_data": "lang_ar"},
            {"text": "🇮🇷 فارسی", "callback_data": "lang_fa"},
            {"text": "🇷🇺 Русский", "callback_data": "lang_ru"}
        ]
        await self.send_message(update, context, msg, buttons)

    async def _handle_language_selection(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = None
        data_lower = data.lower()
        if "lang_en" in data_lower or "english" in data_lower: lang = "EN"
        elif "lang_ar" in data_lower or "arabic" in data_lower: lang = "AR"
        elif "lang_fa" in data_lower or "farsi" in data_lower: lang = "FA"
        elif "lang_ru" in data_lower or "russian" in data_lower: lang = "RU"
        
        if lang:
            session.language = lang
            session.current_state = RealtyState.INTENT_SELECT
            confirm = get_translation("language_confirmed", lang)
            await self.send_message(update, context, confirm)
            await self.send_intent_selection(update, context, session)
        else:
             await self.send_language_selection(update, context, session)

    # ==================== INTENT ====================

    async def send_intent_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        lang = session.language
        msg = get_translation("intent_select", lang)
        buttons = [
            {"text": get_button_text("btn_rent", lang), "callback_data": "intent_rent"},
            {"text": get_button_text("btn_investment", lang), "callback_data": "intent_invest"},
            {"text": get_button_text("btn_residency", lang), "callback_data": "intent_resid"},
        ]
        await self.send_message(update, context, msg, buttons)

    async def _handle_intent_selection(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        flow = FlowController.get_flow_from_intent(data)
        
        if flow == RealtyFlow.RENT:
            session.current_flow = RealtyFlow.RENT
            session.current_state = RealtyState.RENT_PROPERTY_TYPE
            await self._send_rent_property_type(update, context, session)
            
        elif flow == RealtyFlow.INVESTMENT:
            session.current_flow = RealtyFlow.INVESTMENT
            session.current_state = RealtyState.INVEST_TYPE
            await self._send_invest_type(update, context, session)
            
        elif flow == RealtyFlow.RESIDENCY:
            session.current_flow = RealtyFlow.RESIDENCY
            session.current_state = RealtyState.RESID_VISA_TYPE
            await self._send_resid_visa_type(update, context, session)
            
        else:
            await self.send_intent_selection(update, context, session)

    # ==================== RENT FLOW ====================

    async def _send_rent_property_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        lang = session.language
        msg = get_translation("rent_property_type", lang)
        buttons = [
            {"text": get_button_text("btn_residential", lang), "callback_data": "rent_residential"},
            {"text": get_button_text("btn_commercial", lang), "callback_data": "rent_commercial"},
            {"text": get_button_text("btn_back_to_menu", lang), "callback_data": "MAIN_MENU"},
        ]
        await self.send_message(update, context, msg, buttons)

    async def _handle_rent_property_type(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if "residential" in data: session.property_type = PropertyCategory.RESIDENTIAL
        elif "commercial" in data: session.property_type = PropertyCategory.COMMERCIAL
        else:
            await self._send_rent_property_type(update, context, session)
            return

        session.current_state = RealtyState.RENT_BUDGET
        await self._send_rent_budget(update, context, session)

    async def _send_rent_budget(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        lang = session.language
        msg = get_translation("rent_budget", lang)
        opts = get_translation("rent_budget_options", lang)
        
        buttons = []
        for i, opt in enumerate(opts):
             buttons.append({"text": opt, "callback_data": f"rent_budget_{i}"})
        
        await self.send_message(update, context, msg, buttons)

    async def _handle_rent_budget(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Match callback "rent_budget_X"
        match = re.search(r"rent_budget_(\d+)", data)
        budget_index = int(match.group(1)) if match else None
        
        # Or parse text
        if budget_index is None and update.message:
            # Simple fallback for text input (not implementing full parser here for brevity, typical usage is buttons)
             numbers = re.findall(r'[\d,]+', data.replace(',', ''))
             if numbers:
                 # Logic to map text amount to index... omitted for now, relying on buttons
                 pass

        if budget_index is not None:
             min_val, max_val, _ = RENT_BUDGET_RANGES.get(budget_index, (0, None, ""))
             session.budget_min = min_val
             session.budget_max = max_val
             session.budget_index = budget_index
             session.current_state = RealtyState.RENT_AREA
             await self._send_rent_area(update, context, session)
        else:
             await self._send_rent_budget(update, context, session)

    async def _send_rent_area(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        lang = session.language
        msg = get_translation("rent_area", lang)
        buttons = [{"text": get_button_text("btn_back_to_menu", lang), "callback_data": "MAIN_MENU"}]
        await self.send_message(update, context, msg, buttons)

    async def _handle_rent_area(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        session.location_preference = data.strip()
        session.current_state = RealtyState.RENT_RESULTS
        await self._show_rent_results(update, context, session)

    async def _show_rent_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        lang = session.language
        
        searching = get_translation("rent_searching", lang,
            property_type=session.property_type or "All",
            budget=f"{session.budget_min:,} - {session.budget_max:,}" if session.budget_max else f"{session.budget_min:,}+",
            area=session.location_preference or "Any"
        )
        await self.send_message(update, context, searching)
        
        properties = await self._query_properties(session, TransactionType.RENT)
        
        if properties:
            for prop in properties[:3]:
                 await self._send_property_card(update, context, session, prop)
        else:
            await self.send_message(update, context, get_translation("no_results", lang))
            
        buttons = [
            {"text": get_button_text("btn_schedule_viewing", lang), "callback_data": "schedule"},
            {"text": get_button_text("btn_more_properties", lang), "callback_data": "more"},
            {"text": get_button_text("btn_back_to_menu", lang), "callback_data": "MAIN_MENU"},
        ]
        await self.send_message(update, context, "👇 Next Steps:", buttons)

    async def _handle_rent_results(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if "schedule" in data:
            session.current_state = RealtyState.CONSULTATION
            await self._send_consultation_options(update, context, session)
        elif "more" in data:
            await self._show_rent_results(update, context, session)
        else:
             await self._show_rent_results(update, context, session)

    # ==================== INVEST FLOW ====================

    async def _send_invest_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        lang = session.language
        msg = get_translation("invest_type", lang)
        buttons = [
            {"text": get_button_text("btn_residential", lang), "callback_data": "invest_residential"},
            {"text": get_button_text("btn_commercial", lang), "callback_data": "invest_commercial"},
            {"text": get_button_text("btn_land", lang), "callback_data": "invest_land"},
        ]
        await self.send_message(update, context, msg, buttons)
        
    async def _handle_invest_type(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if "residential" in data: session.investment_type = PropertyCategory.RESIDENTIAL
        elif "commercial" in data: session.investment_type = PropertyCategory.COMMERCIAL
        elif "land" in data: session.investment_type = PropertyCategory.LAND
        else:
             await self._send_invest_type(update, context, session)
             return
             
        session.current_state = RealtyState.INVEST_BUDGET
        await self._send_invest_budget(update, context, session)

    async def _send_invest_budget(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        lang = session.language
        msg = get_translation("invest_budget", lang)
        opts = get_translation("invest_budget_options", lang)
        buttons = []
        for i, opt in enumerate(opts):
             buttons.append({"text": opt, "callback_data": f"invest_budget_{i}"})
        await self.send_message(update, context, msg, buttons)

    async def _handle_invest_budget(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        match = re.search(r"invest_budget_(\d+)", data)
        idx = int(match.group(1)) if match else None
        
        if idx is not None:
             min_val, max_val, _ = INVEST_BUDGET_RANGES.get(idx, (0, None, ""))
             session.budget_min = min_val
             session.budget_max = max_val
             session.current_state = RealtyState.INVEST_RESULTS
             await self._show_invest_results(update, context, session)
        else:
             await self._send_invest_budget(update, context, session)

    async def _show_invest_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        lang = session.language
        msg = get_translation("invest_searching", lang,
            property_type=session.investment_type or "All",
            budget=f"{session.budget_min:,}+"
        )
        await self.send_message(update, context, msg)
        
        properties = await self._query_properties(session, TransactionType.BUY)
        
        if properties:
            for prop in properties[:3]:
                 await self._send_property_card(update, context, session, prop, show_roi=True)
        else:
            await self.send_message(update, context, get_translation("no_results", lang))
            
        buttons = [
            {"text": get_button_text("btn_contact_agent", lang), "callback_data": "contact"},
            {"text": get_button_text("btn_more_properties", lang), "callback_data": "more"},
            {"text": get_button_text("btn_back_to_menu", lang), "callback_data": "MAIN_MENU"},
        ]
        await self.send_message(update, context, "📊 Next Steps:", buttons)
        
    async def _handle_invest_results(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
         if "contact" in data:
            session.current_state = RealtyState.CONSULTATION
            await self._send_consultation_options(update, context, session)
         elif "more" in data:
            await self._show_invest_results(update, context, session)
         else:
             await self._show_invest_results(update, context, session)

    # ==================== RESIDENCY FLOW ====================

    async def _send_resid_visa_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        lang = session.language
        msg = get_translation("resid_visa_type", lang)
        buttons = [
            {"text": get_button_text("btn_2year_visa", lang), "callback_data": "visa_2year"},
            {"text": get_button_text("btn_golden_visa", lang), "callback_data": "visa_golden"},
            {"text": get_button_text("btn_back_to_menu", lang), "callback_data": "MAIN_MENU"},
        ]
        await self.send_message(update, context, msg, buttons)

    async def _handle_resid_visa_type(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if "visa_2year" in data: session.visa_type = VisaType.TWO_YEAR
        elif "visa_golden" in data: session.visa_type = VisaType.GOLDEN_VISA
        else:
            await self._send_resid_visa_type(update, context, session)
            return
            
        session.current_state = RealtyState.RESID_PROPERTY_TYPE
        await self._send_resid_property_type(update, context, session)

    async def _send_resid_property_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        lang = session.language
        msg = get_translation("resid_property_type", lang)
        buttons = [
            {"text": get_button_text("btn_residential", lang), "callback_data": "resid_residential"},
            {"text": get_button_text("btn_commercial", lang), "callback_data": "resid_commercial"},
        ]
        await self.send_message(update, context, msg, buttons)
        
    async def _handle_resid_property_type(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if "residential" in data: session.property_type = PropertyCategory.RESIDENTIAL
        elif "commercial" in data: session.property_type = PropertyCategory.COMMERCIAL
        else:
             await self._send_resid_property_type(update, context, session)
             return
        
        session.current_state = RealtyState.RESID_RESULTS
        await self._show_resid_results(update, context, session)

    async def _show_resid_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        lang = session.language
        min_price = RESIDENCY_MINIMUMS.get(VisaType(session.visa_type), 750000)
        
        msg = get_translation("resid_searching", lang,
            visa_type="Golden Visa" if session.visa_type == VisaType.GOLDEN_VISA else "2-Year Visa",
            property_type=session.property_type,
            min_price=f"{min_price:,}"
        )
        await self.send_message(update, context, msg)
        
        # Residency Query Logic needed here
        properties = await self._query_properties(session, TransactionType.BUY, is_residency=True)
         
        if properties:
            for prop in properties[:3]:
                 await self._send_property_card(update, context, session, prop, show_roi=True, show_residency=True)
        else:
            await self.send_message(update, context, get_translation("no_results", lang))

        buttons = [
            {"text": get_button_text("btn_schedule_viewing", lang), "callback_data": "schedule"},
            {"text": get_button_text("btn_more_properties", lang), "callback_data": "more"},
            {"text": get_button_text("btn_back_to_menu", lang), "callback_data": "MAIN_MENU"},
        ]
        await self.send_message(update, context, "🛂 Next Steps:", buttons)

    async def _handle_resid_results(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
         if "schedule" in data:
            session.current_state = RealtyState.CONSULTATION
            await self._send_consultation_options(update, context, session)
         elif "more" in data:
            await self._show_resid_results(update, context, session)
         else:
             await self._show_resid_results(update, context, session)

    # ==================== CONSULTATION ====================

    async def _send_consultation_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession):
        lang = session.language
        msg = get_translation("schedule_consultation", lang)
        # Simplified slots
        buttons = [
            {"text": "Today 14:00", "callback_data": "slot_1"},
            {"text": "Tomorrow 10:00", "callback_data": "slot_2"},
            {"text": "Request Call", "callback_data": "slot_call"},
        ]
        await self.send_message(update, context, msg, buttons)

    async def _handle_consultation(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = session.language
        confirm = get_translation("consultation_confirmed", lang,
            date="Selected Time",
            time="",
            agent_name=self.tenant.name
        )
        await self.send_message(update, context, confirm)
        session.current_state = RealtyState.COMPLETED

    async def _handle_completed(self, session: RealtySession, data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.send_intent_selection(update, context, session)

    # ==================== DATABASE ====================

    async def _query_properties(self, session: RealtySession, dict_transaction_type: TransactionType, is_residency: bool = False):
        try:
            async with async_session() as db_session:
                query = select(TenantProperty).where(
                    TenantProperty.tenant_id == self.tenant_id,
                    TenantProperty.is_active == True
                )
                
                # Filters
                if session.property_type:
                    # Map to DB Enums
                    pt_map = {
                        PropertyCategory.RESIDENTIAL: [DBPropertyType.APARTMENT, DBPropertyType.VILLA, DBPropertyType.PENTHOUSE],
                        PropertyCategory.COMMERCIAL: [DBPropertyType.COMMERCIAL],
                        PropertyCategory.LAND: [DBPropertyType.LAND]
                    }
                    if session.property_type in pt_map:
                         query = query.where(TenantProperty.property_type.in_(pt_map[session.property_type]))

                if dict_transaction_type == TransactionType.RENT:
                     query = query.where(TenantProperty.transaction_type == TransactionType.RENT)
                     if session.budget_max:
                         query = query.where(TenantProperty.price <= session.budget_max * 12)
                
                elif dict_transaction_type == TransactionType.BUY:
                     query = query.where(TenantProperty.transaction_type == TransactionType.BUY)
                     if session.budget_min: query = query.where(TenantProperty.price >= session.budget_min)
                     if session.budget_max: query = query.where(TenantProperty.price <= session.budget_max)

                # Residency specific
                if is_residency:
                     min_price = RESIDENCY_MINIMUMS.get(VisaType(session.visa_type), 750000)
                     query = query.where(TenantProperty.price >= min_price)
                     if session.visa_type == VisaType.GOLDEN_VISA:
                         query = query.where(TenantProperty.golden_visa_eligible == True)

                query = query.limit(5)
                result = await db_session.execute(query)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"DB Query Error: {e}")
            return []

    async def _send_property_card(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: RealtySession, prop: TenantProperty, show_roi=False, show_residency=False):
        lang = session.language
        
        # Build Caption
        caption = f"🏠 *{prop.name}*\n"
        caption += f"📍 {prop.location}\n"
        caption += f"💰 {prop.price:,.0f} AED\n"
        if prop.area_sqft: caption += f"📏 {prop.area_sqft:,.0f} sqft\n"
        if prop.bedrooms: caption += f"🛏 {prop.bedrooms} Bedrooms\n"
        
        if show_roi and prop.expected_roi:
             caption += f"\n📈 *ROI Analysis:*\n"
             caption += f"• Yield: {prop.rental_yield or 7.5}%\n"
             caption += f"• Est. ROI: {prop.expected_roi}%\n"
             
        if show_residency and prop.golden_visa_eligible:
             caption += "\n🌟 *Golden Visa Eligible* (10-Year)\n"

        # Image
        image_url = prop.primary_image
        if prop.image_urls and isinstance(prop.image_urls, list) and len(prop.image_urls) > 0:
             image_url = prop.image_urls[0]

        await self.send_message(update, context, caption, image_url=image_url)

