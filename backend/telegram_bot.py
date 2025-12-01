"""
ArtinSmartRealty V2 - Telegram Bot Interface
Handles Telegram API calls and passes everything to brain.py
"""

import os
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from sqlalchemy.future import select

from database import (
    Tenant, Lead, AgentAvailability, get_tenant_by_bot_token, get_or_create_lead,
    update_lead, ConversationState, book_slot, create_appointment,
    AppointmentType, async_session, Language
)
from brain import Brain, BrainResponse, process_telegram_message, process_voice_message
from redis_manager import redis_manager, init_redis, close_redis
from context_recovery import save_context_to_redis, handle_user_message_with_recovery
from inline_keyboards import edit_message_with_checkmark

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Enable DEBUG logging for telegram library to see all updates
logging.getLogger('telegram').setLevel(logging.DEBUG)
logging.getLogger('telegram.ext').setLevel(logging.DEBUG)


class TelegramBotHandler:
    """
    Telegram Bot Handler - Strict Interface to Brain
    This class ONLY handles Telegram API calls and delegates ALL logic to Brain.
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.brain = Brain(tenant)
        self.application: Optional[Application] = None
    
    async def start_bot(self):
        """Initialize and start the Telegram bot."""
        if not self.tenant.telegram_bot_token:
            logger.error(f"No Telegram token for tenant {self.tenant.id}")
            return
        
        # Initialize Redis for session management
        await init_redis()
        logger.info(f"✅ Redis initialized for tenant {self.tenant.id}")
        
        self.application = Application.builder().token(self.tenant.telegram_bot_token).build()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.CONTACT, self.handle_contact))
        
        # Start polling
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        
        logger.info(f"Bot started for tenant: {self.tenant.name}")
    
    async def stop_bot(self):
        """Stop the Telegram bot."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info(f"Bot stopped for tenant: {self.tenant.name}")
        
        # Close Redis connection
        await close_redis()
        logger.info("✅ Redis connection closed")
    
    def _build_inline_keyboard(self, buttons: List[Dict[str, str]]) -> InlineKeyboardMarkup:
        """Build Telegram inline keyboard from button list."""
        keyboard = []
        row = []
        
        for i, btn in enumerate(buttons):
            row.append(InlineKeyboardButton(
                text=btn["text"],
                callback_data=btn["callback_data"]
            ))
            
            # 2 buttons per row, except for budget which gets 1 per row
            if len(row) == 2 or "budget" in btn["callback_data"]:
                keyboard.append(row)
                row = []
        
        if row:  # Add remaining buttons
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _get_or_create_lead(self, update: Update) -> Lead:
        """Get or create lead from Telegram update."""
        user = update.effective_user
        chat_id = str(update.effective_chat.id)
        username = user.username if user else None
        
        lead = await get_or_create_lead(
            tenant_id=self.tenant.id,
            telegram_chat_id=chat_id,
            telegram_username=username
        )
        
        # Update name if available and not set
        if user and not lead.name:
            name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            if name:
                await update_lead(lead.id, name=name)
                lead.name = name
        
        return lead
    
    async def _send_response(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        response: BrainResponse,
        lead: Lead
    ):
        """Send Brain response to user via Telegram."""
        from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
        
        chat_id = update.effective_chat.id
        
        # DEBUG: Log response details
        logger.info(f"🔍 _send_response - Lead {lead.id}: buttons={len(response.buttons) if response.buttons else 0}, request_contact={response.request_contact}, message_len={len(response.message)}")
        
        # Prepare keyboard
        reply_markup = None
        
        # Priority 1: Contact request button (ReplyKeyboard)
        if response.request_contact:
            button_text = {
                Language.EN: "📱 Share Phone Number",
                Language.FA: "📱 اشتراک‌گذاری شماره تلفن",
                Language.AR: "📱 شارك رقم الهاتف",
                Language.RU: "📱 Поделиться номером"
            }.get(lead.language, "📱 Share Phone Number")
            
            contact_button = KeyboardButton(button_text, request_contact=True)
            reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
            logger.info(f"📱 Showing contact request button for lead {lead.id}")
        
        # Priority 2: Inline buttons
        elif response.buttons:
            logger.info(f"🔘 Building keyboard with {len(response.buttons)} buttons: {[b['text'] for b in response.buttons]}")
            reply_markup = self._build_inline_keyboard(response.buttons)
        
        # Send message
        if update.callback_query:
            # Edit existing message for callback queries
            try:
                await update.callback_query.edit_message_text(
                    text=response.message,
                    reply_markup=reply_markup if not response.request_contact else None,  # Can't use ReplyKeyboard with edit
                    parse_mode='HTML'
                )
                # Send contact request as new message if needed
                if response.request_contact:
                    button_text = {
                        Language.EN: "📱 Share Phone Number",
                        Language.FA: "📱 اشتراک‌گذاری شماره تلفن",
                        Language.AR: "📱 شارك رقم الهاتف",
                        Language.RU: "📱 Поделиться номером"
                    }.get(lead.language, "📱 Share Phone Number")
                    contact_button = KeyboardButton(button_text, request_contact=True)
                    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="👇",
                        reply_markup=reply_markup
                    )
            except Exception:
                # If edit fails, send new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=response.message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=response.message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        # Update lead state if needed
        updates = response.lead_updates or {}
        if response.next_state:
            updates["conversation_state"] = response.next_state
        
        logger.info(f"💾 Saving updates for Lead {lead.id}: {updates}")
        
        if updates:
            await update_lead(lead.id, **updates)
            logger.info(f"✅ Lead {lead.id} updated successfully")
        
        # Handle PDF delivery if metadata flag is set
        send_pdf = False
        if response.metadata and response.metadata.get("send_pdf"):
            send_pdf = True
        elif response.should_generate_roi:
            send_pdf = True
        
        if send_pdf:
            try:
                from roi_engine import generate_roi_pdf
                from io import BytesIO
                
                lang = lead.language or Language.EN
                
                # Send "Preparing..." message first
                preparing_msgs = {
                    Language.EN: "📊 Preparing your personalized ROI report... This will take just a moment!",
                    Language.FA: "📊 در حال آماده‌سازی گزارش ROI شخصی‌سازی شده... چند لحظه صبر کنید!",
                    Language.AR: "📊 جاري تحضير تقرير العائد على الاستثمار الشخصي... سيستغرق لحظات فقط!",
                    Language.RU: "📊 Готовлю персональный отчёт ROI... Это займёт всего мгновение!"
                }
                
                # Determine chat context
                if update.message:
                    chat_id = update.message.chat_id
                elif update.callback_query:
                    chat_id = update.callback_query.message.chat_id
                else:
                    logger.error("No valid chat context for ROI PDF")
                    return
                
                # Send preparing message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=preparing_msgs.get(lang, preparing_msgs[Language.EN])
                )
                
                # Generate PDF
                pdf_bytes = await generate_roi_pdf(
                    tenant=self.tenant,
                    lead=lead,
                    property_value=lead.budget_max or lead.budget_min
                )
                
                # Send PDF as document
                pdf_file = BytesIO(pdf_bytes)
                pdf_file.name = f"roi_analysis_{lead.id}.pdf"
                
                caption_map = {
                    Language.EN: "📊 Here's your personalized ROI Analysis Report!",
                    Language.FA: "📊 این هم گزارش تحلیل سود سرمایه‌گذاری شما!",
                    Language.AR: "📊 إليك تقرير تحليل العائد على الاستثمار الشخصي!",
                    Language.RU: "📊 Вот ваш персональный отчёт ROI!"
                }
                
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=pdf_file,
                    filename=f"ROI_Analysis_{self.tenant.name}.pdf",
                    caption=caption_map.get(lang, caption_map[Language.EN])
                )
                
            except Exception as e:
                logger.error(f"Failed to generate ROI PDF: {e}")
                import traceback
                traceback.print_exc()
                # Don't fail the whole message if PDF generation fails
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        lead = await self._get_or_create_lead(update)
        
        logger.info(f"🔄 /start command - Lead {lead.id}: Before reset - state={lead.conversation_state}, lang={lead.language}")
        
        # Reset conversation state for new start
        await update_lead(lead.id, conversation_state=ConversationState.START)
        # CRITICAL: Update lead object in memory too!
        lead.conversation_state = ConversationState.START
        lead.language = None  # Reset language to show language selection
        
        logger.info(f"🔄 /start command - Lead {lead.id}: After reset - state={lead.conversation_state}, lang={lead.language}")
        
        # Process through Brain
        response = await self.brain.process_message(lead, "/start")
        await self._send_response(update, context, response, lead)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks with race condition protection."""
        query = update.callback_query
        
        # Ignore disabled buttons (anti-loop protection)
        if query.data in ["selected", "disabled"]:
            await query.answer("Already selected ✅")
            return
        
        await query.answer()  # Acknowledge the callback
        
        lead = await self._get_or_create_lead(update)
        telegram_id = str(update.effective_chat.id)
        callback_data = query.data
        
        # CRITICAL FIX #7: Refresh lead to ensure latest state from database
        async with async_session() as session:
            result = await session.execute(select(Lead).where(Lead.id == lead.id))
            fresh_lead = result.scalars().first()
            if fresh_lead:
                lead = fresh_lead
                logger.info(f"🔄 Refreshed lead {lead.id}, state={lead.conversation_state}")
        
        # FIX #6: Ghost Protocol - Update last interaction timestamp
        if redis_manager.redis_client:
            await redis_manager.redis_client.set(f"user:{lead.id}:last_interaction", datetime.now().isoformat())
            logger.info(f"⏰ Updated last_interaction for user {lead.id} (callback)")
        
        # CRITICAL: Acquire lock to prevent race conditions
        if telegram_id not in user_locks:
            user_locks[telegram_id] = Lock()
        
        async with user_locks[telegram_id]:
            logger.info(f"🔒 Lock acquired for callback user {telegram_id}")
        
        # Add checkmark to selected button (anti-loop)
        selected_button_text = None
        if query.message and query.message.reply_markup:
            for row in query.message.reply_markup.inline_keyboard:
                for button in row:
                    if button.callback_data == callback_data:
                        selected_button_text = button.text
                        break
        
        # Handle slot booking
        if callback_data.startswith("slot_"):
            slot_id = int(callback_data.split("_")[1])
            success = await book_slot(slot_id, lead.id)
            
            if success:
                # Get slot details to calculate actual appointment time
                async with async_session() as session:
                    result = await session.execute(
                        select(AgentAvailability).where(AgentAvailability.id == slot_id)
                    )
                    slot = result.scalar_one_or_none()
                    
                    if slot:
                        # Calculate next occurrence of this day
                        now = datetime.utcnow()
                        today = now.date()
                        days_ahead = {
                            'monday': 0, 'tuesday': 1, 'wednesday': 2,
                            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
                        }
                        target_day = days_ahead.get(slot.day_of_week.value, 0)
                        current_day = today.weekday()
                        days_until = (target_day - current_day + 7) % 7
                        
                        # If same day, check if time has passed
                        if days_until == 0:
                            if now.time() >= slot.start_time:
                                days_until = 7  # Schedule for next week
                        
                        appointment_date = datetime.combine(
                            today + timedelta(days=days_until),
                            slot.start_time
                        )
                        
                        # Create appointment with calculated date
                        await create_appointment(
                            lead_id=lead.id,
                            appointment_type=AppointmentType.OFFICE,
                            scheduled_date=appointment_date
                        )
        
        # Process through Brain
        response = await self.brain.process_message(lead, "", callback_data)
        
        # Add checkmark to selected button after Brain processing
        if selected_button_text:
            await edit_message_with_checkmark(update, context, selected_button_text)
            logger.info(f"✅ Checkmark added to button: {selected_button_text}")
        
            # Save context to Redis
            await save_context_to_redis(lead)
            logger.info(f"💾 Saved callback context to Redis for lead {lead.id}")
            
            await self._send_response(update, context, response, lead)
            logger.info(f"🔓 Lock released for callback user {telegram_id}")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages with race condition protection."""
        lead = await self._get_or_create_lead(update)
        message_text = update.message.text
        telegram_id = str(update.effective_chat.id)
        
        # CRITICAL FIX #7: Refresh lead to ensure latest state from database
        # (prevents stale state from previous message's update)
        async with async_session() as session:
            result = await session.execute(select(Lead).where(Lead.id == lead.id))
            fresh_lead = result.scalars().first()
            if fresh_lead:
                lead = fresh_lead
                logger.info(f"🔄 Refreshed lead {lead.id}, state={lead.conversation_state}")
        
        # CRITICAL: Ghost Protocol - Update last interaction timestamp on EVERY message
        if redis_manager.redis_client:
            timestamp = datetime.now().isoformat()
            await redis_manager.redis_client.set(f"user:{lead.id}:last_interaction", timestamp)
            logger.info(f"⏰ Updated last_interaction for user {lead.id} at {timestamp}")
        else:
            logger.warning(f"⚠️ Redis not available - cannot update last_interaction for user {lead.id}")
        
        # CRITICAL: Acquire lock to prevent race conditions (2 messages in 1 second)
        if telegram_id not in user_locks:
            user_locks[telegram_id] = Lock()
        
        async with user_locks[telegram_id]:
            logger.info(f"🔒 Lock acquired for user {telegram_id}")
            
            # Load context from Redis (with recovery if timeout occurred)
            redis_context = await redis_manager.get_context(telegram_id, self.tenant.id)
            if redis_context:
                logger.info(f"📦 Loaded Redis context for lead {lead.id}: state={redis_context.get('state')}")
            
            # Process through Brain
            response = await self.brain.process_message(lead, message_text)
            
            # Save context to Redis after processing
            await save_context_to_redis(lead)
            logger.info(f"💾 Saved context to Redis for lead {lead.id}")
            
            await self._send_response(update, context, response, lead)
            logger.info(f"🔓 Lock released for user {telegram_id}")
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages with slot filling protection."""
        lead = await self._get_or_create_lead(update)
        
        # CRITICAL FIX #7: Refresh lead to ensure latest state from database
        async with async_session() as session:
            result = await session.execute(select(Lead).where(Lead.id == lead.id))
            fresh_lead = result.scalars().first()
            if fresh_lead:
                lead = fresh_lead
                logger.info(f"🔄 Refreshed lead {lead.id}, state={lead.conversation_state}")
        
        # ZOMBIE STATE PROTECTION: If in SLOT_FILLING with pending button selection, guide them
        if lead.conversation_state == ConversationState.SLOT_FILLING and lead.pending_slot:
            lang = lead.language or Language.EN
            voice_redirect = {
                Language.EN: "I'll process your voice in a moment! First, please select an option from the buttons above to continue.",
                Language.FA: "یه لحظه بعد صداتو پردازش میکنم! اول لطفاً یکی از دکمه‌های بالا رو انتخاب کن.",
                Language.AR: "سأعالج رسالتك الصوتية بعد قليل! أولاً، اختر خياراً من الأزرار أعلاه.",
                Language.RU: "Обработаю голосовое чуть позже! Сначала выберите вариант из кнопок выше."
            }
            await update.message.reply_text(voice_redirect.get(lang, voice_redirect[Language.EN]))
            return
        
        # Check if voice exists
        if not update.message.voice:
            await update.message.reply_text("No voice message received. Please try again.")
            return
        
        # Download voice file
        voice = update.message.voice
        
        # Check voice duration (max 5 minutes)
        if voice.duration > 300:
            await update.message.reply_text("Voice message too long (max 5 minutes). Please send a shorter message.")
            return
        
        file = await context.bot.get_file(voice.file_id)
        
        # Download to bytes
        audio_bytes = await file.download_as_bytearray()
        
        # Process through Brain
        transcript, response = await process_voice_message(
            tenant=self.tenant,
            lead=lead,
            audio_data=bytes(audio_bytes),
            file_extension="ogg"
        )
        
        # Update lead with transcript if available
        if transcript:
            await update_lead(lead.id, voice_transcript=transcript)
        
        # Save context to Redis after voice processing
        await save_context_to_redis(lead)
        logger.info(f"💾 Saved voice context to Redis for lead {lead.id}")
        
        # DEBUG: Log response before sending
        logger.info(f"🎤 Voice response ready - message_len={len(response.message)}, has_buttons={bool(response.buttons)}")
        
        await self._send_response(update, context, response, lead)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages - find similar properties OR handle unexpected photo during slot filling."""
        lead = await self._get_or_create_lead(update)
        
        # ZOMBIE STATE PROTECTION: If in SLOT_FILLING, guide back to slots
        if lead.conversation_state == ConversationState.SLOT_FILLING:
            lang = lead.language or Language.EN
            fallback_msgs = {
                Language.EN: "I see you sent a photo! I'll analyze it in a moment, but first let's finish your property preferences. Please select your budget:",
                Language.FA: "عکس فرستادید! یه لحظه بعد بررسی میکنم، اما اول بیا ترجیحاتت رو کامل کنیم. لطفاً بودجه انتخاب کن:",
                Language.AR: "أرى أنك أرسلت صورة! سأحللها بعد قليل، لكن دعنا ننهي تفضيلاتك. اختر ميزانيتك:",
                Language.RU: "Вижу, вы отправили фото! Проанализирую чуть позже, но сначала завершим предпочтения. Выберите бюджет:"
            }
            
            from brain import BUDGET_RANGES
            budget_buttons = []
            for idx, (min_val, max_val) in BUDGET_RANGES.items():
                label = f"{min_val:,} - {max_val:,} AED" if max_val else f"{min_val:,}+ AED"
                budget_buttons.append({"text": label, "callback_data": f"budget_{idx}"})
            
            response = BrainResponse(
                message=fallback_msgs.get(lang, fallback_msgs[Language.EN]),
                next_state=ConversationState.SLOT_FILLING,
                buttons=budget_buttons
            )
            await self._send_response(update, context, response, lead)
            return
        
        # Check if photo exists
        if not update.message.photo:
            await update.message.reply_text("No photo received. Please try again.")
            return
        
        # Get the largest photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Download to bytes
        image_bytes = await file.download_as_bytearray()
        
        # Validate image size (max 20MB for Gemini)
        if len(image_bytes) > 20 * 1024 * 1024:
            await update.message.reply_text("Image too large (max 20MB). Please send a smaller image.")
            return
        
        # Send processing message
        lang = lead.language or Language.EN
        from brain import Brain
        brain = Brain(self.tenant)
        processing_msg = brain.get_text("image_processing", lang)
        await update.message.reply_text(processing_msg)
        
        # Process through Brain
        from brain import process_image_message
        description, response = await process_image_message(
            tenant=self.tenant,
            lead=lead,
            image_data=bytes(image_bytes),
            file_extension="jpg"
        )
        
        await self._send_response(update, context, response, lead)
    
    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle shared contact (phone number)."""
        lead = await self._get_or_create_lead(update)
        
        # CRITICAL FIX #7: Refresh lead to ensure latest state from database
        async with async_session() as session:
            result = await session.execute(select(Lead).where(Lead.id == lead.id))
            fresh_lead = result.scalars().first()
            if fresh_lead:
                lead = fresh_lead
                logger.info(f"🔄 Refreshed lead {lead.id}, state={lead.conversation_state}")
        
        contact = update.message.contact
        
        # Update lead with phone number
        if contact.phone_number:
            await update_lead(lead.id, phone=contact.phone_number)
        
        # Process as if they entered the phone number
        response = await self.brain.process_message(lead, contact.phone_number)
        await self._send_response(update, context, response, lead)
    
    async def send_ghost_reminder(self, lead: Lead):
        """Send ghost protocol reminder to a lead."""
        if not self.application or not lead.telegram_chat_id:
            return
        
        response = self.brain.get_ghost_reminder(lead)
        reply_markup = self._build_inline_keyboard(response.buttons) if response.buttons else None
        
        try:
            await self.application.bot.send_message(
                chat_id=int(lead.telegram_chat_id),
                text=response.message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            # Mark reminder as sent
            await update_lead(lead.id, ghost_reminder_sent=True)
            logger.info(f"Ghost reminder sent to lead {lead.id}")
        except Exception as e:
            logger.error(f"Failed to send ghost reminder to lead {lead.id}: {e}")
    
    async def send_appointment_reminder(self, lead: Lead, appointment_time: datetime):
        """Send appointment reminder to lead."""
        if not self.application or not lead.telegram_chat_id:
            return
        
        # Format reminder message based on language
        lang = lead.language
        time_str = appointment_time.strftime("%A, %B %d at %H:%M")
        
        messages = {
            "en": f"⏰ Reminder: You have an appointment tomorrow!\n\n📅 {time_str}\n\nWe look forward to seeing you!",
            "fa": f"⏰ یادآوری: شما فردا یک قرار ملاقات دارید!\n\n📅 {time_str}\n\nمنتظر دیدار شما هستیم!",
            "ar": f"⏰ تذكير: لديك موعد غدًا!\n\n📅 {time_str}\n\nنتطلع إلى رؤيتك!",
            "ru": f"⏰ Напоминание: У вас завтра встреча!\n\n📅 {time_str}\n\nЖдём вас!"
        }
        
        message = messages.get(lang.value if lang else "en", messages["en"])
        
        try:
            await self.application.bot.send_message(
                chat_id=int(lead.telegram_chat_id),
                text=message,
                parse_mode='HTML'
            )
            logger.info(f"Appointment reminder sent to lead {lead.id}")
        except Exception as e:
            logger.error(f"Failed to send appointment reminder to lead {lead.id}: {e}")


# ==================== BOT MANAGER ====================

class BotManager:
    """
    Manages multiple Telegram bots for multi-tenant system.
    """
    
    def __init__(self):
        self.bots: Dict[int, TelegramBotHandler] = {}
    
    async def start_bot_for_tenant(self, tenant: Tenant):
        """Start a bot for a specific tenant."""
        if tenant.id in self.bots:
            logger.warning(f"Bot already running for tenant {tenant.id}")
            return
        
        handler = TelegramBotHandler(tenant)
        await handler.start_bot()
        self.bots[tenant.id] = handler
    
    async def stop_bot_for_tenant(self, tenant_id: int):
        """Stop a bot for a specific tenant."""
        if tenant_id in self.bots:
            await self.bots[tenant_id].stop_bot()
            del self.bots[tenant_id]
    
    async def stop_all_bots(self):
        """Stop all running bots."""
        for tenant_id in list(self.bots.keys()):
            await self.stop_bot_for_tenant(tenant_id)
    
    async def send_ghost_reminders(self):
        """Send ghost protocol reminders through all bots."""
        from database import get_leads_needing_reminder
        
        leads = await get_leads_needing_reminder(hours=2)
        
        for lead in leads:
            if lead.tenant_id in self.bots:
                await self.bots[lead.tenant_id].send_ghost_reminder(lead)
    
    async def send_appointment_reminders(self):
        """Send appointment reminders through all bots."""
        from database import get_appointments_needing_reminder, async_session
        from sqlalchemy.future import select
        from database import Appointment, Lead
        
        appointments = await get_appointments_needing_reminder(hours_before=24)
        
        for appointment in appointments:
            async with async_session() as session:
                # Get lead
                result = await session.execute(
                    select(Lead).where(Lead.id == appointment.lead_id)
                )
                lead = result.scalar_one_or_none()
                
                if lead and lead.tenant_id in self.bots:
                    await self.bots[lead.tenant_id].send_appointment_reminder(
                        lead, 
                        appointment.scheduled_date
                    )
                    
                    # Mark reminder as sent
                    appointment.reminder_sent = True
                    await session.commit()


# Global bot manager instance
bot_manager = BotManager()

# User locks to prevent concurrent message processing (race condition protection)
from asyncio import Lock
user_locks: Dict[str, Lock] = {}


# ==================== WEBHOOK HANDLER ====================

async def handle_telegram_webhook(token: str, update_data: dict):
    """
    Handle incoming Telegram webhook update.
    This is called from the FastAPI endpoint.
    """
    # Get tenant by token
    tenant = await get_tenant_by_bot_token(token)
    if not tenant:
        logger.error(f"Unknown bot token: {token[:10]}...")
        return
    
    # Get or create bot handler
    if tenant.id not in bot_manager.bots:
        await bot_manager.start_bot_for_tenant(tenant)
    
    handler = bot_manager.bots[tenant.id]
    
    # Process update
    update = Update.de_json(update_data, handler.application.bot)
    await handler.application.process_update(update)
